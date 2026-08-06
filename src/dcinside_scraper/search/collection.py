"""Search/list URL builders, parsers, and link collectors."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any
from urllib.parse import parse_qs, parse_qsl, quote, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from bs4.element import Tag

from dcinside_scraper.core.errors import ParseFailureError, ScraperError, UnsupportedSourceError, ValidationFailure
from dcinside_scraper.core.ports import LoggerPort
from dcinside_scraper.models.enums import GalleryType, IntegratedSearchSort
from dcinside_scraper.models.job import (
    DeepSearchSource,
    DirectPostSource,
    GallerySearchPage,
    GallerySearchRequest,
    GallerySearchSource,
    IntegratedSearchPage,
    IntegratedSearchRequest,
    IntegratedSearchSource,
    JobConfig,
    NoKeywordRangeSource,
    PostCandidate,
    RangeFilter,
    RealtimeAllSource,
    RealtimeKeywordSource,
)

GALL_BASE_URL = "https://gall.dcinside.com"
SEARCH_BASE_URL = "https://search.dcinside.com"
MAX_INTEGRATED_PAGE = 120
DATE_JUMP_URL = f"{GALL_BASE_URL}/ajax/search_ajax/search_date/"


class DatePrecision(str, Enum):
    ABSOLUTE = "absolute"
    DATE_ONLY = "date_only"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ParsedDate:
    value: datetime | date | None
    precision: DatePrecision
    raw: str = ""


@dataclass(frozen=True)
class SubjectHead:
    id: str
    name: str
    active: bool = False


@dataclass(frozen=True)
class GalleryCandidate:
    gallery_id: str
    gallery_type: GalleryType
    gallery_name: str | None = None
    gallery_url: str | None = None


@dataclass(frozen=True)
class CollectorFailure:
    stage: str
    reason: str
    retryable: bool = False
    gallery_id: str | None = None
    gallery_type: GalleryType | None = None
    url: str | None = None
    row_index: int | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "reason": self.reason,
            "retryable": self.retryable,
            "gallery_id": self.gallery_id,
            "gallery_type": self.gallery_type.value if self.gallery_type else None,
            "url": SafeCollectorEventBuilder.redact_url(self.url) if self.url else None,
            "row_index": self.row_index,
        }


@dataclass
class CollectorSummary:
    mode: str
    visited_pages: int = 0
    visited_search_segments: int = 0
    candidate_count: int = 0
    deduped_count: int = 0
    skipped_count: int = 0
    range_stop_reason: str | None = None
    gallery_candidate_count: int = 0
    failures: list[CollectorFailure] = field(default_factory=list)
    final_state: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectorResult:
    candidates: list[PostCandidate]
    summary: CollectorSummary
    gallery_candidates: list[GalleryCandidate] = field(default_factory=list)


@dataclass
class ParserResult:
    candidates: list[PostCandidate] = field(default_factory=list)
    failures: list[CollectorFailure] = field(default_factory=list)
    next_page_url: str | None = None
    next_search_pos: str | None = None
    page_end: int = 1
    subject_heads: list[SubjectHead] = field(default_factory=list)
    gallery_candidates: list[GalleryCandidate] = field(default_factory=list)


@dataclass(frozen=True)
class RangeDecision:
    include: bool
    stop: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class TraversalDecision:
    should_continue: bool
    reason: str = "continue"


class NullLogger:
    def debug(self, message: str, **fields: Any) -> None:
        return None

    def info(self, message: str, **fields: Any) -> None:
        return None

    def warning(self, message: str, **fields: Any) -> None:
        return None

    def error(self, message: str, **fields: Any) -> None:
        return None


class GallerySearchUrlBuilder:
    @classmethod
    def build(
        cls,
        *,
        gallery_type: GalleryType,
        gallery_id: str,
        page: int = 1,
        s_type: str | None = None,
        keyword: str | None = None,
        search_pos: str | None = None,
        head_id: str | None = None,
    ) -> str:
        path = {
            GalleryType.MAJOR: "/board/lists/",
            GalleryType.MINOR: "/mgallery/board/lists/",
            GalleryType.MINI: "/mini/board/lists/",
        }[gallery_type]
        query: dict[str, str | int] = {"id": gallery_id, "page": max(page, 1)}
        if s_type:
            query["s_type"] = s_type
        if keyword is not None:
            query["s_keyword"] = keyword
        if search_pos:
            query["search_pos"] = search_pos
        if head_id:
            query["search_head"] = head_id
        return f"{GALL_BASE_URL}{path}?{urlencode(query, quote_via=quote)}"

    @staticmethod
    def with_page(url: str, page: int) -> str:
        parts = urlsplit(url)
        pairs = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "page"]
        pairs.append(("page", str(max(page, 1))))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(pairs, quote_via=quote), parts.fragment))


class IntegratedSearchUrlBuilder:
    @staticmethod
    def encode_keyword(keyword: str) -> str:
        return quote(keyword, safe="").replace("%", ".")

    @classmethod
    def build(cls, *, keyword: str, page: int = 1, sort_mode: IntegratedSearchSort = IntegratedSearchSort.RELEVANCE) -> str:
        page = min(max(page, 1), MAX_INTEGRATED_PAGE)
        encoded = cls.encode_keyword(keyword)
        if sort_mode == IntegratedSearchSort.LATEST:
            path = f"/post/p/{page}/q/{encoded}" if page > 1 else f"/post/q/{encoded}"
        else:
            path = f"/post/p/{page}/sort/accuracy/q/{encoded}" if page > 1 else f"/post/sort/accuracy/q/{encoded}"
        return f"{SEARCH_BASE_URL}{path}"


class DateParser:
    full_datetime = re.compile(r"(?P<year>\d{4})[.\-/](?P<month>\d{1,2})[.\-/](?P<day>\d{1,2})\s+(?P<hour>\d{1,2}):(?P<minute>\d{2})(?::(?P<second>\d{2}))?")
    date_only = re.compile(r"(?P<year>\d{4})[.\-/](?P<month>\d{1,2})[.\-/](?P<day>\d{1,2})")
    ambiguous = re.compile(r"^\d{1,2}[.\-/]\d{1,2}$|^\d{1,2}:\d{2}$")

    @classmethod
    def parse(cls, value: str | None) -> ParsedDate:
        raw = (value or "").strip()
        if not raw:
            return ParsedDate(None, DatePrecision.UNKNOWN, raw)
        match = cls.full_datetime.search(raw)
        if match:
            parts = {key: int(match.group(key) or 0) for key in ("year", "month", "day", "hour", "minute", "second")}
            return ParsedDate(
                datetime(parts["year"], parts["month"], parts["day"], parts["hour"], parts["minute"], parts["second"]),
                DatePrecision.ABSOLUTE,
                raw,
            )
        match = cls.date_only.search(raw)
        if match:
            parts = {key: int(match.group(key)) for key in ("year", "month", "day")}
            return ParsedDate(date(parts["year"], parts["month"], parts["day"]), DatePrecision.DATE_ONLY, raw)
        if cls.ambiguous.match(raw):
            return ParsedDate(None, DatePrecision.AMBIGUOUS, raw)
        return ParsedDate(None, DatePrecision.UNKNOWN, raw)


class RangeFilterEvaluator:
    @classmethod
    def evaluate(cls, candidate: PostCandidate, range_filter: RangeFilter | None) -> RangeDecision:
        if range_filter is None or not range_filter.has_any_bound():
            return RangeDecision(True)

        number = candidate.post_number
        if range_filter.max_post_number is not None and number is not None and number > range_filter.max_post_number:
            return RangeDecision(False, reason="post_number_above_range")
        if range_filter.min_post_number is not None and number is not None and number < range_filter.min_post_number:
            return RangeDecision(False, stop=True, reason="post_number_below_range")

        candidate_date = cls._candidate_date(candidate)
        if candidate_date is None:
            return RangeDecision(True)
        if range_filter.date_to is not None and candidate_date > range_filter.date_to:
            return RangeDecision(False, reason="date_after_range")
        if range_filter.date_from is not None and candidate_date < range_filter.date_from:
            return RangeDecision(False, stop=True, reason="date_before_range")
        return RangeDecision(True)

    @staticmethod
    def _candidate_date(candidate: PostCandidate) -> date | None:
        value = candidate.created_at
        if candidate.metadata.get("date_precision") == DatePrecision.AMBIGUOUS.value:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        parsed = DateParser.parse(value if isinstance(value, str) else None)
        if parsed.precision in {DatePrecision.ABSOLUTE, DatePrecision.DATE_ONLY} and parsed.value is not None:
            return parsed.value.date() if isinstance(parsed.value, datetime) else parsed.value
        return None


class CandidateDeduper:
    def __init__(self, *, max_seen_candidates: int | None = None, seen: set[tuple[Any, ...]] | None = None) -> None:
        if max_seen_candidates is not None and max_seen_candidates < 1:
            raise ValueError("max_seen_candidates must be >= 1")
        self.max_seen_candidates = max_seen_candidates
        self.seen: set[tuple[Any, ...]] = seen if seen is not None else set()

    def add(self, candidate: PostCandidate) -> bool:
        key = self.key(candidate)
        if key in self.seen:
            return False
        if self.max_seen_candidates is not None and len(self.seen) >= self.max_seen_candidates:
            raise ValidationFailure("max_seen_candidates exceeded", details={"reason": "max_seen_candidates_exceeded"})
        self.seen.add(key)
        return True

    @staticmethod
    def key(candidate: PostCandidate) -> tuple[Any, ...]:
        if candidate.post_number is not None:
            return ("post", candidate.gallery_id, candidate.post_number)
        return ("url", normalize_post_url(candidate.url))


class GalleryCandidateDeduper:
    def __init__(self) -> None:
        self.seen: set[tuple[str, str]] = set()

    def unique(self, candidates: Iterable[GalleryCandidate]) -> list[GalleryCandidate]:
        unique: list[GalleryCandidate] = []
        for candidate in candidates:
            key = (candidate.gallery_type.value, candidate.gallery_id)
            if key not in self.seen:
                self.seen.add(key)
                unique.append(candidate)
        return unique


class TraversalGuard:
    def __init__(self, *, max_pages: int | None = None, max_segments: int | None = None) -> None:
        self.max_pages = max_pages
        self.max_segments = max_segments

    def check_integrated_page(self, page: int) -> TraversalDecision:
        if page > MAX_INTEGRATED_PAGE:
            return TraversalDecision(False, "integrated_page_limit")
        return TraversalDecision(True)

    def check_page_count(self, visited_pages: int) -> TraversalDecision:
        if self.max_pages is not None and visited_pages >= self.max_pages:
            return TraversalDecision(False, "max_pages_reached")
        return TraversalDecision(True)

    def check_segment_count(self, visited_segments: int) -> TraversalDecision:
        if self.max_segments is not None and visited_segments >= self.max_segments:
            return TraversalDecision(False, "max_segments_reached")
        return TraversalDecision(True)


class SafeCollectorEventBuilder:
    blocked_keys = {"html", "raw_html", "body", "raw_body", "content", "cookie", "cookies", "ci_t", "headers"}

    @classmethod
    def build(cls, event: str, *, url: str | None = None, **fields: Any) -> dict[str, Any]:
        safe = {"event": event}
        if url:
            safe["url"] = cls.redact_url(url)
        for key, value in fields.items():
            if key.lower() in cls.blocked_keys:
                continue
            if isinstance(value, GalleryType):
                value = value.value
            safe[key] = value
        return safe

    @staticmethod
    def redact_url(url: str) -> str:
        parts = urlsplit(url)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


class SubjectHeadParser:
    pattern = re.compile(r"listSearchHead\(['\"]?(?P<id>\d+)['\"]?\)")

    @classmethod
    def parse(cls, soup: BeautifulSoup) -> list[SubjectHead]:
        heads: list[SubjectHead] = []
        for anchor in soup.select("a[onclick^='listSearchHead']"):
            match = cls.pattern.search(str(anchor.get("onclick", "")))
            if not match:
                continue
            classes = set(anchor.get("class", []))
            parent_classes = set(anchor.parent.get("class", [])) if isinstance(anchor.parent, Tag) else set()
            heads.append(
                SubjectHead(
                    id=match.group("id"),
                    name=anchor.get_text(" ", strip=True),
                    active=bool({"on", "active", "selected"} & (classes | parent_classes)),
                )
            )
        return heads


class GallerySearchParser:
    def parse(self, html: str, *, current_url: str, gallery_type: GalleryType, gallery_id: str, page: int) -> ParserResult:
        soup = BeautifulSoup(html, "html.parser")
        result = ParserResult(page_end=_parse_page_end(soup, current_url=current_url, current_page=page))
        result.subject_heads = SubjectHeadParser.parse(soup)
        result.next_page_url = self._next_search_url(soup, current_url)
        result.next_search_pos = _query_value(result.next_page_url, "search_pos") if result.next_page_url else None

        rows = soup.select(".gall_listwrap.list tbody tr.ub-content.us-post") or soup.select("tr.ub-content.us-post")
        for row_index, row in enumerate(rows, start=1):
            try:
                candidate = self._parse_row(row, current_url=current_url, gallery_type=gallery_type, gallery_id=gallery_id)
            except ScraperError as exc:
                result.failures.append(
                    CollectorFailure(
                        stage="gallery_row",
                        reason=exc.safe_message,
                        gallery_id=gallery_id,
                        gallery_type=gallery_type,
                        url=current_url,
                        row_index=row_index,
                    )
                )
                continue
            if candidate is not None:
                result.candidates.append(candidate)
        return result

    @staticmethod
    def _parse_row(row: Tag, *, current_url: str, gallery_type: GalleryType, gallery_id: str) -> PostCandidate | None:
        number_text = _text(row.select_one(".gall_num"))
        if number_text == "-":
            return None
        post_number = _int_or_none(number_text)
        if post_number is None:
            raise ParseFailureError("post number missing", details={"reason": "post_number_missing"})

        link = row.select_one(".gall_tit a[href]")
        if link is None:
            raise ParseFailureError("post link missing", details={"reason": "post_link_missing"})
        url = urljoin(current_url, str(link.get("href", "")))
        parsed = parse_post_url(url)
        post_number = parsed.post_number or post_number

        raw_date = _attr(row.select_one(".gall_date"), "title") or _text(row.select_one(".gall_date"))
        parsed_date = DateParser.parse(raw_date)
        marker = row.select_one(".gall_tit > b.font_blue009")
        subject_head = _text(row.select_one(".gall_subject")) or None
        metadata: dict[str, Any] = {
            "gallery_type": gallery_type.value,
            "date_precision": parsed_date.precision.value,
            "is_repost": _text(marker) == "(펌)",
            "subject_head": {"name": subject_head} if subject_head else None,
            "views": _int_or_none(_text(row.select_one(".gall_count"))),
            "recommendations": _int_or_none(_text(row.select_one(".gall_recommend"))),
        }
        return PostCandidate(
            url=url,
            gallery_id=parsed.gallery_id or gallery_id,
            post_id=str(post_number),
            post_number=post_number,
            title=_clean_title(link.get_text(" ", strip=True)),
            created_at=parsed_date.value or raw_date or None,
            metadata=metadata,
        )

    @staticmethod
    def _next_search_url(soup: BeautifulSoup, current_url: str) -> str | None:
        link = soup.select_one("a.search_next[href]")
        if link is None:
            for anchor in soup.select("a[href]"):
                if "다음 검색" in anchor.get_text(" ", strip=True):
                    link = anchor
                    break
        return urljoin(current_url, str(link.get("href", ""))) if link is not None else None


class IntegratedSearchParser:
    def parse(self, html: str, *, current_url: str, keyword: str, page: int) -> ParserResult:
        soup = BeautifulSoup(html, "html.parser")
        result = ParserResult(page_end=_parse_integrated_page_end(soup, current_url=current_url, current_page=page))
        rows = soup.select(".integrate_cont.sch_result.result_all ul.sch_result_list > li") or soup.select("ul.sch_result_list > li")
        for row_index, row in enumerate(rows, start=1):
            try:
                candidate, gallery = self._parse_row(row, current_url=current_url, keyword=keyword)
            except ScraperError as exc:
                result.failures.append(CollectorFailure(stage="integrated_row", reason=exc.safe_message, url=current_url, row_index=row_index))
                continue
            result.candidates.append(candidate)
            result.gallery_candidates.append(gallery)
        return result

    @staticmethod
    def _parse_row(row: Tag, *, current_url: str, keyword: str) -> tuple[PostCandidate, GalleryCandidate]:
        link = row.select_one("a.tit_txt[href]")
        if link is None:
            raise ParseFailureError("integrated result link missing", details={"reason": "post_link_missing"})
        url = urljoin(current_url, str(link.get("href", "")))
        parsed = parse_post_url(url)
        if parsed.post_number is None:
            raise ParseFailureError("integrated post number missing", details={"reason": "post_number_missing"})

        raw_date = _text(row.select_one("p.dsc_sub > span.date_time"))
        parsed_date = DateParser.parse(raw_date)
        gallery_link = row.select_one("p.dsc_sub > a.sub_txt[href]")
        gallery_name = _text(gallery_link) if gallery_link else None
        preview = " ".join(
            p.get_text(" ", strip=True)
            for p in row.select("p.link_dsc_txt")
            if "dsc_sub" not in set(p.get("class", []))
        )
        metadata = {
            "gallery_type": parsed.gallery_type.value,
            "gallery_name": gallery_name,
            "preview": preview or None,
            "keyword": keyword,
            "date_precision": parsed_date.precision.value,
        }
        candidate = PostCandidate(
            url=url,
            gallery_id=parsed.gallery_id,
            post_id=str(parsed.post_number),
            post_number=parsed.post_number,
            title=_clean_title(link.get_text(" ", strip=True)),
            created_at=parsed_date.value or raw_date or None,
            metadata=metadata,
        )
        gallery = GalleryCandidate(
            gallery_id=parsed.gallery_id,
            gallery_type=parsed.gallery_type,
            gallery_name=gallery_name,
            gallery_url=urljoin(current_url, str(gallery_link.get("href", ""))) if gallery_link else None,
        )
        return candidate, gallery


@dataclass(frozen=True)
class ParsedPostUrl:
    url: str
    gallery_id: str
    post_id: str
    post_number: int | None
    gallery_type: GalleryType


def parse_post_url(url: str) -> ParsedPostUrl:
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    gallery_id = (query.get("id") or [""])[0]
    post_id = (query.get("no") or [""])[0]
    post_number = _int_or_none(post_id)
    if not gallery_id or not post_id:
        raise ParseFailureError("post URL must contain id and no", details={"reason": "invalid_post_url"})
    gallery_type = GalleryType.MAJOR
    if "/mgallery/" in parts.path:
        gallery_type = GalleryType.MINOR
    elif "/mini/" in parts.path:
        gallery_type = GalleryType.MINI
    return ParsedPostUrl(url=url, gallery_id=gallery_id, post_id=post_id, post_number=post_number, gallery_type=gallery_type)


class SearchDateJumpClient:
    @staticmethod
    def parse_response(text: str) -> str | None:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None
        if payload.get("result") == "success":
            data = str(payload.get("data") or "").strip()
            return data or None
        return None

    async def jump(
        self,
        client: Any,
        *,
        initial_html: str,
        referer_url: str,
        gallery_type: GalleryType,
        gallery_id: str,
        target_date: date,
        keyword: str = "",
        s_type: str = "search_subject_memo",
    ) -> str | None:
        data = {
            "ci_t": _extract_ci_t(initial_html),
            "date": target_date.isoformat(),
            "id": gallery_id,
            "keyword": keyword,
            "s_type": s_type,
            "_GALLTYPE_": {GalleryType.MAJOR: "G", GalleryType.MINOR: "M", GalleryType.MINI: "MI"}[gallery_type],
        }
        response = await _client_post(client, DATE_JUMP_URL, data=data, referer=referer_url)
        return self.parse_response(response.text)


class GallerySearchCollector:
    def __init__(
        self,
        client: Any,
        *,
        logger: LoggerPort | None = None,
        max_pages: int | None = None,
        max_segments: int | None = None,
        max_seen_candidates: int | None = None,
    ) -> None:
        self.client = client
        self.logger = logger or NullLogger()
        self.guard = TraversalGuard(max_pages=max_pages, max_segments=max_segments)
        self.max_seen_candidates = max_seen_candidates
        self.parser = GallerySearchParser()

    async def collect_page(self, request: GallerySearchRequest) -> GallerySearchPage:
        if request.head_id and request.gallery_type == GalleryType.MAJOR:
            raise ValidationFailure("subject head is only supported for minor galleries", details={"reason": "subject_head_major_gallery"})
        url = GallerySearchUrlBuilder.build(
            gallery_type=request.gallery_type,
            gallery_id=request.gallery_id,
            page=request.page,
            s_type=request.s_type,
            keyword=request.keyword,
            search_pos=request.search_pos,
            head_id=request.head_id,
        )
        response = await self.client.get(url)
        parsed = self.parser.parse(response.text, current_url=url, gallery_type=request.gallery_type, gallery_id=request.gallery_id, page=request.page)
        _validate_subject_head(request.head_id, request.gallery_type, parsed.subject_heads)
        return GallerySearchPage(
            gallery_id=request.gallery_id,
            page=request.page,
            candidates=parsed.candidates,
            next_search_pos=parsed.next_search_pos,
            has_next=parsed.next_page_url is not None,
            metadata={
                "page_end": parsed.page_end,
                "subject_heads": [head.__dict__ for head in parsed.subject_heads],
                "failures": [failure.to_metadata() for failure in parsed.failures],
            },
        )

    async def collect(
        self,
        source: GallerySearchSource,
        *,
        range_filter: RangeFilter | None = None,
        deduper: CandidateDeduper | None = None,
        max_pages: int | None = None,
        max_segments: int | None = None,
    ) -> CollectorResult:
        local_guard = TraversalGuard(max_pages=max_pages, max_segments=max_segments) if max_pages or max_segments else self.guard
        deduper = deduper or CandidateDeduper(max_seen_candidates=self.max_seen_candidates)
        summary = CollectorSummary(mode="gallery_search")
        candidates: list[PostCandidate] = []
        current_url: str | None = GallerySearchUrlBuilder.build(
            gallery_type=source.gallery_type,
            gallery_id=source.gallery_id,
            page=source.page,
            s_type=source.s_type,
            keyword=source.keyword,
            search_pos=source.search_pos,
            head_id=source.head_id,
        )

        while current_url is not None:
            decision = local_guard.check_segment_count(summary.visited_search_segments)
            if not decision.should_continue:
                summary.range_stop_reason = decision.reason
                break
            summary.visited_search_segments += 1
            page = _int_or_none(_query_value(current_url, "page")) or 1

            while current_url is not None:
                decision = local_guard.check_page_count(summary.visited_pages)
                if not decision.should_continue:
                    summary.range_stop_reason = decision.reason
                    return CollectorResult(candidates, summary)

                self._log("debug", "collector_page_fetch", url=current_url, mode="gallery_search", page=page)
                response = await self.client.get(current_url)
                parsed = self.parser.parse(response.text, current_url=current_url, gallery_type=source.gallery_type, gallery_id=source.gallery_id, page=page)
                _validate_subject_head(source.head_id, source.gallery_type, parsed.subject_heads)
                summary.visited_pages += 1
                summary.failures.extend(parsed.failures)

                stop = self._accept_candidates(parsed.candidates, range_filter=range_filter, deduper=deduper, output=candidates, summary=summary)
                if stop:
                    return CollectorResult(candidates, summary)
                if page >= parsed.page_end:
                    current_url = parsed.next_page_url
                    break
                page += 1
                current_url = GallerySearchUrlBuilder.with_page(current_url, page)

        summary.final_state = {"last_url": SafeCollectorEventBuilder.redact_url(current_url) if current_url else None}
        return CollectorResult(candidates, summary)

    async def collect_latest_page(self, *, gallery_type: GalleryType, gallery_id: str, deduper: CandidateDeduper | None = None) -> CollectorResult:
        url = GallerySearchUrlBuilder.build(gallery_type=gallery_type, gallery_id=gallery_id, page=1)
        response = await self.client.get(url)
        parsed = self.parser.parse(response.text, current_url=url, gallery_type=gallery_type, gallery_id=gallery_id, page=1)
        summary = CollectorSummary(mode="realtime_all", visited_pages=1, visited_search_segments=1, failures=parsed.failures)
        deduper = deduper or CandidateDeduper(max_seen_candidates=self.max_seen_candidates)
        candidates: list[PostCandidate] = []
        self._accept_candidates(parsed.candidates, range_filter=None, deduper=deduper, output=candidates, summary=summary)
        return CollectorResult(candidates, summary)

    @staticmethod
    def _accept_candidates(
        source: Sequence[PostCandidate],
        *,
        range_filter: RangeFilter | None,
        deduper: CandidateDeduper,
        output: list[PostCandidate],
        summary: CollectorSummary,
    ) -> bool:
        for candidate in source:
            decision = RangeFilterEvaluator.evaluate(candidate, range_filter)
            if decision.stop:
                summary.skipped_count += 1
                summary.range_stop_reason = decision.reason
                return True
            if not decision.include:
                summary.skipped_count += 1
                continue
            if deduper.add(candidate):
                output.append(candidate)
                summary.candidate_count += 1
            else:
                summary.deduped_count += 1
        return False

    def _log(self, level: str, event: str, *, url: str, **fields: Any) -> None:
        safe = SafeCollectorEventBuilder.build(event, url=url, **fields)
        getattr(self.logger, level)(event, **safe)


class IntegratedSearchCollector:
    def __init__(self, client: Any, *, logger: LoggerPort | None = None, max_seen_candidates: int | None = None) -> None:
        self.client = client
        self.logger = logger or NullLogger()
        self.parser = IntegratedSearchParser()
        self.max_seen_candidates = max_seen_candidates
        self.guard = TraversalGuard()

    async def collect_page(self, request: IntegratedSearchRequest) -> IntegratedSearchPage:
        page = min(request.page, MAX_INTEGRATED_PAGE)
        url = IntegratedSearchUrlBuilder.build(keyword=request.keyword, page=page, sort_mode=request.sort_mode)
        response = await self.client.get(url)
        parsed = self.parser.parse(response.text, current_url=url, keyword=request.keyword, page=page)
        unique_galleries = GalleryCandidateDeduper().unique(parsed.gallery_candidates)
        return IntegratedSearchPage(
            keyword=request.keyword,
            page=page,
            candidates=parsed.candidates,
            gallery_ids=[gallery.gallery_id for gallery in unique_galleries],
            has_next=page < min(parsed.page_end, MAX_INTEGRATED_PAGE),
            metadata={
                "page_end": parsed.page_end,
                "gallery_candidates": [_gallery_metadata(gallery) for gallery in unique_galleries],
                "failures": [failure.to_metadata() for failure in parsed.failures],
            },
        )

    async def collect(
        self,
        source: IntegratedSearchSource,
        *,
        range_filter: RangeFilter | None = None,
        deduper: CandidateDeduper | None = None,
    ) -> CollectorResult:
        deduper = deduper or CandidateDeduper(max_seen_candidates=self.max_seen_candidates)
        summary = CollectorSummary(mode="integrated_search")
        candidates: list[PostCandidate] = []
        galleries: list[GalleryCandidate] = []
        page = min(source.page_start, MAX_INTEGRATED_PAGE)
        page_end = min(source.page_end, MAX_INTEGRATED_PAGE)

        while page <= page_end:
            decision = self.guard.check_integrated_page(page)
            if not decision.should_continue:
                summary.range_stop_reason = decision.reason
                break
            url = IntegratedSearchUrlBuilder.build(keyword=source.keyword, page=page, sort_mode=source.sort_mode)
            response = await self.client.get(url)
            parsed = self.parser.parse(response.text, current_url=url, keyword=source.keyword, page=page)
            summary.visited_pages += 1
            summary.failures.extend(parsed.failures)
            galleries.extend(parsed.gallery_candidates)
            stop = GallerySearchCollector._accept_candidates(parsed.candidates, range_filter=range_filter, deduper=deduper, output=candidates, summary=summary)
            if stop:
                break
            page_end = min(page_end, parsed.page_end, MAX_INTEGRATED_PAGE)
            page += 1

        gallery_candidates = GalleryCandidateDeduper().unique(galleries)
        summary.gallery_candidate_count = len(gallery_candidates)
        return CollectorResult(candidates, summary, gallery_candidates)


class NoKeywordRangeCollector:
    def __init__(self, client: Any, *, logger: LoggerPort | None = None) -> None:
        self.client = client
        self.logger = logger or NullLogger()
        self.date_jump = SearchDateJumpClient()

    async def collect(self, source: NoKeywordRangeSource, *, deduper: CandidateDeduper | None = None) -> CollectorResult:
        search_pos = None
        if source.range_filter.date_to is not None:
            initial_url = GallerySearchUrlBuilder.build(
                gallery_type=source.gallery_type,
                gallery_id=source.gallery_id,
                page=1,
                s_type="search_subject_memo",
                keyword=" ",
            )
            response = await self.client.get(initial_url)
            search_pos = await self.date_jump.jump(
                self.client,
                initial_html=response.text,
                referer_url=initial_url,
                gallery_type=source.gallery_type,
                gallery_id=source.gallery_id,
                target_date=source.range_filter.date_to,
            )
            if search_pos is None:
                return CollectorResult([], CollectorSummary(mode="no_keyword_range", range_stop_reason="search_date_no_result"))

        gallery_source = GallerySearchSource(
            gallery_type=source.gallery_type,
            gallery_id=source.gallery_id,
            s_type="search_subject_memo",
            keyword=" ",
            search_pos=search_pos,
        )
        return await GallerySearchCollector(self.client, logger=self.logger).collect(gallery_source, range_filter=source.range_filter, deduper=deduper)


class DeepSearchCollector:
    def __init__(self, client: Any, *, logger: LoggerPort | None = None) -> None:
        self.client = client
        self.logger = logger or NullLogger()

    async def collect(self, source: DeepSearchSource) -> CollectorResult:
        deduper = CandidateDeduper()
        integrated = await IntegratedSearchCollector(self.client, logger=self.logger).collect(
            IntegratedSearchSource(keyword=source.keyword, sort_mode=source.seed_sort_mode, page_start=1, page_end=MAX_INTEGRATED_PAGE),
            range_filter=source.range_filter,
            deduper=deduper,
        )
        candidates = list(integrated.candidates)
        summary = integrated.summary
        summary.mode = "deep_search"

        for gallery in integrated.gallery_candidates:
            try:
                gallery_result = await GallerySearchCollector(self.client, logger=self.logger).collect(
                    GallerySearchSource(gallery_type=gallery.gallery_type, gallery_id=gallery.gallery_id, s_type="search_subject_memo", keyword=source.keyword),
                    range_filter=source.range_filter,
                    deduper=deduper,
                )
            except ScraperError as exc:
                summary.failures.append(
                    CollectorFailure(
                        stage="deep_gallery",
                        reason=exc.safe_message,
                        retryable=exc.retryable,
                        gallery_id=gallery.gallery_id,
                        gallery_type=gallery.gallery_type,
                    )
                )
                continue
            candidates.extend(gallery_result.candidates)
            summary.candidate_count += gallery_result.summary.candidate_count
            summary.deduped_count += gallery_result.summary.deduped_count
            summary.skipped_count += gallery_result.summary.skipped_count
            summary.failures.extend(gallery_result.summary.failures)
        return CollectorResult(candidates, summary, integrated.gallery_candidates)


class DirectPostCollector:
    def collect(self, source: DirectPostSource, *, deduper: CandidateDeduper | None = None) -> CollectorResult:
        deduper = deduper or CandidateDeduper()
        summary = CollectorSummary(mode="direct_post")
        candidates: list[PostCandidate] = []
        for url in source.urls:
            parsed = parse_post_url(url)
            candidate = PostCandidate(
                url=url,
                gallery_id=parsed.gallery_id,
                post_id=parsed.post_id,
                post_number=parsed.post_number,
                metadata={"gallery_type": parsed.gallery_type.value},
            )
            if deduper.add(candidate):
                candidates.append(candidate)
                summary.candidate_count += 1
            else:
                summary.deduped_count += 1
        return CollectorResult(candidates, summary)


class RealtimeCollectionCycle:
    def __init__(self, client: Any, *, logger: LoggerPort | None = None) -> None:
        self.client = client
        self.logger = logger or NullLogger()

    async def collect_keyword(self, source: RealtimeKeywordSource, *, seen: set[tuple[Any, ...]] | None = None) -> CollectorResult:
        deduper = CandidateDeduper(seen=seen)
        if source.gallery_id and source.gallery_type:
            gallery = GallerySearchSource(gallery_type=source.gallery_type, gallery_id=source.gallery_id, s_type="search_subject_memo", keyword=source.keyword)
            return await GallerySearchCollector(self.client, logger=self.logger).collect(gallery, deduper=deduper, max_pages=1, max_segments=1)
        integrated = IntegratedSearchSource(keyword=source.keyword, sort_mode=IntegratedSearchSort.LATEST, page_start=1, page_end=1)
        return await IntegratedSearchCollector(self.client, logger=self.logger).collect(integrated, deduper=deduper)

    async def collect_all(self, source: RealtimeAllSource, *, seen: set[tuple[Any, ...]] | None = None) -> CollectorResult:
        return await GallerySearchCollector(self.client, logger=self.logger).collect_latest_page(
            gallery_type=source.gallery_type,
            gallery_id=source.gallery_id,
            deduper=CandidateDeduper(seen=seen),
        )


class LinkCollectorService:
    def __init__(self, client: Any, *, logger: LoggerPort | None = None) -> None:
        self.client = client
        self.logger = logger or NullLogger()

    async def collect(self, config: JobConfig | Any) -> CollectorResult:
        source = config.source if isinstance(config, JobConfig) else config
        range_filter = getattr(getattr(config, "scrape_options", None), "range_filter", None)
        if isinstance(source, DirectPostSource):
            return DirectPostCollector().collect(source)
        if isinstance(source, GallerySearchSource):
            return await GallerySearchCollector(self.client, logger=self.logger).collect(source, range_filter=range_filter)
        if isinstance(source, IntegratedSearchSource):
            return await IntegratedSearchCollector(self.client, logger=self.logger).collect(source, range_filter=range_filter)
        if isinstance(source, NoKeywordRangeSource):
            return await NoKeywordRangeCollector(self.client, logger=self.logger).collect(source)
        if isinstance(source, DeepSearchSource):
            return await DeepSearchCollector(self.client, logger=self.logger).collect(source)
        if isinstance(source, RealtimeKeywordSource):
            return await RealtimeCollectionCycle(self.client, logger=self.logger).collect_keyword(source)
        if isinstance(source, RealtimeAllSource):
            return await RealtimeCollectionCycle(self.client, logger=self.logger).collect_all(source)
        raise UnsupportedSourceError("unsupported source", details={"source_type": getattr(source, "type", "unknown")})


def _validate_subject_head(head_id: str | None, gallery_type: GalleryType, heads: Sequence[SubjectHead]) -> None:
    if head_id is None:
        return
    if gallery_type == GalleryType.MAJOR:
        raise ValidationFailure("subject head is only supported for minor galleries", details={"reason": "subject_head_major_gallery"})
    if heads and not any(head.id == head_id and head.active for head in heads):
        raise ValidationFailure("subject head is not active or does not exist", details={"reason": "subject_head_invalid"})


async def _client_post(client: Any, url: str, *, data: dict[str, Any], referer: str) -> Any:
    try:
        return await client.post(url, data=data, referer=referer)
    except TypeError:
        return await client.post(url, data=data)


def _parse_page_end(soup: BeautifulSoup, *, current_url: str, current_page: int) -> int:
    page_end = _page_from_href(soup.select_one("a.page_end[href]"))
    if page_end is not None:
        return page_end
    pages = [_page_from_href(anchor) for anchor in soup.select("a[href]")]
    pages += [_int_or_none(anchor.get_text(" ", strip=True)) for anchor in soup.select("a")]
    return max([current_page, *(page for page in pages if page is not None)])


def _parse_integrated_page_end(soup: BeautifulSoup, *, current_url: str, current_page: int) -> int:
    page_end = _integrated_page_from_href(soup.select_one("a.page_end[href]"))
    if page_end is not None:
        return min(page_end, MAX_INTEGRATED_PAGE)
    pages = [_integrated_page_from_href(anchor) for anchor in soup.select("a[href]")]
    pages += [_int_or_none(anchor.get_text(" ", strip=True)) for anchor in soup.select("a")]
    return min(max([current_page, *(page for page in pages if page is not None)]), MAX_INTEGRATED_PAGE)


def _page_from_href(anchor: Tag | None) -> int | None:
    if anchor is None:
        return None
    return _int_or_none(_query_value(str(anchor.get("href", "")), "page"))


def _integrated_page_from_href(anchor: Tag | None) -> int | None:
    if anchor is None:
        return None
    href = str(anchor.get("href", ""))
    match = re.search(r"/p/(?P<page>\d+)(?:/|$)", href)
    return int(match.group("page")) if match else _page_from_href(anchor)


def _query_value(url: str | None, key: str) -> str | None:
    if not url:
        return None
    values = parse_qs(urlsplit(url).query, keep_blank_values=True).get(key)
    return values[0] if values else None


def _extract_ci_t(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    token = soup.select_one("input[name='ci_t'][value]")
    if token is not None:
        return str(token.get("value", ""))
    match = re.search(r"ci_t['\"]?\s*[:=]\s*['\"](?P<token>[^'\"]+)['\"]", html)
    return match.group("token") if match else ""


def normalize_post_url(url: str) -> str:
    parts = urlsplit(url)
    query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)), quote_via=quote)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


def _gallery_metadata(gallery: GalleryCandidate) -> dict[str, Any]:
    return {
        "gallery_id": gallery.gallery_id,
        "gallery_type": gallery.gallery_type.value,
        "gallery_name": gallery.gallery_name,
        "gallery_url": gallery.gallery_url,
    }


def _text(node: Tag | None) -> str:
    return node.get_text(" ", strip=True) if node is not None else ""


def _attr(node: Tag | None, name: str) -> str:
    return str(node.get(name, "")) if node is not None and node.has_attr(name) else ""


def _int_or_none(value: str | int | None) -> int | None:
    if isinstance(value, int):
        return value
    digits = re.sub(r"[^0-9]", "", value or "")
    return int(digits) if digits else None


def _clean_title(title: str) -> str:
    return title.removeprefix("(펌)").strip()
