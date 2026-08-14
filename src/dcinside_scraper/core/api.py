"""Public async API surface.

Executable behavior is implemented by later units. These functions keep the
library import-safe and establish stable type contracts for adapters.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from dcinside_scraper.core.errors import ValidationFailure
from dcinside_scraper.core.ports import (
    CheckpointStorePort,
    ClockPort,
    FailureStorePort,
    HttpPort,
    LoggerPort,
    MediaStorePort,
    OutputStorePort,
)
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
from dcinside_scraper.post_detail import CommentService, PostDetailService
from dcinside_scraper.retry import ParserFailureRetryRequest, ParserFailureRetryService
from dcinside_scraper.runner import JobRunner
from dcinside_scraper.search import GallerySearchCollector, IntegratedSearchCollector


async def search_gallery(request: GallerySearchRequest, http_client: HttpPort | None = None) -> GallerySearchPage:
    if http_client is None:
        raise ValidationFailure("http_client is required", details={"reason": "http_client_required"})
    return await GallerySearchCollector(http_client).collect_page(request)


async def search_integrated(request: IntegratedSearchRequest, http_client: HttpPort | None = None) -> IntegratedSearchPage:
    if http_client is None:
        raise ValidationFailure("http_client is required", details={"reason": "http_client_required"})
    return await IntegratedSearchCollector(http_client).collect_page(request)


async def fetch_post(request: PostRequest, http_client: HttpPort | None = None) -> PostResult:
    if http_client is None:
        raise ValidationFailure("http_client is required", details={"reason": "http_client_required"})
    return await PostDetailService(http_client).fetch_post(request)


async def fetch_comments(request: CommentRequest, http_client: HttpPort | None = None) -> list[Comment]:
    if http_client is None:
        raise ValidationFailure("http_client is required", details={"reason": "http_client_required"})
    return await CommentService(http_client).fetch_comments(request)


async def run_job(
    config: JobConfig,
    *,
    runner: JobRunner | None = None,
    collector=None,
    post_detail=None,
    output_store: OutputStorePort | None = None,
    failure_store: FailureStorePort | None = None,
    media_store: MediaStorePort | None = None,
    checkpoint_store: CheckpointStorePort | None = None,
    http: HttpPort | None = None,
    logger: LoggerPort | None = None,
    clock: ClockPort | None = None,
) -> JobReport:
    if runner is not None:
        return await runner.run(config)
    if collector is None or post_detail is None or output_store is None or failure_store is None or checkpoint_store is None:
        raise ValidationFailure(
            "runner dependencies are required",
            details={"reason": "runner_dependencies_required"},
        )
    return await JobRunner(
        collector=collector,
        post_detail=post_detail,
        output_store=output_store,
        failure_store=failure_store,
        media_store=media_store,
        http=http,
        checkpoint_store=checkpoint_store,
        logger=logger,
        clock=clock,
    ).run(config)


async def resume_job(
    request: ResumeRequest,
    *,
    runner: JobRunner | None = None,
    collector=None,
    post_detail=None,
    output_store: OutputStorePort | None = None,
    failure_store: FailureStorePort | None = None,
    media_store: MediaStorePort | None = None,
    checkpoint_store: CheckpointStorePort | None = None,
    http: HttpPort | None = None,
    logger: LoggerPort | None = None,
    clock: ClockPort | None = None,
) -> JobReport:
    if runner is not None:
        return await runner.resume(request)
    if collector is None or post_detail is None or output_store is None or failure_store is None or checkpoint_store is None:
        raise ValidationFailure(
            "runner dependencies are required",
            details={"reason": "runner_dependencies_required"},
        )
    return await JobRunner(
        collector=collector,
        post_detail=post_detail,
        output_store=output_store,
        failure_store=failure_store,
        media_store=media_store,
        http=http,
        checkpoint_store=checkpoint_store,
        logger=logger,
        clock=clock,
    ).resume(request)


async def retry_parser_failures(
    request: ParserFailureRetryRequest,
    *,
    retry_service: Any | None = None,
    execute_job: Callable[[JobConfig], Awaitable[JobReport]] | None = None,
) -> JobReport:
    if execute_job is None:
        raise ValidationFailure("execute_job is required", details={"reason": "execute_job_required"})
    service = retry_service or ParserFailureRetryService()
    return await service.retry(request, execute_job=execute_job)
