"""In-process JobRunner orchestration."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

import anyio

from dcinside_scraper.core.errors import (
    BlockedResponseError,
    CaptchaDetectedError,
    CheckpointFailureError,
    ScraperError,
    StorageFailureError,
    ValidationFailure,
)
from dcinside_scraper.core.ports import CheckpointStorePort, ClockPort, LoggerPort, OutputStorePort
from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.enums import CheckpointStatus, GalleryType, JobReportStatus, StopReason
from dcinside_scraper.models.job import (
    JobConfig,
    PostCandidate,
    PostKey,
    PostRequest,
    ResumeRequest,
    SearchPosition,
)
from dcinside_scraper.models.post import PostResult
from dcinside_scraper.models.report import FailureRecord, JobReport, StoredObjectRef

_SENTINEL = object()
_FORBIDDEN_EVENT_FIELDS = {
    "password",
    "proxy_password",
    "proxy_pw",
    "cookie",
    "cookies",
    "token",
    "headers",
    "raw_headers",
    "html",
    "raw_html",
    "body",
    "raw_body",
    "content",
    "env",
}
_SAFE_EVENT_FIELDS = {
    "job_id",
    "event",
    "stage",
    "gallery_id",
    "post_id",
    "post_number",
    "worker_id",
    "queued_count",
    "processed_count",
    "success_count",
    "failure_count",
    "deduped_count",
    "filtered_count",
    "stop_reason",
    "checkpoint_saved",
}


class CandidateCollectorPort(Protocol):
    def collect(self, config: JobConfig) -> Any:
        ...


class PostDetailPort(Protocol):
    async def fetch_post(self, request: PostRequest) -> PostResult:
        ...


class SystemClock:
    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)


class NullLogger:
    def debug(self, message: str, **fields: Any) -> None:
        return None

    def info(self, message: str, **fields: Any) -> None:
        return None

    def warning(self, message: str, **fields: Any) -> None:
        return None

    def error(self, message: str, **fields: Any) -> None:
        return None


def candidate_post_key(candidate: PostCandidate, *, site_id: str = "dcinside") -> PostKey:
    return PostKey(site_id=site_id, board_id=candidate.gallery_id, post_id=candidate.post_id)


def post_key_identity(key: PostKey) -> tuple[str, str, str]:
    return (key.site_id, key.board_id, key.post_id)


def should_skip_candidate(candidate: PostCandidate, completed_keys: Iterable[PostKey], *, site_id: str = "dcinside") -> bool:
    identity = post_key_identity(candidate_post_key(candidate, site_id=site_id))
    return identity in {post_key_identity(key) for key in completed_keys}


def stop_reason_for_error(error: BaseException) -> StopReason:
    if isinstance(error, CaptchaDetectedError):
        return StopReason.CAPTCHA
    return StopReason.ERROR


def report_status_for_checkpoint(status: CheckpointStatus) -> JobReportStatus:
    if status == CheckpointStatus.COMPLETED:
        return JobReportStatus.COMPLETED
    if status == CheckpointStatus.STOPPED:
        return JobReportStatus.STOPPED
    return JobReportStatus.RUNNING


class RunnerEventBuilder:
    @classmethod
    def build(cls, event: str, **fields: Any) -> dict[str, Any]:
        safe: dict[str, Any] = {"event": event}
        for key, value in fields.items():
            key_lower = key.lower()
            if key_lower in _FORBIDDEN_EVENT_FIELDS or key not in _SAFE_EVENT_FIELDS:
                continue
            if isinstance(value, (CheckpointStatus, JobReportStatus, StopReason, GalleryType)):
                value = value.value
            safe[key] = value
        return safe


class StopController:
    def __init__(self) -> None:
        self.requested = False
        self.reason: StopReason | None = None

    def request(self, reason: StopReason) -> None:
        if not self.requested:
            self.requested = True
            self.reason = reason


@dataclass
class JobRunContext:
    job_config: JobConfig
    queue: asyncio.Queue[Any]
    checkpoint: "CheckpointCoordinator"
    stop: StopController
    started_at: datetime
    success_count: int = 0
    failure_count: int = 0
    deduped_count: int = 0
    filtered_count: int = 0
    output_refs: list[StoredObjectRef] = field(default_factory=list)
    failures: list[FailureRecord] = field(default_factory=list)

    @property
    def processed_count(self) -> int:
        return self.success_count + self.failure_count


class CheckpointCoordinator:
    def __init__(
        self,
        *,
        config: JobConfig,
        store: CheckpointStorePort,
        clock: ClockPort,
        initial: Checkpoint | None = None,
        save_interval: int = 10,
    ) -> None:
        self.config = config
        self.store = store
        self.clock = clock
        self.save_interval = save_interval
        self.completed_keys = list(initial.completed_keys) if initial else []
        self._completed_identities = {post_key_identity(key) for key in self.completed_keys}
        self.search_position = initial.search_position if initial else None
        self.board_id = initial.board_id if initial else None
        self.last_completed_post_id = initial.last_completed_post_id if initial else None
        self.last_completed_url = initial.last_completed_url if initial else None
        self.processed_count = initial.scraping_processed_count if initial else 0
        self._since_save = 0
        self._lock = anyio.Lock()

    def is_completed(self, candidate: PostCandidate) -> bool:
        return post_key_identity(candidate_post_key(candidate, site_id=self.config.site_id)) in self._completed_identities

    async def record_success(self, candidate: PostCandidate, post: PostResult) -> None:
        await self._record_completed(candidate, board_id=post.gallery_id, post_id=post.post_id, url=candidate.url)

    async def record_failure(self, candidate: PostCandidate) -> None:
        await self._record_completed(candidate, board_id=candidate.gallery_id, post_id=candidate.post_id, url=candidate.url)

    async def _record_completed(self, candidate: PostCandidate, *, board_id: str, post_id: str, url: str) -> None:
        async with self._lock:
            key = candidate_post_key(candidate, site_id=self.config.site_id)
            identity = post_key_identity(key)
            if identity not in self._completed_identities:
                self._completed_identities.add(identity)
                self.completed_keys.append(key)
            self.board_id = board_id
            self.last_completed_post_id = post_id
            self.last_completed_url = url
            self.processed_count += 1
            self._since_save += 1
            if self._since_save >= self.save_interval:
                await self._save(CheckpointStatus.RUNNING, reason=None, remaining_queue=None)
                self._since_save = 0

    async def save_final(
        self,
        *,
        status: CheckpointStatus,
        reason: StopReason | None,
        remaining_queue: list[PostCandidate] | None = None,
    ) -> None:
        async with self._lock:
            await self._save(status, reason=reason, remaining_queue=remaining_queue)
            self._since_save = 0

    async def _save(
        self,
        status: CheckpointStatus,
        *,
        reason: StopReason | None,
        remaining_queue: list[PostCandidate] | None,
    ) -> None:
        if status == CheckpointStatus.STOPPED and reason is None:
            reason = StopReason.ERROR
        checkpoint = Checkpoint(
            job_id=self.config.job_id,
            site_id=self.config.site_id,
            board_id=self.board_id,
            last_completed_post_id=self.last_completed_post_id,
            last_completed_url=self.last_completed_url,
            scraping_processed_count=self.processed_count,
            status=status,
            reason=reason if status == CheckpointStatus.STOPPED else None,
            job_config_snapshot=self.config,
            search_position=self.search_position,
            completed_keys=list(self.completed_keys),
            remaining_queue=remaining_queue,
            updated_at=self.clock.now_utc(),
        )
        await self.store.save(checkpoint)


class JobRunner:
    def __init__(
        self,
        *,
        collector: CandidateCollectorPort,
        post_detail: PostDetailPort,
        output_store: OutputStorePort,
        checkpoint_store: CheckpointStorePort,
        logger: LoggerPort | None = None,
        clock: ClockPort | None = None,
    ) -> None:
        self.collector = collector
        self.post_detail = post_detail
        self.output_store = output_store
        self.checkpoint_store = checkpoint_store
        self.logger = logger or NullLogger()
        self.clock = clock or SystemClock()
        self._active_stop: StopController | None = None
        self._pending_manual_stop = False

    def request_stop(self) -> None:
        if self._active_stop is not None:
            self._active_stop.request(StopReason.MANUAL_STOP)
            return
        self._pending_manual_stop = True

    async def run(self, config: JobConfig) -> JobReport:
        return await self._run(config, initial_checkpoint=None)

    async def resume(self, request: ResumeRequest) -> JobReport:
        checkpoint = await self.checkpoint_store.load(request.job_id) if request.job_id else await self.checkpoint_store.load_latest()
        if checkpoint is None:
            raise ValidationFailure("checkpoint not found", details={"reason": "checkpoint_not_found"})
        return await self._run(checkpoint.job_config_snapshot, initial_checkpoint=checkpoint)

    async def _run(self, config: JobConfig, *, initial_checkpoint: Checkpoint | None) -> JobReport:
        queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=config.worker_config.queue_max_size or 0)
        stop = StopController()
        if self._pending_manual_stop:
            stop.request(StopReason.MANUAL_STOP)
            self._pending_manual_stop = False
        context = JobRunContext(
            job_config=config,
            queue=queue,
            checkpoint=CheckpointCoordinator(
                config=config,
                store=self.checkpoint_store,
                clock=self.clock,
                initial=initial_checkpoint,
            ),
            stop=stop,
            started_at=self.clock.now_utc(),
        )
        self._active_stop = stop
        self._log("info", "job_start", context)
        try:
            async with anyio.create_task_group() as task_group:
                task_group.start_soon(self._collector_task, context, initial_checkpoint.remaining_queue if initial_checkpoint else None)
                for worker_index in range(config.worker_config.post_worker_count):
                    task_group.start_soon(self._worker_task, context, f"worker-{worker_index + 1}")
        finally:
            self._active_stop = None

        status = CheckpointStatus.STOPPED if context.stop.requested else CheckpointStatus.COMPLETED
        reason = context.stop.reason if status == CheckpointStatus.STOPPED else None
        await context.checkpoint.save_final(
            status=status,
            reason=reason,
            remaining_queue=_snapshot_queue(context.queue) if status == CheckpointStatus.STOPPED else None,
        )
        report = self._build_report(context, status=status)
        await self.output_store.finalize(report)
        self._log("info", "job_end", context, stop_reason=reason.value if reason else None)
        return report

    async def _collector_task(self, context: JobRunContext, remaining_queue: list[PostCandidate] | None) -> None:
        try:
            if context.stop.requested:
                return
            if remaining_queue is not None:
                for candidate in remaining_queue:
                    if context.stop.requested:
                        break
                    await context.queue.put(candidate)
                return
            if _is_realtime(context.job_config):
                await self._collect_realtime(context)
            else:
                await self._collect_once(context)
        except (CaptchaDetectedError, BlockedResponseError) as exc:
            context.stop.request(stop_reason_for_error(exc))
            self._log("warning", "collector_stop", context, stop_reason=context.stop.reason.value if context.stop.reason else None)
        except ScraperError as exc:
            context.stop.request(StopReason.ERROR)
            self._log("error", "collector_error", context, stage=exc.details.get("stage", "collector"))
        except Exception:
            context.stop.request(StopReason.ERROR)
            self._log("error", "collector_error", context, stage="collector")
        finally:
            for _ in range(context.job_config.worker_config.post_worker_count):
                await context.queue.put(_SENTINEL)

    async def _collect_once(self, context: JobRunContext) -> None:
        result = await _maybe_await(self.collector.collect(context.job_config))
        context.deduped_count += int(getattr(getattr(result, "summary", None), "deduped_count", 0) or 0)
        context.filtered_count += int(getattr(getattr(result, "summary", None), "skipped_count", 0) or 0)
        for candidate in _result_candidates(result):
            if context.stop.requested:
                break
            await context.queue.put(candidate)
            self._log("debug", "candidate_queued", context, gallery_id=candidate.gallery_id, post_id=candidate.post_id)

    async def _collect_realtime(self, context: JobRunContext) -> None:
        while not context.stop.requested and not _realtime_done(context, self.clock.now_utc()):
            await self._collect_once(context)
            if context.stop.requested or _realtime_done(context, self.clock.now_utc()):
                break
            await anyio.sleep(_poll_interval(context.job_config))

    async def _worker_task(self, context: JobRunContext, worker_id: str) -> None:
        while True:
            item = await context.queue.get()
            try:
                if item is _SENTINEL:
                    return
                candidate = item
                if not isinstance(candidate, PostCandidate):
                    continue
                if context.stop.requested or context.checkpoint.is_completed(candidate):
                    context.deduped_count += 1
                    continue
                await self._process_candidate(context, candidate, worker_id)
            finally:
                context.queue.task_done()

    async def _process_candidate(self, context: JobRunContext, candidate: PostCandidate, worker_id: str) -> None:
        request = _post_request(candidate, context.job_config)
        try:
            post = await self.post_detail.fetch_post(request)
        except (CaptchaDetectedError, BlockedResponseError) as exc:
            context.stop.request(stop_reason_for_error(exc))
            self._log("warning", "worker_stop", context, worker_id=worker_id, stop_reason=context.stop.reason.value if context.stop.reason else None)
            return
        except (StorageFailureError, CheckpointFailureError) as exc:
            context.stop.request(stop_reason_for_error(exc))
            self._log("error", "worker_error", context, worker_id=worker_id, stage=exc.details.get("stage", "worker"))
            return
        except ScraperError as exc:
            await self._write_failure(context, candidate, exc.safe_message, "post", exc.retryable)
            return
        except Exception:
            context.stop.request(StopReason.ERROR)
            self._log("error", "worker_error", context, worker_id=worker_id, stage="post")
            return

        try:
            ref = await self.output_store.append_post(post)
            await context.checkpoint.record_success(candidate, post)
        except (StorageFailureError, CheckpointFailureError) as exc:
            context.stop.request(stop_reason_for_error(exc))
            self._log("error", "worker_storage_error", context, worker_id=worker_id, stage=exc.details.get("stage", "storage"))
            return
        context.output_refs.append(ref)
        context.success_count += 1
        self._log("debug", "worker_success", context, worker_id=worker_id, gallery_id=post.gallery_id, post_id=post.post_id)

    async def _write_failure(
        self,
        context: JobRunContext,
        candidate: PostCandidate,
        reason: str,
        stage: str,
        retryable: bool,
    ) -> None:
        failure = FailureRecord(
            gallery_id=candidate.gallery_id,
            post_id=candidate.post_id,
            post_number=candidate.post_number,
            url=candidate.url,
            reason=reason,
            stage=stage,
            retryable=retryable,
        )
        try:
            ref = await self.output_store.write_failure(failure)
            await context.checkpoint.record_failure(candidate)
        except (StorageFailureError, CheckpointFailureError) as exc:
            context.stop.request(stop_reason_for_error(exc))
            self._log("error", "worker_failure_storage_error", context, stage=exc.details.get("stage", "storage"))
            return
        context.failures.append(failure)
        context.output_refs.append(ref)
        context.failure_count += 1

    def _build_report(self, context: JobRunContext, *, status: CheckpointStatus) -> JobReport:
        return JobReport(
            job_id=context.job_config.job_id,
            status=report_status_for_checkpoint(status),
            success_count=context.success_count,
            failure_count=context.failure_count,
            deduped_count=context.deduped_count,
            filtered_count=context.filtered_count,
            started_at=context.started_at,
            finished_at=self.clock.now_utc(),
            failures=list(context.failures),
            output_refs=list(context.output_refs),
        )

    def _log(self, level: str, event: str, context: JobRunContext, **fields: Any) -> None:
        safe = RunnerEventBuilder.build(
            event,
            job_id=context.job_config.job_id,
            processed_count=context.processed_count,
            success_count=context.success_count,
            failure_count=context.failure_count,
            deduped_count=context.deduped_count,
            filtered_count=context.filtered_count,
            **fields,
        )
        getattr(self.logger, level)(event, **safe)


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def _result_candidates(result: Any) -> list[PostCandidate]:
    if isinstance(result, list):
        return [candidate for candidate in result if isinstance(candidate, PostCandidate)]
    return list(getattr(result, "candidates", []) or [])


def _post_request(candidate: PostCandidate, config: JobConfig) -> PostRequest:
    gallery_type = candidate.metadata.get("gallery_type")
    try:
        parsed_gallery_type = GalleryType(gallery_type) if gallery_type else None
    except ValueError:
        parsed_gallery_type = None
    return PostRequest(
        url=candidate.url,
        gallery_type=parsed_gallery_type,
        gallery_id=candidate.gallery_id,
        post_id=candidate.post_id,
        post_number=candidate.post_number,
        scrape_options=config.scrape_options,
    )


def _is_realtime(config: JobConfig) -> bool:
    return config.source.type in {"realtime_keyword", "realtime_all"}


def _poll_interval(config: JobConfig) -> float:
    return float(getattr(config.source, "poll_interval_seconds", 30.0))


def _realtime_done(context: JobRunContext, now: datetime) -> bool:
    termination = getattr(context.job_config.source, "termination", None)
    if termination is None:
        return False
    if termination.end_at is not None:
        return now >= termination.end_at
    if termination.duration_seconds is not None:
        return now >= context.started_at + timedelta(seconds=termination.duration_seconds)
    return False


def _snapshot_queue(queue: asyncio.Queue[Any]) -> list[PostCandidate] | None:
    items = [item for item in list(getattr(queue, "_queue", [])) if isinstance(item, PostCandidate)]
    return items or None
