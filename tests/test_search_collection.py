from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest

from dcinside_scraper.core import api
from dcinside_scraper.core.errors import ValidationFailure
from dcinside_scraper.models.enums import GalleryType, IntegratedSearchSort
from dcinside_scraper.models.job import (
    GallerySearchRequest,
    GallerySearchSource,
    IntegratedSearchRequest,
    NoKeywordRangeSource,
    PostCandidate,
    RangeFilter,
    RealtimeOptions,
    RealtimeKeywordSource,
)
from dcinside_scraper.search import (
    CandidateDeduper,
    GallerySearchCollector,
    GallerySearchParser,
    GallerySearchUrlBuilder,
    IntegratedSearchParser,
    IntegratedSearchUrlBuilder,
    NoKeywordRangeCollector,
    RangeFilterEvaluator,
    RealtimeCollectionCycle,
    SafeCollectorEventBuilder,
    SearchDateJumpClient,
)

FIXTURES = Path(__file__).parent / "fixtures" / "search"


@dataclass
class FakeResponse:
    text: str


class FakeClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.get_urls: list[str] = []
        self.post_calls: list[tuple[str, dict]] = []

    async def get(self, url, *, headers=None, params=None):
        self.get_urls.append(url)
        return FakeResponse(self.response_text)

    async def post(self, url, *, data=None, headers=None, referer=None):
        self.post_calls.append((url, data or {}))
        return FakeResponse((FIXTURES / "search_date_success.json").read_text(encoding="utf-8"))

    async def download(self, url, *, headers=None):
        return b""

    async def close(self):
        return None


def run(coro):
    return asyncio.run(coro)


def test_gallery_url_builder_uses_minor_path_and_percent_space() -> None:
    url = GallerySearchUrlBuilder.build(
        gallery_type=GalleryType.MINOR,
        gallery_id="singlebungle1472",
        page=2,
        s_type="search_subject_memo",
        keyword=" ",
        search_pos="-17000000",
        head_id="160",
    )

    assert "/mgallery/board/lists/" in url
    assert "s_keyword=%20" in url
    assert "search_head=160" in url
    assert "search_pos=-17000000" in url


def test_gallery_parser_extracts_candidates_subject_heads_and_next_search_pos() -> None:
    html = (FIXTURES / "gallery_search.html").read_text(encoding="utf-8")
    url = GallerySearchUrlBuilder.build(
        gallery_type=GalleryType.MINOR,
        gallery_id="singlebungle1472",
        s_type="search_subject_memo",
        keyword="test",
    )

    page = GallerySearchParser().parse(html, current_url=url, gallery_type=GalleryType.MINOR, gallery_id="singlebungle1472", page=1)

    assert [candidate.post_number for candidate in page.candidates] == [100, 99]
    assert page.candidates[0].metadata["is_repost"] is True
    assert page.candidates[1].title == "일반 제목 99"
    assert page.candidates[1].metadata["date_precision"] == "ambiguous"
    assert page.subject_heads[0].id == "160"
    assert page.subject_heads[0].active is True
    assert page.next_search_pos == "-17000000"
    assert page.page_end == 3


def test_gallery_collect_page_validates_subject_head() -> None:
    html = (FIXTURES / "gallery_search.html").read_text(encoding="utf-8")
    request = GallerySearchRequest(
        gallery_type=GalleryType.MINOR,
        gallery_id="singlebungle1472",
        s_type="search_subject_memo",
        keyword="test",
        head_id="999",
    )

    with pytest.raises(ValidationFailure):
        run(GallerySearchCollector(FakeClient(html)).collect_page(request))


def test_integrated_url_builder_encodes_keyword_and_clamps_page() -> None:
    url = IntegratedSearchUrlBuilder.build(keyword="싱글벙글", page=999, sort_mode=IntegratedSearchSort.LATEST)

    assert url == "https://search.dcinside.com/post/p/120/q/.EC.8B.B1.EA.B8.80.EB.B2.99.EA.B8.80"


