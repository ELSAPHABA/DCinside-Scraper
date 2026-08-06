from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from dcinside_scraper.core import api
from dcinside_scraper.core.errors import UnavailableContentError
from dcinside_scraper.core.ports import (
    CheckpointStorePort,
    ClockPort,
    HttpPort,
    LoggerPort,
    MediaStorePort,
    OutputStorePort,
)
from dcinside_scraper.models.job import GallerySearchRequest, ResumeRequest


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

    async def write_failure(self, failure):
        return None

    async def finalize(self, report):
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


def test_ports_accept_structural_fakes() -> None:
    assert isinstance(FakeHttp(), HttpPort)
    assert isinstance(FakeOutputStore(), OutputStorePort)
    assert isinstance(FakeMediaStore(), MediaStorePort)
    assert isinstance(FakeCheckpointStore(), CheckpointStorePort)
    assert isinstance(FakeClock(), ClockPort)
    assert isinstance(FakeLogger(), LoggerPort)


def test_public_api_placeholders_are_import_safe() -> None:
    request = GallerySearchRequest(
        gallery_type="minor",
        gallery_id="singlebungle1472",
        s_type="search_subject_memo",
        keyword="test",
    )
    with pytest.raises(UnavailableContentError):
        asyncio.run(api.search_gallery(request))


def test_resume_placeholder_is_import_safe() -> None:
    with pytest.raises(UnavailableContentError):
        asyncio.run(api.resume_job(ResumeRequest(job_id="job-1")))

