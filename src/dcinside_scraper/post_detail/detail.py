"""Post detail, content, repost, and comment parsers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from dcinside_scraper.core.errors import BlockedResponseError, CaptchaDetectedError, ParseFailureError, ScraperError, ValidationFailure
from dcinside_scraper.core.ports import LoggerPort
from dcinside_scraper.models.comment import AuthorInfo, Comment, RecommendationInfo
from dcinside_scraper.models.content import ContentLink, DcVideoBlock, ImageBlock, LinkBlock, SeriesBlock, TextBlock, UnknownEmbedBlock, YouTubeBlock
from dcinside_scraper.models.enums import GalleryType, MediaType, NicknameType
from dcinside_scraper.models.job import CommentRequest, PostRequest
from dcinside_scraper.models.media import DcconItem, MediaItem
from dcinside_scraper.models.post import PostResult, RepostInfo
from dcinside_scraper.post_detail.normalization import (
    classify_nickname_type,
    make_safe_detail_failure,
    parse_count,
    parse_dcinside_date,
    strip_repost_marker,
)
from dcinside_scraper.collect.urls import parse_post_url

GALL_BASE_URL = "https://gall.dcinside.com"
COMMENT_URL = f"{GALL_BASE_URL}/board/comment/"


class NullLogger:
    def debug(self, message: str, **fields: Any) -> None:
        return None

    def info(self, message: str, **fields: Any) -> None:
        return None

    def warning(self, message: str, **fields: Any) -> None:
        return None

    def error(self, message: str, **fields: Any) -> None:
        return None


@dataclass
class ParsedContent:
    blocks: list[Any] = field(default_factory=list)
    images: list[MediaItem] = field(default_factory=list)
    links: list[ContentLink] = field(default_factory=list)


@dataclass
class ParsedMetadata:
    gallery_id: str
    post_id: str
    post_number: int | None
    gallery_type: GalleryType | None
    title: str
    author: AuthorInfo
    nickname_type: NicknameType
    date: Any = None
    views: int | None = None
    recommendations: RecommendationInfo = field(default_factory=RecommendationInfo)
    comment_count: int | None = None
    is_repost: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RepostParseResult:
    repost: RepostInfo
    content: ParsedContent


@dataclass
class CommentPage:
    comments: list[Comment]
    has_next: bool


@dataclass
class CommentCollection:
    comments: list[Comment] = field(default_factory=list)
    failures: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class PaginationDecision:
    should_continue: bool
    reason: str


class DetailFailureRecorder:
    def __init__(self) -> None:
        self.failures: list[dict[str, Any]] = []

    def record(
        self,
        *,
        stage: str,
        reason: str,
        retryable: bool = False,
        field_path: str | None = None,
        failed_fields: list[str] | None = None,
    ) -> None:
        self.failures.append(
            make_safe_detail_failure(
                stage=stage,
                reason=reason,
                retryable=retryable,
                field_path=field_path,
                failed_fields=failed_fields,
            )
        )

    def apply(self, metadata: dict[str, Any]) -> dict[str, Any]:
        if self.failures:
            metadata = dict(metadata)
            metadata["detail_failures"] = list(self.failures)
        return metadata


class SafeDetailEventBuilder:
    blocked_keys = {"html", "raw_html", "body", "raw_body", "content", "cookie", "cookies", "headers", "proxy", "password"}

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


class PostMetadataParser:
    def parse(self, html: str, request: PostRequest) -> ParsedMetadata:
        soup = BeautifulSoup(html, "html.parser")
        parsed_url = _safe_parse_post_url(request.url)
        gallery_id = _first_text(request.gallery_id, parsed_url.get("gallery_id"))
        post_id = _first_text(request.post_id, parsed_url.get("post_id"))
        if not gallery_id or not post_id:
            raise ParseFailureError("post identity missing", details={"reason": "post_identity_missing"})

        title_node = soup.select_one("h3.title") or soup.select_one(".gallview_head .title") or soup.select_one("title")
        raw_title = _title_text(title_node)
        if not raw_title:
            raise ParseFailureError("post title missing", details={"reason": "post_title_missing"})
        marker = title_node.select_one("b.font_blue009") if isinstance(title_node, Tag) else None
        is_repost = _text(marker) == "(펌)" or raw_title.startswith("(펌)") or "/ajax/pum_ajax/get_contents" in html
        title = strip_repost_marker(raw_title)

        writer = soup.select_one(".gall_writer") or soup.select_one(".writer") or soup.select_one("[data-nick]")
        author = _parse_author(writer)
        if not author.name and not author.user_id and not author.ip:
            raise ParseFailureError("post author missing", details={"reason": "post_author_missing"})

        post_number = request.post_number or parsed_url.get("post_number")
        upvotes = parse_count(_text(soup.select_one(f"#recommend_view_up_{post_id}")) or _text(soup.select_one(".up_num")))
        downvotes = parse_count(_text(soup.select_one(f"#recommend_view_down_{post_id}")) or _text(soup.select_one(".down_num")))
        subject_head = _subject_head(soup)
        metadata: dict[str, Any] = {
            "gallery_type": (request.gallery_type or parsed_url.get("gallery_type")).value
            if request.gallery_type or parsed_url.get("gallery_type")
            else None,
            "subject_head": subject_head,
            "comment_params": _comment_params(soup),
        }
        return ParsedMetadata(
            gallery_id=gallery_id,
            post_id=post_id,
            post_number=post_number,
            gallery_type=request.gallery_type or parsed_url.get("gallery_type"),
            title=title,
            author=author,
            nickname_type=author.nickname_type,
            date=parse_dcinside_date(_attr(soup.select_one(".gall_date"), "title") or _text(soup.select_one(".gall_date"))),
            views=parse_count(_text(soup.select_one(".gall_count"))),
            recommendations=RecommendationInfo(upvotes=upvotes, downvotes=downvotes),
            comment_count=parse_count(_text(soup.select_one(".gall_comment"))),
            is_repost=is_repost,
            metadata=metadata,
        )


class ContentBlockParser:
    noise_classes = {"img_comment", "image_comment", "tip_box2", "num", "btn", "cmt_write_box"}

    def parse(self, html_or_node: str | Tag, *, base_url: str) -> ParsedContent:
        soup = BeautifulSoup(html_or_node, "html.parser") if isinstance(html_or_node, str) else html_or_node
        root = soup.select_one(".writing_view_box .write_div") or soup.select_one(".write_div") if isinstance(soup, BeautifulSoup) else soup
        content = ParsedContent()
        if root is None:
            return content
        for child in root.children:
            self._append_node(child, content, base_url=base_url)
        return content

    def _append_node(self, node: Any, content: ParsedContent, *, base_url: str) -> None:
        if isinstance(node, NavigableString):
            self._append_text(str(node), content)
            return
        if not isinstance(node, Tag) or self._skip(node):
            return

        if node.name == "img":
            self._append_image(node, content, base_url=base_url)
            return
        if node.name == "iframe":
            self._append_iframe(node, content, base_url=base_url)
            return
        if node.name == "video":
            self._append_video(node, content, base_url=base_url)
            return
        if self._is_series(node):
            self._append_series(node, content, base_url=base_url)
            return
        if node.name == "a" and node.has_attr("href"):
            image = node.select_one("img")
            if image is not None:
                self._append_image(image, content, base_url=base_url, source_url=urljoin(base_url, str(node.get("href"))))
            else:
                self._append_link(node, content, base_url=base_url)
            return
        if node.select_one("img, iframe, video, a[href], .series, .writing_series"):
            for child in node.children:
                self._append_node(child, content, base_url=base_url)
            return
        self._append_text(node.get_text(" ", strip=True), content)

    def _append_text(self, value: str, content: ParsedContent) -> None:
        text = " ".join(value.split())
        if text:
            content.blocks.append(TextBlock(order=len(content.blocks), text=text))

    def _append_image(self, node: Tag, content: ParsedContent, *, base_url: str, source_url: str | None = None) -> None:
        url = _media_url(node, base_url=base_url)
        if not url:
            return
        block = ImageBlock(
            order=len(content.blocks),
            url=url,
            source_url=source_url or _attr(node, "data-original") or None,
            alt=_attr(node, "alt") or _attr(node, "title") or None,
        )
        content.blocks.append(block)
        content.images.append(MediaItem(media_type=MediaType.IMAGE, url=url, source_url=block.source_url, media_id=_media_id(_query_value(url, "no"))))

    def _append_iframe(self, node: Tag, content: ParsedContent, *, base_url: str) -> None:
        src = urljoin(base_url, _attr(node, "src"))
        if not src:
            return
        if "youtube.com" in src or "youtu.be" in src:
            content.blocks.append(YouTubeBlock(order=len(content.blocks), url=src, video_id=_youtube_id(src)))
            return
        if "/board/movie/movie_view" in src:
            movie_no = _query_value(src, "no")
            content.blocks.append(DcVideoBlock(order=len(content.blocks), url=src, metadata={"iframe_url": src, "movie_no": movie_no}))
            content.images.append(MediaItem(media_type=MediaType.DC_VIDEO, media_id=movie_no, url=src, source_url=src))
            return
        content.blocks.append(UnknownEmbedBlock(order=len(content.blocks), kind="iframe", reason="unsupported_iframe"))

    def _append_video(self, node: Tag, content: ParsedContent, *, base_url: str) -> None:
        src = _media_url(node, base_url=base_url) or _media_url(node.select_one("source"), base_url=base_url)
        if src:
            content.blocks.append(DcVideoBlock(order=len(content.blocks), url=src, thumbnail_url=_attr(node, "poster") or None))
            content.images.append(MediaItem(media_type=MediaType.DC_VIDEO, url=src, source_url=src))

    def _append_link(self, node: Tag, content: ParsedContent, *, base_url: str) -> None:
        url = urljoin(base_url, str(node.get("href")))
        text = node.get_text(" ", strip=True)
        content.blocks.append(LinkBlock(order=len(content.blocks), url=url, text=text or None, title=_attr(node, "title") or None))
        content.links.append(ContentLink(url=url, text=text or None, title=_attr(node, "title") or None))

    def _append_series(self, node: Tag, content: ParsedContent, *, base_url: str) -> None:
        link = node.select_one("a[href]")
        url = urljoin(base_url, str(link.get("href"))) if link is not None else None
        content.blocks.append(
            SeriesBlock(
                order=len(content.blocks),
                title=node.get_text(" ", strip=True) or None,
                url=url,
                post_count=parse_count(_text(node.select_one(".count"))),
            )
        )

    def _skip(self, node: Tag) -> bool:
        if node.name in {"script", "button", "style"}:
            return True
        classes = set(node.get("class", []))
        return bool(classes & self.noise_classes)

    @staticmethod
    def _is_series(node: Tag) -> bool:
        classes = set(node.get("class", []))
        return bool(classes & {"series", "writing_series", "series_area"})


class RepostClient:
    pattern = re.compile(r"(?P<url>/ajax/pum_ajax/get_contents[^'\"\s<)]*)")

    @classmethod
    def extract_url(cls, html: str, *, base_url: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        node = soup.select_one("[data-repost-url]")
        if node is not None:
            return urljoin(base_url, str(node.get("data-repost-url")))
        match = cls.pattern.search(html)
        return urljoin(base_url, match.group("url")) if match else None


class RepostParser:
    def __init__(self) -> None:
        self.content_parser = ContentBlockParser()

    def parse(self, html: str, *, current_url: str) -> RepostParseResult:
        soup = BeautifulSoup(html, "html.parser")
        card = soup.select_one(".cloned_card, .repost_card, article") or soup
        link = card.select_one("a[href*='/board/view/']")
        parsed_url = _safe_parse_post_url(urljoin(current_url, str(link.get("href"))) if link is not None else "")
        gallery_id = parsed_url.get("gallery_id") or _text(card.select_one(".gallery_id"))
        post_id = parsed_url.get("post_id") or str(parse_count(_text(card.select_one(".gall_num"))) or "")
        if not gallery_id or not post_id:
            raise ParseFailureError("repost identity missing", details={"reason": "repost_identity_missing"})
        author = _parse_author(card.select_one(".gall_writer") or card.select_one(".writer"))
        repost = RepostInfo(
            gallery_id=gallery_id,
            gallery_name=_text(card.select_one(".gallery_name")) or None,
            post_id=post_id,
            post_number=parsed_url.get("post_number") or parse_count(post_id),
            author=author,
            nickname_type=author.nickname_type,
            views=parse_count(_text(card.select_one(".gall_count, .views"))),
            recommendations=RecommendationInfo(upvotes=parse_count(_text(card.select_one(".gall_reply_num, .up_num")))),
        )
        body = card.select_one(".cloned_card_body, .repost_body, .write_div") or card
        return RepostParseResult(repost=repost, content=self.content_parser.parse(body, base_url=current_url))


class DcVideoMetadataResolver:
    async def resolve(self, client: Any, iframe_url: str) -> dict[str, Any]:
        response = await client.get(iframe_url)
        soup = BeautifulSoup(_response_text(response), "html.parser")
        description = _text(soup.select_one("body > div > div > div.video_infobox > div.box > div"))
        video = soup.select_one("video[src], source[src]")
        poster = _attr(soup.select_one("video[poster]"), "poster") or _attr(soup.select_one("img[src]"), "src")
        download = soup.select_one("a[href*='download']")
        return {
            "video_url": _media_url(video, base_url=iframe_url) if video is not None else None,
            "poster_url": urljoin(iframe_url, poster) if poster else None,
            "download_url": urljoin(iframe_url, str(download.get("href"))) if download is not None else None,
            "description": description or None,
        }


class CommentPaginationGuard:
    def __init__(self, max_pages: int = 100) -> None:
        if max_pages < 1:
            raise ValueError("max_pages must be >= 1")
        self.max_pages = max_pages

    def check(self, *, page: int, comment_count: int, has_next: bool) -> PaginationDecision:
        if page >= self.max_pages and has_next:
            return PaginationDecision(False, "comment_page_limit")
        if comment_count == 0:
            return PaginationDecision(False, "empty_page")
        if not has_next:
            return PaginationDecision(False, "pagination_end")
        return PaginationDecision(True, "continue")


class CommentMemoParser:
    def parse(self, memo: str | None) -> tuple[str | None, list[DcconItem]]:
        raw = memo or ""
        if "<" not in raw and ">" not in raw:
            return (raw.strip() or None, [])
        soup = BeautifulSoup(raw, "html.parser")
        dccons: list[DcconItem] = []
        for node in soup.select("img.written_dccon, video.written_dccon"):
            src = _attr(node, "src") or _attr(node, "data-src")
            dccons.append(
                DcconItem(
                    src=src or None,
                    alt=_attr(node, "alt") or None,
                    title=_attr(node, "title") or None,
                    conalt=_attr(node, "conalt") or _attr(node, "data-conalt") or None,
                )
            )
            node.decompose()
        text = soup.get_text(" ", strip=True)
        return (text or None, dccons)


class CommentAjaxParser:
    def __init__(self) -> None:
        self.memo_parser = CommentMemoParser()

    def parse(self, text: str, *, current_page: int = 1) -> CommentPage:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ParseFailureError("comment JSON invalid", details={"reason": "comment_json_invalid"}) from exc
        items = _comment_items(payload)
        comments = [self._comment_from_item(item) for item in items]
        total_page = parse_count(str(payload.get("total_page") or payload.get("totalPage") or ""))
        pagination = payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}
        has_next = bool(pagination.get("next") or pagination.get("has_next"))
        if total_page is not None:
            has_next = current_page < total_page
        return CommentPage(comments=comments, has_next=has_next)

    def _comment_from_item(self, item: dict[str, Any]) -> Comment:
        number = parse_count(str(item.get("no") or item.get("comment_no") or item.get("id") or ""))
        depth = parse_count(str(item.get("depth") or 0)) or 0
        parent_number = parse_count(str(item.get("c_no") or item.get("parent_no") or "")) if depth else None
        memo_text, dccons = self.memo_parser.parse(str(item.get("memo") or ""))
        author = AuthorInfo(
            name=str(item.get("name") or "").strip() or None,
            user_id=str(item.get("user_id") or item.get("uid") or "").strip() or None,
            ip=str(item.get("ip") or "").strip() or None,
        )
        author.nickname_type = classify_nickname_type(user_id=author.user_id, ip=author.ip)
        return Comment(
            comment_id=str(number or item.get("no") or item.get("id") or "unknown"),
            comment_number=number,
            parent_comment_id=str(parent_number) if parent_number is not None else None,
            parent_comment_number=parent_number,
            depth=depth,
            author=author,
            memo_text=memo_text,
            dccons=dccons,
            created_at=parse_dcinside_date(str(item.get("reg_date") or item.get("date") or "").strip()),
            metadata={"deleted": item.get("del_yn") == "Y" or item.get("is_delete") is True},
        )


class CommentHtmlFallbackParser:
    def __init__(self) -> None:
        self.memo_parser = CommentMemoParser()

    def parse(self, html: str) -> list[Comment]:
        soup = BeautifulSoup(html, "html.parser")
        comments: list[Comment] = []
        for item in soup.select("li[id^='comment_li_']"):
            if item.get("id") == "comment_li_0" or {"dory", "cmt_pw_ad"} & set(item.get("class", [])):
                continue
            comment = self._comment_from_node(item, depth=0)
            comments.append(comment)
            sibling = item.find_next_sibling("li")
            reply_list = sibling.select_one(f"ul.reply_list[p-no='{comment.comment_id}']") if isinstance(sibling, Tag) else None
            if reply_list is not None:
                for reply in reply_list.select("li[id^='reply_li_'], li"):
                    if isinstance(reply, Tag):
                        comments.append(self._comment_from_node(reply, depth=1, parent=comment))
        return comments

    def _comment_from_node(self, node: Tag, *, depth: int, parent: Comment | None = None) -> Comment:
        node_id = str(node.get("id") or "")
        number = parse_count(node_id) or parse_count(_attr(node, "data-no"))
        memo = _text(node.select_one(".cmt_txtbox, .usertxt, .memo")) or _text(node)
        memo_text, dccons = self.memo_parser.parse(memo)
        writer = node.select_one(".gall_writer") or node.select_one(".writer")
        author = _parse_author(writer)
        return Comment(
            comment_id=str(number or node_id or "unknown"),
            comment_number=number,
            parent_comment_id=parent.comment_id if parent else None,
            parent_comment_number=parent.comment_number if parent else None,
            depth=depth,
            author=author,
            memo_text=memo_text,
            dccons=dccons,
            created_at=parse_dcinside_date(_text(node.select_one(".date_time, .date"))),
        )


class CommentService:
    def __init__(self, client: Any, *, logger: LoggerPort | None = None, max_comment_pages: int = 100) -> None:
        self.client = client
        self.logger = logger or NullLogger()
        self.guard = CommentPaginationGuard(max_comment_pages)
        self.parser = CommentAjaxParser()

    async def collect(self, request: CommentRequest) -> CommentCollection:
        page = 1
        collection = CommentCollection()
        while True:
            response = await _client_post(
                self.client,
                COMMENT_URL,
                data={
                    "id": request.gallery_id,
                    "no": request.post_id,
                    "cmt_id": request.gallery_id,
                    "cmt_no": request.post_id,
                    "comment_page": page,
                    "sort": "D",
                },
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            parsed = self.parser.parse(_response_text(response), current_page=page)
            collection.comments.extend(parsed.comments)
            decision = self.guard.check(page=page, comment_count=len(parsed.comments), has_next=parsed.has_next)
            if not decision.should_continue:
                if decision.reason == "comment_page_limit":
                    collection.failures.append(
                        make_safe_detail_failure(stage="comments", reason=decision.reason, retryable=False, failed_fields=["comments"])
                    )
                break
            page += 1
        return collection

    async def fetch_comments(self, request: CommentRequest) -> list[Comment]:
        return (await self.collect(request)).comments


class PostDetailService:
    def __init__(self, client: Any, *, logger: LoggerPort | None = None) -> None:
        self.client = client
        self.logger = logger or NullLogger()
        self.metadata_parser = PostMetadataParser()
        self.content_parser = ContentBlockParser()
        self.repost_parser = RepostParser()
        self.video_resolver = DcVideoMetadataResolver()

    async def fetch_post(self, request: PostRequest) -> PostResult:
        response = await self.client.get(request.url)
        html = _response_text(response)
        recorder = DetailFailureRecorder()
        parsed = self.metadata_parser.parse(html, request)
        content = self.content_parser.parse(html, base_url=request.url)
        await self._resolve_videos(content, recorder)
        repost = await self._fetch_repost(html, request_url=request.url, is_repost=parsed.is_repost, content=content, recorder=recorder)
        comments: list[Comment] = []
        if request.scrape_options.include_comments:
            comments = await self._fetch_comments(parsed, request, recorder)

        return PostResult(
            gallery_id=parsed.gallery_id,
            post_id=parsed.post_id,
            post_number=parsed.post_number,
            is_repost=parsed.is_repost,
            repost=repost,
            title=parsed.title,
            author=parsed.author,
            nickname_type=parsed.nickname_type,
            date=parsed.date,
            views=parsed.views,
            recommendations=parsed.recommendations,
            comment_count=parsed.comment_count,
            content=content.blocks,
            images=content.images,
            comments=comments,
            links=content.links,
            metadata=recorder.apply(parsed.metadata),
        )

    async def _resolve_videos(self, content: ParsedContent, recorder: DetailFailureRecorder) -> None:
        for block in content.blocks:
            if not isinstance(block, DcVideoBlock):
                continue
            iframe_url = block.metadata.get("iframe_url") if isinstance(block.metadata, dict) else None
            if not iframe_url:
                continue
            try:
                resolved = await self.video_resolver.resolve(self.client, str(iframe_url))
            except (CaptchaDetectedError, BlockedResponseError):
                raise
            except ScraperError as exc:
                recorder.record(stage="dc_video", reason=exc.safe_message, retryable=exc.retryable, failed_fields=["dc_video"])
                continue
            if resolved.get("video_url"):
                block.url = resolved["video_url"]
            block.thumbnail_url = resolved.get("poster_url")
            block.description = resolved.get("description")
            block.metadata = {**block.metadata, "download_url": resolved.get("download_url")}

    async def _fetch_repost(
        self,
        html: str,
        *,
        request_url: str,
        is_repost: bool,
        content: ParsedContent,
        recorder: DetailFailureRecorder,
    ) -> RepostInfo | None:
        if not is_repost:
            return None
        ajax_url = RepostClient.extract_url(html, base_url=request_url)
        if not ajax_url:
            recorder.record(stage="repost", reason="repost_ajax_url_missing", failed_fields=["repost"])
            return _unresolved_repost()
        try:
            response = await self.client.get(ajax_url)
            parsed = self.repost_parser.parse(_response_text(response), current_url=ajax_url)
        except (CaptchaDetectedError, BlockedResponseError):
            raise
        except ScraperError as exc:
            recorder.record(stage="repost", reason=exc.safe_message, retryable=exc.retryable, failed_fields=["repost"])
            return _unresolved_repost()
        _extend_content(content, parsed.content)
        return parsed.repost

    async def _fetch_comments(self, parsed: ParsedMetadata, request: PostRequest, recorder: DetailFailureRecorder) -> list[Comment]:
        try:
            collection = await CommentService(
                self.client,
                logger=self.logger,
                max_comment_pages=request.scrape_options.max_comment_pages,
            ).collect(
                CommentRequest(
                    gallery_id=parsed.gallery_id,
                    post_id=parsed.post_id,
                    post_number=parsed.post_number,
                    gallery_type=parsed.gallery_type,
                )
            )
        except (CaptchaDetectedError, BlockedResponseError):
            raise
        except ScraperError as exc:
            recorder.record(stage="comments", reason=exc.safe_message, retryable=exc.retryable, failed_fields=["comments"])
            return []
        recorder.failures.extend(collection.failures)
        return collection.comments


def _extend_content(target: ParsedContent, extra: ParsedContent) -> None:
    for block in extra.blocks:
        block.order = len(target.blocks)
        target.blocks.append(block)
    target.images.extend(extra.images)
    target.links.extend(extra.links)


def _unresolved_repost() -> RepostInfo:
    return RepostInfo(
        gallery_id="unknown",
        post_id="unknown",
        author=AuthorInfo(nickname_type=NicknameType.UNKNOWN),
        metadata={"unresolved": True},
    )


async def _client_post(client: Any, url: str, *, data: dict[str, Any], headers: dict[str, str] | None = None) -> Any:
    try:
        return await client.post(url, data=data, headers=headers)
    except TypeError:
        return await client.post(url, data=data)


def _response_text(response: Any) -> str:
    return str(getattr(response, "text", response))


def _safe_parse_post_url(url: str) -> dict[str, Any]:
    try:
        parsed = parse_post_url(url)
    except ScraperError:
        return {}
    return {
        "gallery_id": parsed.gallery_id,
        "post_id": parsed.post_id,
        "post_number": parsed.post_number,
        "gallery_type": parsed.gallery_type,
    }


def _parse_author(node: Tag | None) -> AuthorInfo:
    if node is None:
        return AuthorInfo()
    text = node.get_text(" ", strip=True)
    ip_match = re.search(r"\((?P<ip>\d{1,3}(?:\.\d{1,3}){1,3})\)", text)
    user_id = _attr(node, "data-uid") or _attr(node, "data-user-id") or _attr(node, "user_id") or None
    ip = _attr(node, "data-ip") or (ip_match.group("ip") if ip_match else None)
    name = _attr(node, "data-nick") or re.sub(r"\s*\([^)]*\)\s*$", "", text).strip() or None
    nickname_type = classify_nickname_type(user_id=user_id, ip=ip, classes=list(node.get("class", [])))
    return AuthorInfo(name=name, user_id=user_id, ip=ip, nickname_type=nickname_type)


def _title_text(node: Tag | None) -> str:
    if node is None:
        return ""
    subject = node.select_one(".title_subject")
    if subject is not None:
        return subject.get_text(" ", strip=True)
    raw = node.get_text(" ", strip=True)
    for child in node.select("b.font_blue009, .title_headtext, .headtext, .title_device, .blind"):
        child_text = child.get_text(" ", strip=True)
        raw = raw.replace(child_text, "", 1).strip()
    return raw


def _subject_head(soup: BeautifulSoup) -> dict[str, Any] | None:
    node = soup.select_one(".title_headtext, .title_subject, .headtext")
    if node is None:
        return None
    head_id = _attr(node, "data-head-id") or _attr(node, "data-id") or None
    return {"id": parse_count(head_id), "name": node.get_text(" ", strip=True)}


def _comment_params(soup: BeautifulSoup) -> dict[str, str]:
    params: dict[str, str] = {}
    for key in ("e_s_n_o", "board_type", "_GALLTYPE_", "secret_article_key"):
        node = soup.select_one(f"#{key}, input[name='{key}']")
        value = _attr(node, "value")
        if value:
            params[key] = value
    return params


def _comment_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("comments", "comment_list", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                nested = _comment_items(value)
                if nested:
                    return nested
    return []


def _media_url(node: Tag | None, *, base_url: str) -> str | None:
    if node is None:
        return None
    value = _attr(node, "data-src") or _attr(node, "src") or _attr(node, "href")
    return urljoin(base_url, value) if value else None


def _youtube_id(url: str) -> str | None:
    match = re.search(r"(?:embed/|youtu\.be/|v=)(?P<id>[A-Za-z0-9_-]+)", url)
    return match.group("id") if match else None


def _query_value(url: str, key: str) -> str | None:
    values = parse_qs(urlsplit(url).query).get(key)
    return values[0] if values else None


def _media_id(value: str | None) -> str | None:
    if value and len(value) <= 200:
        return value
    return None


def _text(node: Tag | None) -> str:
    return node.get_text(" ", strip=True) if node is not None else ""


def _attr(node: Tag | None, name: str) -> str:
    return str(node.get(name, "")) if node is not None and node.has_attr(name) else ""


def _first_text(*values: str | None) -> str:
    for value in values:
        if value:
            return value
    return ""
