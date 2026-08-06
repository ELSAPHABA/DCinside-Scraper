"""Protocol contracts for external dependencies."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.media import MediaItem
from dcinside_scraper.models.post import PostResult
from dcinside_scraper.models.report import FailureRecord, JobReport, StoredObjectRef


@runtime_checkable
class HttpPort(Protocol):
    async def get(self, url: str, *, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> Any:
        ...

    async def post(self, url: str, *, data: Any = None, headers: dict[str, str] | None = None) -> Any:
        ...

    async def download(self, url: str, *, headers: dict[str, str] | None = None) -> bytes:
        ...

    async def close(self) -> None:
        ...


@runtime_checkable
class OutputStorePort(Protocol):
    async def append_post(self, post: PostResult) -> StoredObjectRef:
        ...

    async def write_failure(self, failure: FailureRecord) -> StoredObjectRef:
        ...

    async def finalize(self, report: JobReport) -> None:
        ...


@runtime_checkable
class MediaStorePort(Protocol):
    async def save_media(self, item: MediaItem, content: bytes) -> MediaItem:
        ...

    async def save_metadata_only(self, item: MediaItem) -> MediaItem:
        ...


@runtime_checkable
class CheckpointStorePort(Protocol):
    async def save(self, checkpoint: Checkpoint) -> None:
        ...

    async def load(self, job_id: str) -> Checkpoint | None:
        ...

    async def load_latest(self) -> Checkpoint | None:
        ...


@runtime_checkable
class ClockPort(Protocol):
    def now_utc(self) -> datetime:
        ...


@runtime_checkable
class LoggerPort(Protocol):
    def debug(self, message: str, **fields: Any) -> None:
        ...

    def info(self, message: str, **fields: Any) -> None:
        ...

    def warning(self, message: str, **fields: Any) -> None:
        ...

    def error(self, message: str, **fields: Any) -> None:
        ...

