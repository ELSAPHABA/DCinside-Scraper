from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path

import anyio
import pytest

from dcinside_scraper.core.errors import CheckpointFailureError
from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.comment import AuthorInfo
from dcinside_scraper.models.enums import JobReportStatus, JobType, MediaType
from dcinside_scraper.models.job import JobConfig
from dcinside_scraper.models.media import MediaItem
from dcinside_scraper.models.post import PostResult
from dcinside_scraper.models.report import FailureRecord, JobReport
from dcinside_scraper.outputs import OutputRunLayout, S3ObjectStore, S3OutputStore
from dcinside_scraper.outputs.postgres_checkpoint import PostgresCheckpointStore


def minimal_job(job_id: str = "job-1") -> JobConfig:
    return JobConfig(
        job_id=job_id,
        job_type=JobType.DIRECT_POST,
        source={"type": "direct_post", "urls": ["https://gall.dcinside.com/board/view/?id=dcbest&no=1"]},
    )


def minimal_post() -> PostResult:
    return PostResult(
        gallery_id="dcbest",
        post_id="1",
        post_number=1,
        title="title",
        author=AuthorInfo(name="writer"),
    )


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_object(self, **kwargs) -> None:
        self.objects[kwargs["Key"]] = kwargs["Body"]

    def get_object(self, **kwargs):
        return {"Body": BytesIO(self.objects[kwargs["Key"]])}


def test_s3_output_store_uploads_jsonl_report_and_media(tmp_path: Path) -> None:
    client = FakeS3Client()
    layout = OutputRunLayout.create(base_path=tmp_path, job_id="job-1", run_id="run-1", prefix="prod")
    object_store = S3ObjectStore(bucket="bucket", layout=layout, client=client)
    store = S3OutputStore(layout, object_store)

    post_ref = anyio.run(store.append_post, minimal_post())
    failure_ref = anyio.run(
        store.write_failure,
        FailureRecord(
            gallery_id="dcbest",
            post_id="1",
            reason="failed",
            stage="post",
            metadata={"proxy_password": "secret", "proxy_host": "proxy.local"},
        ),
    )
    saved = anyio.run(
        store.save_media,
        MediaItem(media_type=MediaType.IMAGE, url="https://example.test/a.jpg", metadata={"gallery_id": "dcbest", "post_number": 1}),
        b"image",
    )
    anyio.run(store.finalize, JobReport(job_id="job-1", status=JobReportStatus.COMPLETED, success_count=1))

    assert post_ref.object_key == "prod/outputs/job-1/run-1/posts.jsonl"
    assert failure_ref.object_key == "prod/outputs/job-1/run-1/failures.jsonl"
    assert saved.object_key == "prod/outputs/job-1/run-1/media/dcbest/1/image/a.jpg"
    assert anyio.run(store.read_failures, failure_ref.uri)[0].post_id == "1"
    assert json.loads(client.objects["prod/outputs/job-1/run-1/posts.jsonl"].splitlines()[0])["title"] == "title"
    assert json.loads(client.objects["prod/outputs/job-1/run-1/failures.jsonl"].splitlines()[0])["metadata"] == {"proxy_host": "proxy.local"}
    assert json.loads(client.objects["prod/outputs/job-1/run-1/report.json"])["status"] == "completed"
    assert not store.spool.base_path.exists()


class FakeCursor:
    def __init__(self, store: dict[str, tuple[datetime, dict]]) -> None:
        self.store = store
        self.row = None

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, sql: str, params=()) -> None:
        normalized = " ".join(sql.lower().split())
        if normalized.startswith("create table"):
            return
        if normalized.startswith("insert into"):
            job_id, updated_at, document = params
            self.store[job_id] = (updated_at, json.loads(document))
            return
        if "where job_id" in normalized:
            item = self.store.get(params[0])
            self.row = (item[1],) if item else None
            return
        if "order by updated_at" in normalized:
            self.row = (max(self.store.values(), key=lambda item: item[0])[1],) if self.store else None

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, store: dict[str, tuple[datetime, dict]]) -> None:
        self.store = store

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return FakeCursor(self.store)


def test_postgres_checkpoint_store_saves_loads_and_loads_latest() -> None:
    rows: dict[str, tuple[datetime, dict]] = {}
    store = PostgresCheckpointStore("postgresql://example", connection_factory=lambda dsn: FakeConnection(rows))
    older = Checkpoint(
        job_id="job-1",
        job_config_snapshot=minimal_job("job-1"),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    newer = Checkpoint(
        job_id="job-2",
        job_config_snapshot=minimal_job("job-2"),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    anyio.run(store.save, older)
    anyio.run(store.save, newer)

    assert anyio.run(store.load, "job-1").job_id == "job-1"  # type: ignore[union-attr]
    assert anyio.run(store.load_latest).job_id == "job-2"  # type: ignore[union-attr]


def test_postgres_checkpoint_store_wraps_invalid_loaded_json() -> None:
    rows = {"job-1": (datetime(2026, 1, 1, tzinfo=timezone.utc), {"bad": "shape"})}
    store = PostgresCheckpointStore("postgresql://example", connection_factory=lambda dsn: FakeConnection(rows))

    with pytest.raises(CheckpointFailureError):
        anyio.run(store.load, "job-1")
