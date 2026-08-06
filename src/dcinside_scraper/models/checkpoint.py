"""Checkpoint contract."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from dcinside_scraper.models.base import MetadataModel
from dcinside_scraper.models.enums import CheckpointStatus, StopReason
from dcinside_scraper.models.job import JobConfig, PostCandidate, PostKey, SearchPosition, utc_now


class Checkpoint(MetadataModel):
    schema_version: Literal["dcinside.checkpoint.v1"] = "dcinside.checkpoint.v1"
    job_id: str = Field(min_length=1, max_length=200)
    site_id: str = Field(default="dcinside", min_length=1, max_length=50)
    board_id: str | None = Field(default=None, max_length=100)
    last_completed_post_id: str | None = Field(default=None, max_length=100)
    last_completed_url: str | None = Field(default=None, max_length=4096)
    scraping_processed_count: int = Field(default=0, ge=0)
    worker_id: str | None = Field(default=None, max_length=100)
    lease_until: datetime | None = None
    status: CheckpointStatus = CheckpointStatus.RUNNING
    reason: StopReason | None = None
    retry_after: datetime | None = None
    job_config_snapshot: JobConfig
    search_position: SearchPosition | None = None
    completed_keys: list[PostKey] = Field(default_factory=list)
    remaining_queue: list[PostCandidate] | None = None
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _validate_status_reason(self) -> "Checkpoint":
        if self.status == CheckpointStatus.STOPPED and self.reason is None:
            raise ValueError("reason is required when checkpoint is stopped")
        if self.status != CheckpointStatus.STOPPED and self.reason is not None:
            raise ValueError("reason must be null unless checkpoint is stopped")
        return self

