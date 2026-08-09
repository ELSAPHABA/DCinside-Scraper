"""S3-backed output and media store for container runtime."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from dcinside_scraper.models.media import MediaItem
from dcinside_scraper.models.post import PostResult
from dcinside_scraper.models.report import FailureRecord, JobReport, StoredObjectRef
from dcinside_scraper.outputs.local import JsonlWriter, OutputRunLayout, SafeFailureRecordBuilder
from dcinside_scraper.outputs.s3 import S3ObjectStore


class S3Spool:
    def __init__(self, base_path: str | Path | None = None) -> None:
        self.base_path = Path(base_path or tempfile.mkdtemp(prefix="dcinside-s3-spool-")).resolve(strict=False)
        self.posts_path = self.base_path / "posts.jsonl"
        self.failures_path = self.base_path / "failures.jsonl"

    def cleanup(self) -> None:
        shutil.rmtree(self.base_path, ignore_errors=True)


class S3OutputStore:
    def __init__(self, layout: OutputRunLayout, object_store: S3ObjectStore, *, spool: S3Spool | None = None) -> None:
        self.layout = layout
        self.object_store = object_store
        self.spool = spool or S3Spool()
        self._post_writer = JsonlWriter(self.spool.posts_path)
        self._failure_writer = JsonlWriter(self.spool.failures_path)

    async def append_post(self, post: PostResult) -> StoredObjectRef:
        self._post_writer.append(post)
        return await self.object_store.put_bytes(
            self.layout.posts_key,
            self.spool.posts_path.read_bytes(),
            content_type="application/x-ndjson",
        )

    async def write_failure(self, failure: FailureRecord) -> StoredObjectRef:
        self._failure_writer.append(SafeFailureRecordBuilder.sanitize(failure))
        return await self.object_store.put_bytes(
            self.layout.failures_key,
            self.spool.failures_path.read_bytes(),
            content_type="application/x-ndjson",
        )

    async def finalize(self, report: JobReport) -> None:
        try:
            await self.object_store.put_bytes(
                self.layout.report_key,
                report.model_dump_json().encode("utf-8"),
                content_type="application/json",
            )
        finally:
            self.spool.cleanup()

    async def save_media(self, item: MediaItem, content: bytes) -> MediaItem:
        key = self.layout.media_key(
            item.metadata.get("gallery_id", "unknown_gallery"),
            item.metadata.get("post_number") or item.metadata.get("post_id", "unknown_post"),
            str(item.media_type),
            item.media_id or Path(item.url).name or "media.bin",
        )
        ref = await self.object_store.put_bytes(key, content, content_type="application/octet-stream")
        return item.model_copy(update={"object_key": ref.object_key, "file_path": None})

    async def save_metadata_only(self, item: MediaItem) -> MediaItem:
        return item
