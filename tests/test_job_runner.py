from __future__ import annotations

from datetime import datetime, timezone

import anyio
import pytest

from dcinside_scraper.core.errors import BlockedResponseError, ParseFailureError, StorageFailureError
from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.comment import AuthorInfo
from dcinside_scraper.models.enums import CheckpointStatus, JobReportStatus, JobType, StopReason
from dcinside_scraper.models.job import JobConfig, PostCandidate, ResumeRequest, WorkerConfig
from dcinside_scraper.models.post import PostResult
from dcinside_scraper.models.report import FailureRecord, JobReport, StoredObjectRef
from dcinside_scraper.runner import JobRunner


def minimal_job(*, job_id: str = "job-1", worker_count: int = 1) -> JobConfig:
    return JobConfig(
        job_id=job_id,
        job_type=JobType.DIRECT_POST,
        source={"type": "direct_post", "urls": ["https://gall.dcinside.com/board/view/?id=dcbest&no=1"]},
        worker_config=WorkerConfig(post_worker_count=worker_count),
    )


def candidate(number: int) -> PostCandidate:
    return PostCandidate(
        url=f"https://gall.dcinside.com/board/view/?id=dcbest&no={number}",
        gallery_id="dcbest",
        post_id=str(number),
        post_number=number,
    )


class FakeClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def now_utc(self) -> datetime:
        return self.now


class FakeCollector:
    def __init__(self, candidates: list[PostCandidate]) -> None:
        self.candidates = candidates
        self.calls = 0

    async def collect(self, config: JobConfig):
        self.calls += 1
        return list(self.candidates)


class FakePostDetail:
    def __init__(self, failures: dict[str, Exception] | None = None) -> None:
        self.failures = failures or {}
        self.requests = []

    async def fetch_post(self, request):
        self.requests.append(request)
        error = self.failures.get(str(request.post_id))
        if error is not None:
            raise error
        return PostResult(
            gallery_id=request.gallery_id or "dcbest",
            post_id=request.post_id or "1",
            post_number=request.post_number,
            title="title",
            author=AuthorInfo(name="writer"),
        )


class FakeOutputStore:
    def __init__(self, *, fail_append: bool = False) -> None:
        self.fail_append = fail_append
        self.posts = []
        self.failures = []
        self.reports = []

    async def append_post(self, post: PostResult) -> StoredObjectRef:
        if self.fail_append:
            raise StorageFailureError("write failed", details={"stage": "posts"})
        self.posts.append(post)
        return StoredObjectRef(uri="memory://posts", storage_type="memory")

    async def write_failure(self, failure: FailureRecord) -> StoredObjectRef:
        self.failures.append(failure)
        return StoredObjectRef(uri="memory://failures", storage_type="memory")

    async def finalize(self, report: JobReport) -> None:
        self.reports.append(report)


class FakeCheckpointStore:
    def __init__(self, checkpoint: Checkpoint | None = None) -> None:
        self.checkpoint = checkpoint
        self.saved = []

    async def save(self, checkpoint: Checkpoint) -> None:
        self.saved.append(checkpoint)
        self.checkpoint = checkpoint

    async def load(self, job_id: str) -> Checkpoint | None:
        if self.checkpoint and self.checkpoint.job_id == job_id:
            return self.checkpoint
        return None

    async def load_latest(self) -> Checkpoint | None:
        return self.checkpoint


def make_runner(
    *,
    collector: FakeCollector | None = None,
    detail: FakePostDetail | None = None,
    output: FakeOutputStore | None = None,
    checkpoint: FakeCheckpointStore | None = None,
) -> tuple[JobRunner, FakeCollector, FakePostDetail, FakeOutputStore, FakeCheckpointStore]:
    collector = collector or FakeCollector([candidate(1)])
    detail = detail or FakePostDetail()
    output = output or FakeOutputStore()
    checkpoint = checkpoint or FakeCheckpointStore()
    runner = JobRunner(
        collector=collector,
        post_detail=detail,
        output_store=output,
        checkpoint_store=checkpoint,
        clock=FakeClock(),
    )
    return runner, collector, detail, output, checkpoint


