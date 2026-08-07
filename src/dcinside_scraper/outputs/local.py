"""Local JSONL, media, and checkpoint storage."""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote, urlparse

from pydantic import BaseModel

from dcinside_scraper.core.errors import CheckpointFailureError, StorageFailureError
from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.job import StorageConfig
from dcinside_scraper.models.media import MediaItem
from dcinside_scraper.models.post import PostResult
from dcinside_scraper.models.report import FailureRecord, JobReport, StoredObjectRef

_SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9._-]+")

SAFE_FAILURE_CONTEXT_KEYS = {
    "site_id",
    "gallery_id",
    "post_id",
    "post_number",
    "url",
    "stage",
    "reason",
    "retryable",
    "http_status",
    "proxy_host",
    "user_agent",
}

_MEDIA_EXTENSIONS = {
    "image": ".bin",
    "dc_video": ".mp4",
    "youtube_thumbnail": ".jpg",
    "dccon": ".bin",
    "other": ".bin",
}


def sanitize_path_segment(value: object, fallback: str = "item") -> str:
    safe = _SAFE_SEGMENT_RE.sub("_", str(value)).strip("._-")
    return safe if safe and safe not in {".", ".."} else fallback


def ensure_under_base(base: str | Path, target: str | Path) -> Path:
    base_path = Path(base).resolve(strict=False)
    target_path = Path(target).resolve(strict=False)
    if not target_path.is_relative_to(base_path):
        raise StorageFailureError(
            "path escapes output base",
            details={"stage": "pathing", "reason": "path_traversal"},
        )
    return target_path


def _clean_prefix(prefix: str | None) -> str | None:
    if not prefix:
        return None
    parts = [
        sanitize_path_segment(part, "prefix")
        for part in prefix.replace("\\", "/").split("/")
        if part and part not in {".", ".."}
    ]
    return "/".join(parts) or None


def _utc_now_json() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _jsonable(record: Any) -> Any:
    if isinstance(record, BaseModel):
        return record.model_dump(mode="json")
    return record


