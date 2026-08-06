"""Job report and failure contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from dcinside_scraper.models.base import MetadataModel
from dcinside_scraper.models.enums import JobReportStatus
from dcinside_scraper.models.job import utc_now


class StoredObjectRef(MetadataModel):
    uri: str = Field(min_length=1, max_length=4096)
    storage_type: str = Field(min_length=1, max_length=100)
    object_key: str | None = None
    local_path: str | None = None


class FailureRecord(MetadataModel):
    gallery_id: str | None = Field(default=None, max_length=100)
    post_id: str | None = Field(default=None, max_length=100)
    post_number: int | None = Field(default=None, ge=0)
    url: str | None = Field(default=None, max_length=4096)
    reason: str = Field(min_length=1, max_length=1000)
    stage: str = Field(min_length=1, max_length=100)
    retryable: bool = False


class JobReport(MetadataModel):
    schema_version: Literal["dcinside.job_report.v1"] = "dcinside.job_report.v1"
    job_id: str = Field(min_length=1, max_length=200)
    status: JobReportStatus
    success_count: int = Field(default=0, ge=0)
    failure_count: int = Field(default=0, ge=0)
    deduped_count: int = Field(default=0, ge=0)
    filtered_count: int = Field(default=0, ge=0)
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    failures: list[FailureRecord] = Field(default_factory=list)
    output_refs: list[StoredObjectRef] = Field(default_factory=list)