def test_job_runner_completes_fake_job() -> None:
    runner, _, _, output, checkpoint = make_runner(collector=FakeCollector([candidate(1), candidate(2)]))

    report = anyio.run(runner.run, minimal_job(worker_count=2))

    assert report.status == JobReportStatus.COMPLETED
    assert report.success_count == 2
    assert len(output.posts) == 2
    assert checkpoint.saved[-1].status == CheckpointStatus.COMPLETED
    assert checkpoint.saved[-1].scraping_processed_count == 2


def test_completed_key_is_skipped_on_resume() -> None:
    job = minimal_job()
    completed = candidate(1)
    checkpoint = Checkpoint(
        job_id=job.job_id,
        job_config_snapshot=job,
        completed_keys=[{"board_id": completed.gallery_id, "post_id": completed.post_id}],
    )
    runner, _, detail, output, _ = make_runner(
        collector=FakeCollector([completed, candidate(2)]),
        checkpoint=FakeCheckpointStore(checkpoint),
    )

    report = anyio.run(runner.resume, ResumeRequest(job_id=job.job_id))

    assert report.success_count == 1
    assert report.deduped_count == 1
    assert [request.post_id for request in detail.requests] == ["2"]
    assert [post.post_id for post in output.posts] == ["2"]


def test_checkpoint_saves_every_ten_completed_outcomes() -> None:
    runner, _, _, _, checkpoint = make_runner(collector=FakeCollector([candidate(number) for number in range(1, 11)]))

    report = anyio.run(runner.run, minimal_job())

    assert report.success_count == 10
    assert [saved.status for saved in checkpoint.saved] == [CheckpointStatus.RUNNING, CheckpointStatus.COMPLETED]


def test_storage_failure_stops_without_advancing_completed_key() -> None:
    runner, _, _, _, checkpoint = make_runner(output=FakeOutputStore(fail_append=True))

    report = anyio.run(runner.run, minimal_job())

    assert report.status == JobReportStatus.STOPPED
    assert report.success_count == 0
    assert checkpoint.saved[-1].status == CheckpointStatus.STOPPED
    assert checkpoint.saved[-1].reason == StopReason.ERROR
    assert checkpoint.saved[-1].completed_keys == []


def test_recoverable_post_failure_is_written_and_job_continues() -> None:
    runner, _, _, output, checkpoint = make_runner(
        collector=FakeCollector([candidate(1), candidate(2)]),
        detail=FakePostDetail({"1": ParseFailureError("parse failed")}),
    )

    report = anyio.run(runner.run, minimal_job())

    assert report.status == JobReportStatus.COMPLETED
    assert report.success_count == 1
    assert report.failure_count == 1
    assert output.failures[0].post_id == "1"
    assert len(checkpoint.saved[-1].completed_keys) == 2


def test_blocked_response_stops_new_work() -> None:
    runner, _, _, output, checkpoint = make_runner(
        collector=FakeCollector([candidate(1)]),
        detail=FakePostDetail({"1": BlockedResponseError("blocked")}),
    )

    report = anyio.run(runner.run, minimal_job())

    assert report.status == JobReportStatus.STOPPED
    assert output.posts == []
    assert checkpoint.saved[-1].reason == StopReason.ERROR


def test_manual_stop_before_run_saves_stopped_checkpoint() -> None:
    runner, collector, _, _, checkpoint = make_runner()
    runner.request_stop()

    report = anyio.run(runner.run, minimal_job())

    assert report.status == JobReportStatus.STOPPED
    assert report.success_count == 0
    assert collector.calls == 0
    assert checkpoint.saved[-1].reason == StopReason.MANUAL_STOP
