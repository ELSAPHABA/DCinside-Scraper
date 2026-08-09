"""Retry parser-stage post failures through the existing direct-post runner."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse
from urllib.request import url2pathname

from pydantic import ValidationError

from dcinside_scraper.core.errors import ScraperError, StorageFailureError, ValidationFailure
from dcinside_scraper.models.enums import JobReportStatus, JobType
from dcinside_scraper.models.job import DirectPostSource, JobConfig, ScrapeOptions, StorageConfig, WorkerConfig
from dcinside_scraper.models.report import FailureRecord, JobReport
from dcinside_scraper.search.collection import parse_post_url

RetryKey = tuple[str, str, str]

_DEFAULT_SITE_ID = "dcinside"
_RETRY_REASON_FRAGMENTS = (
    "post title missing",
    "post author missing",
    "post identity missing",
    "metadata parse",
    "metadata failure",
    "content parse",
    "content failure",
    "comment parse",
)
_EXCLUDED_REASON_FRAGMENTS = (
    "captcha",
    "block",
    "network",
    "storage",
    "checkpoint",
    "manual",
    "cancel",
)


class FailureInputReader(Protocol):
    def iter_lines(self, ref: str) -> Iterable[str]:
        ...


class LocalFailureInputReader:
    def iter_lines(self, ref: str) -> Iterable[str]:
        path = _local_path(ref)
        if not path.is_file():
            raise ValidationFailure("input file not found", details={"reason": "file_not_found", "input_ref": _safe_ref(ref)})
        try:
            with path.open("r", encoding="utf-8") as file:
                yield from file
        except OSError as exc:
            raise StorageFailureError("input file read failed", details={"stage": "retry_input", "reason": exc.__class__.__name__}) from exc


class S3FailureInputReader:
    def __init__(
        self,
        client: Any | None = None,
        *,
        endpoint_url: str | None = None,
        region_name: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        force_path_style: bool = False,
    ) -> None:
        self._client = client
        self.endpoint_url = endpoint_url
        self.region_name = region_name
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.force_path_style = force_path_style

    def iter_lines(self, ref: str) -> Iterable[str]:
        parsed = urlparse(ref)
        if parsed.scheme != "s3" or not parsed.netloc or not parsed.path.strip("/"):
            raise ValidationFailure("invalid s3 input ref", details={"reason": "invalid_s3_ref"})
        try:
            response = self._get_client().get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))
            body = response["Body"]
            for raw_line in body.iter_lines():
                yield raw_line.decode("utf-8") + "\n"
        except Exception as exc:
            raise StorageFailureError("s3 input read failed", details={"stage": "retry_input", "reason": exc.__class__.__name__}) from exc

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            import boto3
        except ImportError as exc:
            raise StorageFailureError(
                "s3 extra is required",
                details={"stage": "retry_input", "reason": "missing_s3_dependency"},
            ) from exc
        kwargs: dict[str, Any] = {}
        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url
        if self.region_name:
            kwargs["region_name"] = self.region_name
        if self.access_key_id:
            kwargs["aws_access_key_id"] = self.access_key_id
        if self.secret_access_key:
            kwargs["aws_secret_access_key"] = self.secret_access_key
        if self.force_path_style:
            try:
                from botocore.config import Config
            except ImportError as exc:
                raise StorageFailureError(
                    "s3 extra is required",
                    details={"stage": "retry_input", "reason": "missing_s3_dependency"},
                ) from exc
            kwargs["config"] = Config(s3={"addressing_style": "path"})
        self._client = boto3.client("s3", **kwargs)
        return self._client


class CompositeFailureInputReader:
    def __init__(self, *, local: FailureInputReader | None = None, s3: FailureInputReader | None = None) -> None:
        self.local = local or LocalFailureInputReader()
        self.s3 = s3 or S3FailureInputReader()

    def iter_lines(self, ref: str) -> Iterable[str]:
        return self.s3.iter_lines(ref) if str(ref).startswith("s3://") else self.local.iter_lines(ref)


@dataclass(frozen=True)
class RetryCandidate:
    key: RetryKey
    url: str
    gallery_id: str
    post_id: str
    post_number: int | None = None
    last_failure_reason: str = ""
    source_ref: str = ""


@dataclass(frozen=True)
class ExistingPostIndex:
    keys: frozenset[RetryKey] = field(default_factory=frozenset)
    invalid_record_count: int = 0
    refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrySelectionSummary:
    retry_source_failure_refs: tuple[str, ...] = ()
    initial_failure_count: int = 0
    invalid_failure_record_count: int = 0
    ineligible_failure_count: int = 0
    selected_retry_count: int = 0
    deduped_failure_count: int = 0
    skipped_existing_count: int = 0
    existing_post_invalid_record_count: int = 0

    def to_metadata(self) -> dict[str, Any]:
        return {
            "retry_source_failure_refs": list(self.retry_source_failure_refs),
            "initial_failure_count": self.initial_failure_count,
            "invalid_failure_record_count": self.invalid_failure_record_count,
            "ineligible_failure_count": self.ineligible_failure_count,
            "selected_retry_count": self.selected_retry_count,
            "deduped_failure_count": self.deduped_failure_count,
            "skipped_existing_count": self.skipped_existing_count,
            "existing_post_invalid_record_count": self.existing_post_invalid_record_count,
        }


@dataclass(frozen=True)
class ParserFailureRetryRequest:
    failure_refs: tuple[str, ...]
    existing_post_refs: tuple[str, ...] = ()
    existing_post_roots: tuple[str, ...] = ()
    job_id: str | None = None
    scrape_options: ScrapeOptions = field(default_factory=ScrapeOptions)
    worker_config: WorkerConfig = field(default_factory=WorkerConfig)
    storage_config: StorageConfig = field(default_factory=StorageConfig)


def select_parser_failure_retries(
    failure_lines_by_ref: Mapping[str, Iterable[str]],
    *,
    existing_keys: Iterable[RetryKey] = (),
    existing_post_invalid_record_count: int = 0,
) -> tuple[list[RetryCandidate], RetrySelectionSummary]:
    existing = set(existing_keys)
    candidates: dict[RetryKey, RetryCandidate] = {}
    initial_count = 0
    invalid_count = 0
    ineligible_count = 0
    deduped_count = 0

    for source_ref, lines in failure_lines_by_ref.items():
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            initial_count += 1
            try:
                raw = json.loads(line)
                failure = FailureRecord.model_validate(raw)
                candidate = _candidate_from_failure(failure, raw, source_ref=source_ref)
            except (json.JSONDecodeError, ValidationError, ValidationFailure, ScraperError, ValueError, TypeError):
                invalid_count += 1
                continue
            if not _is_retryable_parser_failure(failure):
                ineligible_count += 1
                continue
            if candidate.key in candidates:
                deduped_count += 1
                del candidates[candidate.key]
            candidates[candidate.key] = candidate

    selected: list[RetryCandidate] = []
    skipped_existing = 0
    for candidate in candidates.values():
        if candidate.key in existing:
            skipped_existing += 1
            continue
        selected.append(candidate)

    summary = RetrySelectionSummary(
        retry_source_failure_refs=tuple(failure_lines_by_ref.keys()),
        initial_failure_count=initial_count,
        invalid_failure_record_count=invalid_count,
        ineligible_failure_count=ineligible_count,
        selected_retry_count=len(selected),
        deduped_failure_count=deduped_count,
        skipped_existing_count=skipped_existing,
        existing_post_invalid_record_count=existing_post_invalid_record_count,
    )
    return selected, summary


class ParserFailureRetryService:
    def __init__(self, reader: FailureInputReader | None = None) -> None:
        self.reader = reader or CompositeFailureInputReader()

    async def retry(
        self,
        request: ParserFailureRetryRequest,
        *,
        execute_job: Callable[[JobConfig], Awaitable[JobReport]],
    ) -> JobReport:
        _validate_request(request)
        existing = self.build_existing_post_index(request.existing_post_refs, request.existing_post_roots)
        failure_lines = {ref: self.reader.iter_lines(ref) for ref in request.failure_refs}
        candidates, summary = select_parser_failure_retries(
            failure_lines,
            existing_keys=existing.keys,
            existing_post_invalid_record_count=existing.invalid_record_count,
        )
        if not candidates:
            return _empty_report(request, summary)
        config = _job_config_for_retry(request, candidates, summary)
        report = await execute_job(config)
        return _with_final_retry_metadata(report, summary)

    def build_existing_post_index(self, refs: Iterable[str] = (), roots: Iterable[str] = ()) -> ExistingPostIndex:
        resolved_refs = [*refs, *_discover_local_posts(roots)]
        keys: set[RetryKey] = set()
        invalid_count = 0
        for ref in resolved_refs:
            for line in self.reader.iter_lines(ref):
                if not line.strip():
                    continue
                try:
                    raw = json.loads(line)
                    key = _post_key_from_raw(raw)
                except (json.JSONDecodeError, TypeError, ValueError):
                    invalid_count += 1
                    continue
                if key is None:
                    invalid_count += 1
                    continue
                keys.add(key)
        return ExistingPostIndex(frozenset(keys), invalid_count, tuple(resolved_refs))


def _validate_request(request: ParserFailureRetryRequest) -> None:
    if not request.failure_refs:
        raise ValidationFailure("at least one failure input is required", details={"reason": "missing_failure_input"})


def _candidate_from_failure(failure: FailureRecord, raw: Mapping[str, Any], *, source_ref: str) -> RetryCandidate:
    parsed = None
    if failure.url:
        try:
            parsed = parse_post_url(failure.url)
        except ScraperError:
            parsed = None
    site_id = str(raw.get("site_id") or raw.get("metadata", {}).get("site_id") or _DEFAULT_SITE_ID)
    gallery_id = failure.gallery_id or (parsed.gallery_id if parsed else None)
    post_id = failure.post_id or (parsed.post_id if parsed else None) or (str(failure.post_number) if failure.post_number is not None else None)
    post_number = failure.post_number if failure.post_number is not None else (parsed.post_number if parsed else _int_or_none(post_id))
    if not gallery_id or not post_id:
        raise ValidationFailure("failure record lacks post identity", details={"reason": "missing_post_identity"})
    url = failure.url if parsed else _canonical_post_url(gallery_id, post_id)
    return RetryCandidate(
        key=(site_id, gallery_id, post_id),
        url=url,
        gallery_id=gallery_id,
        post_id=post_id,
        post_number=post_number,
        last_failure_reason=failure.reason,
        source_ref=source_ref,
    )


def _is_retryable_parser_failure(failure: FailureRecord) -> bool:
    if failure.stage != "post":
        return False
    reason = failure.reason.lower()
    if any(fragment in reason for fragment in _EXCLUDED_REASON_FRAGMENTS):
        return False
    return any(fragment in reason for fragment in _RETRY_REASON_FRAGMENTS)


def _post_key_from_raw(raw: Mapping[str, Any]) -> RetryKey | None:
    site_id = str(raw.get("site_id") or raw.get("metadata", {}).get("site_id") or _DEFAULT_SITE_ID)
    gallery_id = raw.get("gallery_id")
    post_id = raw.get("post_id") or (str(raw.get("post_number")) if raw.get("post_number") is not None else None)
    if not gallery_id or not post_id:
        return None
    return (site_id, str(gallery_id), str(post_id))


def _job_config_for_retry(
    request: ParserFailureRetryRequest,
    candidates: list[RetryCandidate],
    summary: RetrySelectionSummary,
) -> JobConfig:
    return JobConfig(
        job_id=request.job_id or "retry-parser-failures",
        job_type=JobType.DIRECT_POST,
        source=DirectPostSource(urls=[candidate.url for candidate in candidates]),
        scrape_options=request.scrape_options,
        worker_config=request.worker_config,
        storage_config=request.storage_config,
        metadata={"parser_failure_retry": summary.to_metadata()},
    )


def _empty_report(request: ParserFailureRetryRequest, summary: RetrySelectionSummary) -> JobReport:
    metadata = summary.to_metadata()
    metadata["success_count"] = 0
    metadata["remaining_failure_count"] = 0
    return JobReport(
        job_id=request.job_id or "retry-parser-failures",
        status=JobReportStatus.COMPLETED,
        metadata={"parser_failure_retry": metadata},
    )


def _with_final_retry_metadata(report: JobReport, summary: RetrySelectionSummary) -> JobReport:
    metadata = dict(report.metadata)
    retry_metadata = summary.to_metadata()
    retry_metadata["success_count"] = report.success_count
    retry_metadata["remaining_failure_count"] = report.failure_count
    metadata["parser_failure_retry"] = retry_metadata
    return report.model_copy(update={"metadata": metadata})


def _discover_local_posts(roots: Iterable[str]) -> list[str]:
    refs: list[str] = []
    for root in roots:
        root_path = _local_path(root)
        if not root_path.is_dir():
            raise ValidationFailure("existing posts root not found", details={"reason": "root_not_found", "input_ref": _safe_ref(root)})
        refs.extend(str(path) for path in sorted(root_path.rglob("posts.jsonl")))
    return refs


def _local_path(ref: str) -> Path:
    if _is_windows_drive_path(ref):
        return Path(ref).resolve(strict=False)
    parsed = urlparse(str(ref))
    if parsed.scheme == "file":
        return Path(url2pathname(parsed.path)).resolve(strict=False)
    if parsed.scheme and parsed.scheme != "file":
        raise ValidationFailure("unsupported input ref", details={"reason": "unsupported_input_ref"})
    return Path(ref).resolve(strict=False)


def _canonical_post_url(gallery_id: str, post_id: str) -> str:
    return f"https://gall.dcinside.com/board/view/?id={gallery_id}&no={post_id}"


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_ref(ref: str) -> str:
    parsed = urlparse(str(ref))
    if parsed.scheme == "s3":
        return f"s3://{parsed.netloc}/{parsed.path.lstrip('/')}"
    return str(ref)


def _is_windows_drive_path(ref: str) -> bool:
    return len(ref) >= 3 and ref[1] == ":" and ref[0].isalpha() and ref[2] in {"\\", "/"}