def to_json_line(record: Any) -> str:
    return json.dumps(_jsonable(record), ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n"


def sanitize_failure_context(context: Mapping[str, Any] | None) -> dict[str, Any]:
    if not context:
        return {}
    safe: dict[str, Any] = {}
    for key, value in context.items():
        if key not in SAFE_FAILURE_CONTEXT_KEYS:
            continue
        try:
            json.dumps(value, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError):
            continue
        safe[key] = value
    return safe


def checkpoint_document(checkpoints: Mapping[str, Checkpoint]) -> dict[str, Any]:
    return {
        "schema_version": "dcinside.local_checkpoint.v1",
        "updated_at": _utc_now_json(),
        "checkpoints": {
            job_id: checkpoint.model_dump(mode="json")
            for job_id, checkpoint in checkpoints.items()
        },
    }


def parse_checkpoint_document(document: Mapping[str, Any]) -> dict[str, Checkpoint]:
    raw_checkpoints = document.get("checkpoints", {})
    if not isinstance(raw_checkpoints, Mapping):
        raise CheckpointFailureError(
            "invalid checkpoint document",
            details={"stage": "checkpoint", "reason": "invalid_document"},
        )
    return {
        str(job_id): Checkpoint.model_validate(raw)
        for job_id, raw in raw_checkpoints.items()
    }


@dataclass(frozen=True)
class OutputRunLayout:
    base_path: Path
    job_id: str
    run_id: str
    prefix: str | None = None

    @classmethod
    def create(
        cls,
        *,
        job_id: str,
        run_id: str,
        base_path: str | Path | None = None,
        prefix: str | None = None,
    ) -> "OutputRunLayout":
        return cls(
            base_path=Path(base_path or Path.cwd()).resolve(strict=False),
            job_id=sanitize_path_segment(job_id, "job"),
            run_id=sanitize_path_segment(run_id, "run"),
            prefix=_clean_prefix(prefix),
        )

    @classmethod
    def from_storage_config(cls, config: StorageConfig, *, job_id: str, run_id: str) -> "OutputRunLayout":
        prefix = config.s3.prefix if config.s3 else None
        return cls.create(job_id=job_id, run_id=run_id, base_path=config.base_output_path, prefix=prefix)

    @property
    def run_key(self) -> str:
        return self.join_key("outputs", self.job_id, self.run_id)

    @property
    def run_dir(self) -> Path:
        return self.path_for_key(self.run_key)

    @property
    def posts_key(self) -> str:
        return self.join_key(self.run_key, "posts.jsonl")

    @property
    def failures_key(self) -> str:
        return self.join_key(self.run_key, "failures.jsonl")

    @property
    def report_key(self) -> str:
        return self.join_key(self.run_key, "report.json")

    @property
    def posts_path(self) -> Path:
        return self.path_for_key(self.posts_key)

    @property
    def failures_path(self) -> Path:
        return self.path_for_key(self.failures_key)

    @property
    def report_path(self) -> Path:
        return self.path_for_key(self.report_key)

    @property
    def checkpoint_path(self) -> Path:
        return ensure_under_base(self.base_path, self.base_path / "Checkpoint.json")

    def media_key(self, gallery_id: object, post_no: object, media_type: object, filename: object) -> str:
        return self.join_key(
            self.run_key,
            "media",
            sanitize_path_segment(gallery_id, "unknown_gallery"),
            sanitize_path_segment(post_no, "unknown_post"),
            sanitize_path_segment(media_type, "other"),
            sanitize_path_segment(filename, "media.bin"),
        )

    def media_path(self, gallery_id: object, post_no: object, media_type: object, filename: object) -> Path:
        return self.path_for_key(self.media_key(gallery_id, post_no, media_type, filename))

    def prefixed_key(self, key: str) -> str:
        return f"{self.prefix}/{key}" if self.prefix else key

    def path_for_key(self, key: str) -> Path:
        return ensure_under_base(self.base_path, self.base_path.joinpath(*key.split("/")))

    @staticmethod
    def join_key(*parts: object) -> str:
        return "/".join(str(part).replace("\\", "/").strip("/") for part in parts if str(part).strip("/"))


class JsonlWriter:
    def __init__(self, path: str | Path, *, fsync: bool = False) -> None:
        self.path = Path(path)
        self.fsync = fsync

    def append(self, record: Any) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as file:
                file.write(to_json_line(record))
                file.flush()
                if self.fsync:
                    os.fsync(file.fileno())
        except (OSError, TypeError, ValueError) as exc:
            raise StorageFailureError(
                "jsonl write failed",
                details={"stage": "jsonl", "reason": exc.__class__.__name__},
            ) from exc


class AtomicJsonWriter:
    def __init__(self, *, fsync: bool = False) -> None:
        self.fsync = fsync

    def write(self, path: str | Path, record: Any) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, delete=False) as file:
                temp_name = file.name
                file.write(to_json_line(record).rstrip("\n"))
                file.flush()
                if self.fsync:
                    os.fsync(file.fileno())
            os.replace(temp_name, target)
        except (OSError, TypeError, ValueError) as exc:
            if temp_name:
                Path(temp_name).unlink(missing_ok=True)
            raise StorageFailureError(
                "atomic json write failed",
                details={"stage": "atomic_json", "reason": exc.__class__.__name__},
            ) from exc


