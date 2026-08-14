from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from dcinside_scraper.core import api
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
from dcinside_scraper.models.enums import JobReportStatus
from dcinside_scraper.models.job import GallerySearchRequest, ResumeRequest
from dcinside_scraper.models.report import JobReport
from dcinside_scraper.retry import ParserFailureRetryRequest


class FakeHttp:
    async def get(self, url, *, headers=None, params=None):
        return None

    async def post(self, url, *, data=None, headers=None):
        return None

    async def download(self, url, *, headers=None):
        return b""

    async def close(self):
        return None


class FakeOutputStore:
    async def append_post(self, post):
        return None

    async def finalize(self, report):
        return None


class FakeFailureStore:
    async def write_failure(self, failure):
        return None

    async def read_failures(self, failure_input):
        return None


class FakeMediaStore:
    async def save_media(self, item, content):
        return item

    async def save_metadata_only(self, item):
        return item


class FakeCheckpointStore:
    async def save(self, checkpoint):
        return None

    async def load(self, job_id):
        return None

    async def load_latest(self):
        return None


class FakeClock:
    def now_utc(self):
        return datetime.now(timezone.utc)


class FakeLogger:
    def debug(self, message, **fields):
        return None

    def info(self, message, **fields):
        return None

    def warning(self, message, **fields):
        return None

    def error(self, message, **fields):
        return None


class FakeRetryService:
    def __init__(self) -> None:
        self.request = None

    async def retry(self, request, *, execute_job):
        self.request = request
        return await execute_job(None)


def test_ports_accept_structural_fakes() -> None:
    assert isinstance(FakeHttp(), HttpPort)
    assert isinstance(FakeOutputStore(), OutputStorePort)
    assert isinstance(FakeFailureStore(), FailureStorePort)
    assert isinstance(FakeMediaStore(), MediaStorePort)
    assert isinstance(FakeCheckpointStore(), CheckpointStorePort)
    assert isinstance(FakeClock(), ClockPort)
    assert isinstance(FakeLogger(), LoggerPort)


def test_public_search_api_requires_injected_client() -> None:
    request = GallerySearchRequest(
        gallery_type="minor",
        gallery_id="singlebungle1472",
        s_type="search_subject_memo",
        keyword="test",
    )
    with pytest.raises(ValidationFailure):
        asyncio.run(api.search_gallery(request))


def test_resume_requires_runner_dependencies() -> None:
    with pytest.raises(ValidationFailure):
        asyncio.run(api.resume_job(ResumeRequest(job_id="job-1")))


def test_retry_parser_failures_delegates_to_service() -> None:
    service = FakeRetryService()

    async def execute_job(config):
        return JobReport(job_id="retry-1", status=JobReportStatus.COMPLETED, success_count=1)

    report = asyncio.run(
        api.retry_parser_failures(
            ParserFailureRetryRequest(failure_refs=("failures.jsonl",), job_id="retry-1"),
            retry_service=service,
            execute_job=execute_job,
        )
    )

    assert report.job_id == "retry-1"
    assert service.request.failure_refs == ("failures.jsonl",)