def test_integrated_parser_extracts_candidates_galleries_and_page_end() -> None:
    html = (FIXTURES / "integrated_search.html").read_text(encoding="utf-8")

    page = IntegratedSearchParser().parse(html, current_url="https://search.dcinside.com/post/q/test", keyword="test", page=1)

    assert [candidate.post_number for candidate in page.candidates] == [100, 200]
    assert page.gallery_candidates[0].gallery_id == "singlebungle1472"
    assert page.gallery_candidates[0].gallery_type == GalleryType.MINOR
    assert page.gallery_candidates[1].gallery_type == GalleryType.MAJOR
    assert page.page_end == 4


def test_public_search_gallery_uses_injected_client() -> None:
    html = (FIXTURES / "gallery_search.html").read_text(encoding="utf-8")
    request = GallerySearchRequest(
        gallery_type=GalleryType.MINOR,
        gallery_id="singlebungle1472",
        s_type="search_subject_memo",
        keyword="test",
        head_id="160",
    )

    page = run(api.search_gallery(request, FakeClient(html)))

    assert page.candidates[0].post_number == 100
    assert page.next_search_pos == "-17000000"


def test_public_search_gallery_requires_client() -> None:
    request = GallerySearchRequest(
        gallery_type=GalleryType.MINOR,
        gallery_id="singlebungle1472",
        s_type="search_subject_memo",
        keyword="test",
    )

    with pytest.raises(ValidationFailure):
        run(api.search_gallery(request))


def test_no_keyword_date_jump_posts_same_client_and_uses_search_pos() -> None:
    page_html = (FIXTURES / "gallery_search.html").read_text(encoding="utf-8")
    page_html = re.sub(r'<a[^>]*class="page_end"[^>]*>.*?</a>', "", page_html)
    page_html = re.sub(r'<a[^>]*class="search_next"[^>]*>.*?</a>', "", page_html)
    html = '<input name="ci_t" value="token-1">' + page_html
    client = FakeClient(html)
    source = NoKeywordRangeSource(
        gallery_type=GalleryType.MINOR,
        gallery_id="singlebungle1472",
        range_filter=RangeFilter(date_to=date(2026, 8, 6), min_post_number=99),
    )

    result = run(NoKeywordRangeCollector(client).collect(source))

    assert client.post_calls[0][1]["ci_t"] == "token-1"
    assert "search_pos=-17000000" in client.get_urls[-1]
    assert result.summary.candidate_count == 2
    assert SearchDateJumpClient.parse_response((FIXTURES / "search_date_success.json").read_text(encoding="utf-8")) == "-17000000"


def test_range_filter_stops_below_min_post_number() -> None:
    candidate = PostCandidate(
        url="https://gall.dcinside.com/board/view/?id=x&no=9",
        gallery_id="x",
        post_id="9",
        post_number=9,
    )

    decision = RangeFilterEvaluator.evaluate(candidate, RangeFilter(min_post_number=10))

    assert decision.include is False
    assert decision.stop is True
    assert decision.reason == "post_number_below_range"


def test_realtime_cycle_excludes_seen_candidates() -> None:
    html = (FIXTURES / "gallery_search.html").read_text(encoding="utf-8")
    seen = {("post", "singlebungle1472", 100)}
    source = RealtimeKeywordSource(
        keyword="test",
        gallery_type=GalleryType.MINOR,
        gallery_id="singlebungle1472",
        termination=RealtimeOptions(duration_seconds=1),
    )

    result = run(RealtimeCollectionCycle(FakeClient(html)).collect_keyword(source, seen=seen))

    assert [candidate.post_number for candidate in result.candidates] == [99]


def test_deduper_and_safe_event_bounds() -> None:
    candidate = PostCandidate(url="https://gall.dcinside.com/board/view/?id=x&no=1", gallery_id="x", post_id="1", post_number=1)
    deduper = CandidateDeduper(max_seen_candidates=1)

    assert deduper.add(candidate) is True
    assert deduper.add(candidate) is False
    with pytest.raises(ValidationFailure):
        deduper.add(PostCandidate(url="https://gall.dcinside.com/board/view/?id=x&no=2", gallery_id="x", post_id="2", post_number=2))

    event = SafeCollectorEventBuilder.build(
        "collector_page_fetch",
        url="https://gall.dcinside.com/board/lists/?id=x&ci_t=secret",
        ci_t="secret",
        raw_html="<html>",
        count=1,
    )
    assert event["url"] == "https://gall.dcinside.com/board/lists/"
    assert "secret" not in repr(event)
