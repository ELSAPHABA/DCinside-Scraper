"""Public async API surface.

Executable behavior is implemented by later units. These functions keep the
library import-safe and establish stable type contracts for adapters.
"""

from __future__ import annotations

from dcinside_scraper.core.errors import UnavailableContentError
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


async def search_gallery(request: GallerySearchRequest) -> GallerySearchPage:
    raise UnavailableContentError("search_gallery is implemented in UOW-003")


async def search_integrated(request: IntegratedSearchRequest) -> IntegratedSearchPage:
    raise UnavailableContentError("search_integrated is implemented in UOW-003")


async def fetch_post(request: PostRequest) -> PostResult:
    raise UnavailableContentError("fetch_post is implemented in UOW-004")


async def fetch_comments(request: CommentRequest) -> list[Comment]:
    raise UnavailableContentError("fetch_comments is implemented in UOW-004")


async def run_job(config: JobConfig) -> JobReport:
    raise UnavailableContentError("run_job is implemented in UOW-005")


async def resume_job(request: ResumeRequest) -> JobReport:
    raise UnavailableContentError("resume_job is implemented in UOW-005")