class SafeFailureRecordBuilder:
    @classmethod
    def sanitize(cls, failure: FailureRecord) -> FailureRecord:
        data = failure.model_dump(mode="json")
        data["metadata"] = sanitize_failure_context(data.get("metadata", {}))
        return FailureRecord.model_validate(data)

    @classmethod
    def build(
        cls,
        *,
        reason: str,
        stage: str,
        retryable: bool = False,
        gallery_id: str | None = None,
        post_id: str | None = None,
        post_number: int | None = None,
        url: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> FailureRecord:
        return FailureRecord(
            gallery_id=gallery_id,
            post_id=post_id,
            post_number=post_number,
            url=url,
            reason=reason,
            stage=stage,
            retryable=retryable,
            metadata=sanitize_failure_context(context),
        )


class LocalOutputStore:
    def __init__(self, layout: OutputRunLayout, *, fsync_jsonl: bool = False) -> None:
        self.layout = layout
        self._post_writer = JsonlWriter(layout.posts_path, fsync=fsync_jsonl)
        self._failure_writer = JsonlWriter(layout.failures_path, fsync=fsync_jsonl)
        self._json_writer = AtomicJsonWriter()

    async def append_post(self, post: PostResult) -> StoredObjectRef:
        self._post_writer.append(post)
        return self._local_ref(self.layout.posts_path, self.layout.posts_key)

    async def write_failure(self, failure: FailureRecord) -> StoredObjectRef:
        self._failure_writer.append(SafeFailureRecordBuilder.sanitize(failure))
        return self._local_ref(self.layout.failures_path, self.layout.failures_key)

    async def finalize(self, report: JobReport) -> None:
        self._json_writer.write(self.layout.report_path, report)

    @staticmethod
    def _local_ref(path: Path, key: str) -> StoredObjectRef:
        return StoredObjectRef(uri=str(path), storage_type="local", object_key=key, local_path=str(path))


class LocalMediaStore:
    def __init__(self, layout: OutputRunLayout) -> None:
        self.layout = layout

    async def save_media(self, item: MediaItem, content: bytes) -> MediaItem:
        gallery_id = item.metadata.get("gallery_id", "unknown_gallery")
        post_no = item.metadata.get("post_number") or item.metadata.get("post_no") or item.metadata.get("post_id", "unknown_post")
        media_type = str(item.media_type)
        filename = self._filename(item)
        path = self.layout.media_path(gallery_id, post_no, media_type, filename)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        except OSError as exc:
            raise StorageFailureError(
                "media write failed",
                details={"stage": "media", "reason": exc.__class__.__name__},
            ) from exc
        return item.model_copy(update={"file_path": str(path)})

    async def save_metadata_only(self, item: MediaItem) -> MediaItem:
        return item

    @staticmethod
    def _filename(item: MediaItem) -> str:
        if item.media_id:
            base = item.media_id
        else:
            base = Path(unquote(urlparse(item.url).path)).name
        fallback = f"media{_MEDIA_EXTENSIONS.get(str(item.media_type), '.bin')}"
        safe = sanitize_path_segment(base, fallback)
        if "." not in safe:
            safe += _MEDIA_EXTENSIONS.get(str(item.media_type), ".bin")
        return safe


class LocalCheckpointStore:
    def __init__(self, base_path: str | Path | None = None) -> None:
        self.base_path = Path(base_path or Path.cwd()).resolve(strict=False)
        self.path = ensure_under_base(self.base_path, self.base_path / "Checkpoint.json")
        self._lock = threading.RLock()
        self._writer = AtomicJsonWriter()

    async def save(self, checkpoint: Checkpoint) -> None:
        with self._lock:
            checkpoints = self._load_all()
            checkpoints[checkpoint.job_id] = checkpoint
            self._writer.write(self.path, checkpoint_document(checkpoints))

    async def load(self, job_id: str) -> Checkpoint | None:
        with self._lock:
            return self._load_all().get(job_id)

    async def load_latest(self) -> Checkpoint | None:
        with self._lock:
            checkpoints = self._load_all()
        if not checkpoints:
            return None
        return max(checkpoints.values(), key=lambda checkpoint: checkpoint.updated_at)

    def _load_all(self) -> dict[str, Checkpoint]:
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as file:
                return parse_checkpoint_document(json.load(file))
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            raise CheckpointFailureError(
                "checkpoint load failed",
                details={"stage": "checkpoint", "reason": exc.__class__.__name__},
            ) from exc
