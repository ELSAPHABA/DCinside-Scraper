"""Public async API surface.

Executable behavior is implemented by later units. These functions keep the
library import-safe and establish stable type contracts for adapters.
"""

from __future__ import annotations

from dcinside_scraper.core.errors import UnavailableContentError, ValidationFailure
from dcinside_scraper.core.ports import HttpPort
from dcinside_scraper.models.comment import Comment
from dcinside_scraper.models.job import (
    CommentRequest,
    GallerySearchPage,
    GallerySearchRequest,
    IntegratedSearchPage,
    IntegratedSearchRequest,
    JobConfig,
    PostRequest,
    ResumeRequest,
)
from dcinside_scraper.models.post import PostResult
from dcinside_scraper.models.report import JobReport
from dcinside_scraper.search import GallerySearchCollector, IntegratedSearchCollector


async def search_gallery(request: GallerySearchRequest, http_client: HttpPort | None = None) -> GallerySearchPage:
    if http_client is None:
        raise ValidationFailure("http_client is required", details={"reason": "http_client_required"})
    return await GallerySearchCollector(http_client).collect_page(request)


async def search_integrated(request: IntegratedSearchRequest, http_client: HttpPort | None = None) -> IntegratedSearchPage:
    if http_client is None:
        raise ValidationFailure("http_client is required", details={"reason": "http_client_required"})
    return await IntegratedSearchCollector(http_client).collect_page(request)


async def fetch_post(request: PostRequest) -> PostResult:
    raise UnavailableContentError("fetch_post is implemented in UOW-004")


async def fetch_comments(request: CommentRequest) -> list[Comment]:
    raise UnavailableContentError("fetch_comments is implemented in UOW-004")


async def run_job(config: JobConfig) -> JobReport:
    raise UnavailableContentError("run_job is implemented in UOW-005")


async def resume_job(request: ResumeRequest) -> JobReport:
    raise UnavailableContentError("resume_job is implemented in UOW-005")
