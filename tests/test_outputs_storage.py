from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from dcinside_scraper.core.errors import StorageFailureError
from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.comment import AuthorInfo
from dcinside_scraper.models.enums import JobReportStatus, JobType, MediaType
from dcinside_scraper.models.job import JobConfig
from dcinside_scraper.models.media import MediaItem
from dcinside_scraper.models.post import PostResult
from dcinside_scraper.models.report import FailureRecord, JobReport
from dcinside_scraper.outputs import (
    LocalCheckpointStore,
    LocalMediaStore,
    LocalOutputStore,
    OutputRunLayout,
    S3ObjectStore,
    ensure_under_base,
)


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


def test_local_output_store_writes_posts_failures_and_report(tmp_path: Path) -> None:
    layout = OutputRunLayout.create(base_path=tmp_path, job_id="job-1", run_id="run-1")
    store = LocalOutputStore(layout)
    failure = FailureRecord(
        gallery_id="dcbest",
        post_id="1",
        url="https://gall.dcinside.com/board/view/?id=dcbest&no=1",
        reason="network",
        stage="post",
        retryable=True,
        metadata={
            "proxy_host": "127.0.0.1:8080",
            "user_agent": "ua",
            "proxy_password": "secret",
            "cookie": "secret",
            "raw_html": "<html>",
        },
    )

    post_ref = asyncio.run(store.append_post(minimal_post()))
    failure_ref = asyncio.run(store.write_failure(failure))
    asyncio.run(store.finalize(JobReport(job_id="job-1", status=JobReportStatus.COMPLETED, success_count=1)))

    post_line = json.loads(layout.posts_path.read_text(encoding="utf-8").splitlines()[0])
    failure_line = json.loads(layout.failures_path.read_text(encoding="utf-8").splitlines()[0])
    report = json.loads(layout.report_path.read_text(encoding="utf-8"))

    assert post_line["title"] == "title"
    assert failure_line["metadata"] == {"proxy_host": "127.0.0.1:8080", "user_agent": "ua"}
    assert report["status"] == "completed"
    assert post_ref.storage_type == "local"
    assert failure_ref.object_key == "outputs/job-1/run-1/failures.jsonl"


def test_local_media_store_saves_bytes_and_metadata_only(tmp_path: Path) -> None:
    layout = OutputRunLayout.create(base_path=tmp_path, job_id="job-1", run_id="run-1")
    store = LocalMediaStore(layout)
    item = MediaItem(
        media_type=MediaType.IMAGE,
        url="https://example.test/image.jpg",
        metadata={"gallery_id": "dcbest", "post_number": 1},
    )

    saved = asyncio.run(store.save_media(item, b"image-bytes"))
    metadata_only = asyncio.run(store.save_metadata_only(item))

    assert saved.file_path is not None
    assert Path(saved.file_path).read_bytes() == b"image-bytes"
    assert metadata_only.file_path is None


def test_local_checkpoint_store_saves_loads_and_loads_latest(tmp_path: Path) -> None:
    store = LocalCheckpointStore(tmp_path)
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

    asyncio.run(store.save(older))
    asyncio.run(store.save(newer))

    assert asyncio.run(store.load("job-1")).job_id == "job-1"  # type: ignore[union-attr]
    assert asyncio.run(store.load_latest()).job_id == "job-2"  # type: ignore[union-attr]


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(StorageFailureError):
        ensure_under_base(tmp_path, tmp_path / ".." / "outside")


def test_s3_object_refs_use_prefixed_local_layout(tmp_path: Path) -> None:
    layout = OutputRunLayout.create(base_path=tmp_path, job_id="job-1", run_id="run-1", prefix="prod")
    store = S3ObjectStore(bucket="bucket", layout=layout, client=object())

    ref = store.object_ref(layout.posts_key)

    assert ref.uri == "s3://bucket/prod/outputs/job-1/run-1/posts.jsonl"
    assert ref.object_key == "prod/outputs/job-1/run-1/posts.jsonl"


def test_s3_put_bytes_uses_injected_client(tmp_path: Path) -> None:
    class FakeS3Client:
        def __init__(self) -> None:
            self.kwargs = None

        def put_object(self, **kwargs) -> None:
            self.kwargs = kwargs

    client = FakeS3Client()
    layout = OutputRunLayout.create(base_path=tmp_path, job_id="job-1", run_id="run-1", prefix="prod")
    store = S3ObjectStore(bucket="bucket", layout=layout, client=client)

    ref = asyncio.run(store.put_bytes(layout.report_key, b"{}", content_type="application/json"))

    assert ref.object_key == "prod/outputs/job-1/run-1/report.json"
    assert client.kwargs == {
        "Bucket": "bucket",
        "Key": "prod/outputs/job-1/run-1/report.json",
        "Body": b"{}",
        "ContentType": "application/json",
    }
