"""S3-backed output and media store for container runtime."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dcinside_scraper.models.media import MediaItem
from dcinside_scraper.models.post import PostResult
from dcinside_scraper.models.report import FailureRecord, JobReport, StoredObjectRef
from dcinside_scraper.outputs.jsonl import JsonlWriter
from dcinside_scraper.outputs.layout import OutputRunLayout
from dcinside_scraper.outputs.redaction import SafeFailureRecordBuilder
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

    async def read_failures(self, failure_input: Any) -> list[FailureRecord]:
        object_key = self._input_key(failure_input)
        content = await self.object_store.get_bytes(object_key)
        return [
            FailureRecord.model_validate(json.loads(line))
            for line in content.decode("utf-8").splitlines()
            if line.strip()
        ]

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

    def _input_key(self, failure_input: Any) -> str:
        raw = getattr(failure_input, "failure_path", None) or getattr(failure_input, "uri", None) or failure_input
        if raw is None:
            return self.layout.prefixed_key(self.layout.failures_key)
        text = str(raw)
        if text.startswith("s3://"):
            return urlparse(text).path.lstrip("/")
        if text == self.layout.failures_key:
            return self.layout.prefixed_key(text)
        return text.lstrip("/")
