from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from dcinside_scraper.core import api
from dcinside_scraper.core.errors import ValidationFailure
from dcinside_scraper.models.content import DcVideoBlock, ImageBlock, LinkBlock, SeriesBlock, TextBlock, YouTubeBlock
from dcinside_scraper.models.enums import GalleryType, NicknameType
from dcinside_scraper.models.job import CommentRequest, PostRequest, ScrapeOptions
from dcinside_scraper.post_detail import (
    CommentAjaxParser,
    CommentHtmlFallbackParser,
    ContentBlockParser,
    PostDetailService,
    PostMetadataParser,
    SafeDetailEventBuilder,
    make_safe_detail_failure,
)

FIXTURES = Path(__file__).parent / "fixtures" / "post_detail"


@dataclass
class FakeResponse:
    text: str


class FakeClient:
    def __init__(self, detail: str) -> None:
        self.detail = detail
        self.get_urls: list[str] = []
        self.post_calls: list[tuple[str, dict]] = []
        self.post_referers: list[str | None] = []

    async def get(self, url, *, headers=None, params=None):
        self.get_urls.append(url)
        if "movie_view" in url:
            return FakeResponse((FIXTURES / "dc_video_iframe.html").read_text(encoding="utf-8"))
        if "pum_ajax" in url:
            return FakeResponse((FIXTURES / "repost_ajax.html").read_text(encoding="utf-8"))
        return FakeResponse(self.detail)

    async def post(self, url, *, data=None, headers=None, referer=None):
        self.post_calls.append((url, data or {}))
        self.post_referers.append(referer)
        return FakeResponse((FIXTURES / "comments_page.json").read_text(encoding="utf-8"))

    async def download(self, url, *, headers=None):
        return b""

    async def close(self):
        return None


def run(coro):
    return asyncio.run(coro)


def test_metadata_and_content_parser_extract_detail_shape() -> None:
    html = (FIXTURES / "normal_post.html").read_text(encoding="utf-8")
    request = PostRequest(url="https://gall.dcinside.com/mgallery/board/view/?id=singlebungle1472&no=100")

    metadata = PostMetadataParser().parse(html, request)
    content = ContentBlockParser().parse(html, base_url=request.url)

    assert metadata.gallery_id == "singlebungle1472"
    assert metadata.post_number == 100
    assert metadata.title == "일반 제목"
    assert metadata.metadata["subject_head"] == {"id": 160, "name": "2D"}
    assert metadata.recommendations.upvotes == 7
    assert [type(block) for block in content.blocks] == [TextBlock, ImageBlock, DcVideoBlock, YouTubeBlock, LinkBlock, SeriesBlock]
    assert content.images[0].media_type == "image"
    assert content.links[0].url == "https://example.com/article"


def test_content_parser_ignores_oversized_image_media_id() -> None:
    token = "x" * 201
    html = f'<div class="write_div"><img src="/viewimage.php?no={token}"></div>'

    content = ContentBlockParser().parse(html, base_url="https://gall.dcinside.com/board/view/?id=x&no=1")

    assert content.images[0].media_id is None
    assert content.images[0].url.endswith(token)


def test_post_detail_service_fetches_video_comments_and_uses_public_api() -> None:
    html = (FIXTURES / "normal_post.html").read_text(encoding="utf-8")
    client = FakeClient(html)
    request = PostRequest(url="https://gall.dcinside.com/mgallery/board/view/?id=singlebungle1472&no=100&s_keyword=싱글벙글")

    post = run(api.fetch_post(request, client))

    video = next(block for block in post.content if isinstance(block, DcVideoBlock))
    assert video.url == "https://media.example.test/movie.mp4"
    assert video.description == "동영상 설명"
    assert len(post.comments) == 2
    assert post.comments[1].parent_comment_id == "1"
    assert post.comments[1].dccons[0].src == "/dccon.png"
    assert client.post_calls[0][1]["comment_page"] == 1
    assert client.post_calls[0][1]["e_s_n_o"] == "token-1"
    assert client.post_calls[0][1]["_GALLTYPE_"] == "M"
    assert client.post_calls[0][1]["focus_cno"] == ""
    assert client.post_calls[0][1]["nptest"] == ""
    assert "%EC%8B%B1%EA%B8%80%EB%B2%99%EA%B8%80" in (client.post_referers[0] or "")


def test_repost_ajax_populates_repost_info_and_strips_title_marker() -> None:
    html = (FIXTURES / "repost_post.html").read_text(encoding="utf-8")
    request = PostRequest(
        url="https://gall.dcinside.com/mgallery/board/view/?id=stockus&no=200",
        scrape_options=ScrapeOptions(include_comments=False),
    )

    post = run(PostDetailService(FakeClient(html)).fetch_post(request))

    assert post.is_repost is True
    assert post.title == "리포스트 제목"
    assert post.repost is not None
    assert post.repost.gallery_id == "origin"
    assert post.repost.post_number == 10
    assert post.repost.views == 58
    assert post.repost.recommendations.upvotes == 4
    assert any(isinstance(block, ImageBlock) for block in post.content)


def test_comment_ajax_and_rendered_fallback_parsers_preserve_replies() -> None:
    page = CommentAjaxParser().parse((FIXTURES / "comments_page.json").read_text(encoding="utf-8"))
    rendered = CommentHtmlFallbackParser().parse((FIXTURES / "comments_rendered_fallback.html").read_text(encoding="utf-8"))

    assert page.comments[0].depth == 0
    assert page.comments[1].depth == 1
    assert page.comments[1].parent_comment_number == 1
    assert page.comments[1].author.nickname_type == NicknameType.FIXED
    assert rendered[1].parent_comment_id == "10"
    assert rendered[1].author.user_id == "reply-id"


def test_comment_ajax_parser_ignores_comment_ad_items() -> None:
    payload = {
        "comments": [
            {"no": "1", "name": "ㅇㅇ", "memo": "real", "reg_date": "2026.08.06 12:00:01"},
            {"no": 0, "nicktype": "COMMENT_BOY", "name": "댓글돌이", "memo": "ad"},
        ]
    }

    page = CommentAjaxParser().parse(json.dumps(payload))

    assert [comment.comment_id for comment in page.comments] == ["1"]


def test_failure_and_event_builders_exclude_raw_values() -> None:
    failure = make_safe_detail_failure(stage="metadata", reason="bad", raw_html="<html>", failed_fields=["title"])
    event = SafeDetailEventBuilder.build(
        "detail_parse",
        url="https://gall.dcinside.com/board/view/?id=x&no=1&ci_t=secret",
        raw_html="<html>",
        cookie="secret",
        count=1,
    )

    assert failure == {
        "stage": "metadata",
        "reason": "bad",
        "retryable": False,
        "field_path": None,
        "failed_fields": ["title"],
    }
    assert event["url"] == "https://gall.dcinside.com/board/view/"
    assert "secret" not in repr(event)


def test_public_post_detail_apis_require_client() -> None:
    with pytest.raises(ValidationFailure):
        run(api.fetch_post(PostRequest(url="https://gall.dcinside.com/board/view/?id=x&no=1")))
    with pytest.raises(ValidationFailure):
        run(api.fetch_comments(CommentRequest(gallery_id="x", post_id="1", gallery_type=GalleryType.MAJOR)))
