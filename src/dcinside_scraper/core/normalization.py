"""Common analytics/operations normalization helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from dcinside_scraper.models.base import MetadataModel
from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.job import JobConfig, PostCandidate, PostKey
from dcinside_scraper.models.report import JobReport, StoredObjectRef


class NormalizedRunReport(MetadataModel):
    schema_version: Literal["community.run_report.v1"] = "community.run_report.v1"
    scraper_id: str | None = Field(default=None, max_length=100)
    site_id: str = Field(min_length=1, max_length=50)
    job_id: str = Field(min_length=1, max_length=200)
    run_id: str | None = Field(default=None, max_length=200)
    status: str = Field(min_length=1, max_length=100)
    stop_reason: str | None = Field(default=None, max_length=100)
    started_at: datetime
    finished_at: datetime | None = None
    candidate_seen_count: int | None = Field(default=None, ge=0)
    candidate_collected_count: int | None = Field(default=None, ge=0)
    post_stored_count: int | None = Field(default=None, ge=0)
    failure_count: int = Field(default=0, ge=0)
    duplicate_skipped_count: int | None = Field(default=None, ge=0)
    range_filtered_count: int | None = Field(default=None, ge=0)
    output_ref_count: int = Field(default=0, ge=0)
    output_refs: list[dict[str, Any]] = Field(default_factory=list)
    native_report: dict[str, Any]


class NormalizedCheckpoint(MetadataModel):
    schema_version: Literal["community.checkpoint.v1"] = "community.checkpoint.v1"
    scraper_id: str | None = Field(default=None, max_length=100)
    site_id: str = Field(min_length=1, max_length=50)
    job_id: str = Field(min_length=1, max_length=200)
    status: str = Field(min_length=1, max_length=100)
    stop_reason: str | None = Field(default=None, max_length=100)
    updated_at: datetime
    collector_page: int | None = Field(default=None, ge=1)
    collector_board_id: str | None = Field(default=None, max_length=100)
    collector_cursor_value: str | None = Field(default=None, max_length=4096)
    last_completed_post_key: str | None = Field(default=None, max_length=500)
    processed_count: int | None = Field(default=None, ge=0)
    lease_until: datetime | None = None
    worker_id: str | None = Field(default=None, max_length=100)
    job_config: dict[str, Any]
    native_checkpoint: dict[str, Any]


class NormalizedCheckpointCompletedPost(MetadataModel):
    schema_version: Literal["community.checkpoint_completed_post.v1"] = "community.checkpoint_completed_post.v1"
    scraper_id: str | None = Field(default=None, max_length=100)
    site_id: str = Field(min_length=1, max_length=50)
    job_id: str = Field(min_length=1, max_length=200)
    post_key: str = Field(min_length=1, max_length=500)
    board_id: str | None = Field(default=None, max_length=100)
    post_id: str | None = Field(default=None, max_length=100)
    completed_at: datetime | None = None
    native_key: dict[str, Any]


class NormalizedCheckpointPendingQueue(MetadataModel):
    schema_version: Literal["community.checkpoint_pending_queue.v1"] = "community.checkpoint_pending_queue.v1"
    scraper_id: str | None = Field(default=None, max_length=100)
    site_id: str = Field(min_length=1, max_length=50)
    job_id: str = Field(min_length=1, max_length=200)
    queue_order: int = Field(ge=0)
    url: str = Field(min_length=1, max_length=4096)
    board_id: str | None = Field(default=None, max_length=100)
    post_id: str | None = Field(default=None, max_length=100)
    candidate_payload: dict[str, Any]


class NormalizedCheckpointBundle(MetadataModel):
    checkpoint: NormalizedCheckpoint
    completed_posts: list[NormalizedCheckpointCompletedPost] = Field(default_factory=list)
    pending_queue: list[NormalizedCheckpointPendingQueue] = Field(default_factory=list)


def normalize_job_report(
    report: JobReport,
    *,
    run_id: str | None = None,
    scraper_id: str | None = None,
) -> NormalizedRunReport:
    output_refs = [_dump(ref) for ref in report.output_refs]
    candidate_seen_count = report.success_count + report.failure_count + report.deduped_count + report.filtered_count
    return NormalizedRunReport(
        scraper_id=scraper_id,
        site_id="dcinside",
        job_id=report.job_id,
        run_id=run_id or _run_id_from_refs(report.job_id, report.output_refs),
        status=_value(report.status),
        stop_reason=None,
        started_at=report.started_at,
        finished_at=report.finished_at,
        candidate_seen_count=candidate_seen_count,
        candidate_collected_count=None,
        post_stored_count=report.success_count,
        failure_count=report.failure_count,
        duplicate_skipped_count=report.deduped_count,
        range_filtered_count=report.filtered_count,
        output_ref_count=len(output_refs),
        output_refs=output_refs,
        metadata=dict(report.metadata),
        native_report=report.model_dump(mode="json"),
    )


def normalize_checkpoint(checkpoint: Checkpoint, *, scraper_id: str | None = None) -> NormalizedCheckpointBundle:
    site_id = checkpoint.site_id
    job_config = checkpoint.job_config_snapshot
    completed = [
        _completed_row(key, job_id=checkpoint.job_id, site_id=site_id, scraper_id=scraper_id)
        for key in checkpoint.completed_keys
    ]
    pending = [
        _pending_row(candidate, index, job_id=checkpoint.job_id, site_id=site_id, scraper_id=scraper_id)
        for index, candidate in enumerate(checkpoint.remaining_queue or [])
    ]
    position = checkpoint.search_position
    common = NormalizedCheckpoint(
        scraper_id=scraper_id,
        site_id=site_id,
        job_id=checkpoint.job_id,
        status=_value(checkpoint.status),
        stop_reason=_value(checkpoint.reason),
        updated_at=checkpoint.updated_at,
        collector_page=position.page if position else None,
        collector_board_id=checkpoint.board_id or _source_board_id(job_config),
        collector_cursor_value=_cursor_value(position),
        last_completed_post_key=completed[-1].post_key if completed else _legacy_post_key(checkpoint),
        processed_count=checkpoint.scraping_processed_count,
        lease_until=checkpoint.lease_until,
        worker_id=checkpoint.worker_id,
        job_config=job_config.model_dump(mode="json"),
        native_checkpoint=checkpoint.model_dump(mode="json"),
        metadata=dict(checkpoint.metadata),
    )
    return NormalizedCheckpointBundle(checkpoint=common, completed_posts=completed, pending_queue=pending)


def _completed_row(
    key: PostKey,
    *,
    job_id: str,
    site_id: str,
    scraper_id: str | None,
) -> NormalizedCheckpointCompletedPost:
    return NormalizedCheckpointCompletedPost(
        scraper_id=scraper_id,
        site_id=site_id,
        job_id=job_id,
        post_key=_post_key(key.site_id, key.board_id, key.post_id),
        board_id=key.board_id,
        post_id=key.post_id,
        native_key=key.model_dump(mode="json"),
    )


def _pending_row(
    candidate: PostCandidate,
    index: int,
    *,
    job_id: str,
    site_id: str,
    scraper_id: str | None,
) -> NormalizedCheckpointPendingQueue:
    return NormalizedCheckpointPendingQueue(
        scraper_id=scraper_id,
        site_id=site_id,
        job_id=job_id,
        queue_order=index,
        url=candidate.url,
        board_id=candidate.gallery_id,
        post_id=candidate.post_id,
        candidate_payload=candidate.model_dump(mode="json"),
    )


def _source_board_id(config: JobConfig) -> str | None:
    return getattr(config.source, "gallery_id", None)


def _legacy_post_key(checkpoint: Checkpoint) -> str | None:
    if checkpoint.board_id and checkpoint.last_completed_post_id:
        return _post_key(checkpoint.site_id, checkpoint.board_id, checkpoint.last_completed_post_id)
    return None


def _cursor_value(position: Any | None) -> str | None:
    if position is None:
        return None
    value = position.cursor or position.search_pos
    return str(value) if value else None


def _run_id_from_refs(job_id: str, refs: list[StoredObjectRef]) -> str | None:
    for ref in refs:
        for value in (ref.object_key, ref.local_path, ref.uri):
            run_id = _run_id_from_path(job_id, value)
            if run_id:
                return run_id
    return None


def _run_id_from_path(job_id: str, value: str | None) -> str | None:
    parts = str(value or "").replace("\\", "/").split("/")
    for index, part in enumerate(parts[:-2]):
        if part == "outputs" and parts[index + 1] == job_id:
            return parts[index + 2]
    return None


def _post_key(site_id: str | None, board_id: str | None, post_id: str | None) -> str:
    return ":".join((site_id or "", board_id or "", post_id or ""))


def _dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return dict(value)


def _value(value: Any) -> str | None:
    if value is None:
        return None
    return getattr(value, "value", str(value))

