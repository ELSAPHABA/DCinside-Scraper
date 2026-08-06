"""Job configuration, source, request, and search result contracts."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from dcinside_scraper.models.base import MetadataModel
from dcinside_scraper.models.enums import (
    CheckpointMode,
    DcconMode,
    GalleryType,
    IntegratedSearchSort,
    JobType,
    MediaMode,
    OutputMode,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RangeFilter(MetadataModel):
    """Date and post-number range filter."""

    date_from: date | None = None
    date_to: date | None = None
    min_post_number: int | None = Field(default=None, ge=0)
    max_post_number: int | None = Field(default=None, ge=0)

    def has_any_bound(self) -> bool:
        return any(
            value is not None
            for value in (
                self.date_from,
                self.date_to,
                self.min_post_number,
                self.max_post_number,
            )
        )

    @model_validator(mode="after")
    def _validate_order(self) -> "RangeFilter":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be before or equal to date_to")
        if (
            self.min_post_number is not None
            and self.max_post_number is not None
            and self.min_post_number > self.max_post_number
        ):
            raise ValueError("min_post_number must be <= max_post_number")
        return self


class RealtimeOptions(MetadataModel):
    """Realtime run termination condition."""

    duration_seconds: int | None = Field(default=None, ge=1)
    end_at: datetime | None = None

    @model_validator(mode="after")
    def _validate_exactly_one_stop_condition(self) -> "RealtimeOptions":
        if (self.duration_seconds is None) == (self.end_at is None):
            raise ValueError("exactly one of duration_seconds or end_at is required")
        return self


class ScrapeOptions(MetadataModel):
    include_comments: bool = True
    image_mode: MediaMode = MediaMode.METADATA_ONLY
    dccon_mode: DcconMode = DcconMode.METADATA
    request_interval_seconds: float = Field(default=1.0, ge=0)
    max_post_retries: int = Field(default=3, ge=0)
    max_comment_pages: int = Field(default=100, ge=1)
    range_filter: RangeFilter | None = None


class WorkerConfig(MetadataModel):
    post_worker_count: int = Field(default=1, ge=1)
    queue_max_size: int | None = Field(default=None, ge=1)


class S3StorageConfig(MetadataModel):
    endpoint_url: str
    bucket: str = Field(min_length=1, max_length=255)
    prefix: str | None = None
    region: str | None = None


class PostgresCheckpointConfig(MetadataModel):
    dsn: str = Field(min_length=1, max_length=4096)


class StorageConfig(MetadataModel):
    output_mode: OutputMode = OutputMode.LOCAL
    checkpoint_mode: CheckpointMode = CheckpointMode.LOCAL
    base_output_path: str | None = None
    s3: S3StorageConfig | None = None
    postgres: PostgresCheckpointConfig | None = None

    @model_validator(mode="after")
    def _validate_selected_backends(self) -> "StorageConfig":
        if self.output_mode == OutputMode.S3 and self.s3 is None:
            raise ValueError("s3 config is required when output_mode is s3")
        if self.checkpoint_mode == CheckpointMode.POSTGRES and self.postgres is None:
            raise ValueError("postgres config is required when checkpoint_mode is postgres")
        return self


class DirectPostSource(MetadataModel):
    type: Literal["direct_post"] = "direct_post"
    urls: list[str] = Field(min_length=1, max_length=500)

    @field_validator("urls")
    @classmethod
    def _validate_urls(cls, urls: list[str]) -> list[str]:
        for url in urls:
            if "gall.dcinside.com" not in url or "/board/view/" not in url:
                raise ValueError("url must be a DCinside post URL")
        return urls


class GallerySearchSource(MetadataModel):
    type: Literal["gallery_search"] = "gallery_search"
    gallery_type: GalleryType
    gallery_id: str = Field(min_length=1, max_length=100)
    s_type: str = Field(min_length=1, max_length=100)
    keyword: str = Field(min_length=1, max_length=500)
    page: int = Field(default=1, ge=1)
    search_pos: str | None = None
    head_id: str | None = None


class IntegratedSearchSource(MetadataModel):
    type: Literal["integrated_search"] = "integrated_search"
    keyword: str = Field(min_length=1, max_length=500)
    sort_mode: IntegratedSearchSort = IntegratedSearchSort.RELEVANCE
    page_start: int = Field(default=1, ge=1)
    page_end: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def _validate_page_range(self) -> "IntegratedSearchSource":
        if self.page_start > self.page_end:
            raise ValueError("page_start must be <= page_end")
        return self


class DeepSearchSource(MetadataModel):
    type: Literal["deep_search"] = "deep_search"
    keyword: str = Field(min_length=1, max_length=500)
    seed_sort_mode: IntegratedSearchSort = IntegratedSearchSort.RELEVANCE
    range_filter: RangeFilter

    @model_validator(mode="after")
    def _validate_range(self) -> "DeepSearchSource":
        if not self.range_filter.has_any_bound():
            raise ValueError("deep_search requires a date or post-number range")
        return self


class NoKeywordRangeSource(MetadataModel):
    type: Literal["no_keyword_range"] = "no_keyword_range"
    gallery_type: GalleryType
    gallery_id: str = Field(min_length=1, max_length=100)
    range_filter: RangeFilter

    @model_validator(mode="after")
    def _validate_range(self) -> "NoKeywordRangeSource":
        if not self.range_filter.has_any_bound():
            raise ValueError("no_keyword_range requires a date or post-number range")
        return self


class RealtimeKeywordSource(MetadataModel):
    type: Literal["realtime_keyword"] = "realtime_keyword"
    keyword: str = Field(min_length=1, max_length=500)
    gallery_type: GalleryType | None = None
    gallery_id: str | None = Field(default=None, max_length=100)
    poll_interval_seconds: float = Field(default=30.0, ge=1.0)
    termination: RealtimeOptions


class RealtimeAllSource(MetadataModel):
    type: Literal["realtime_all"] = "realtime_all"
    gallery_type: GalleryType
    gallery_id: str = Field(min_length=1, max_length=100)
    poll_interval_seconds: float = Field(default=30.0, ge=1.0)
    termination: RealtimeOptions


JobSource = Annotated[
    DirectPostSource
    | GallerySearchSource
    | IntegratedSearchSource
    | DeepSearchSource
    | NoKeywordRangeSource
    | RealtimeKeywordSource
    | RealtimeAllSource,
    Field(discriminator="type"),
]


class JobConfig(MetadataModel):
    job_id: str = Field(min_length=1, max_length=200)
    job_type: JobType
    site_id: str = Field(default="dcinside", min_length=1, max_length=50)
    source: JobSource
    scrape_options: ScrapeOptions = Field(default_factory=ScrapeOptions)
    worker_config: WorkerConfig = Field(default_factory=WorkerConfig)
    storage_config: StorageConfig = Field(default_factory=StorageConfig)
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _validate_source_type(self) -> "JobConfig":
        if self.job_type.value != self.source.type:
            raise ValueError("job_type must match source.type")
        return self


class GallerySearchRequest(MetadataModel):
    gallery_type: GalleryType
    gallery_id: str = Field(min_length=1, max_length=100)
    s_type: str = Field(min_length=1, max_length=100)
    keyword: str = Field(min_length=1, max_length=500)
    page: int = Field(default=1, ge=1)
    search_pos: str | None = None
    head_id: str | None = None


class IntegratedSearchRequest(MetadataModel):
    keyword: str = Field(min_length=1, max_length=500)
    sort_mode: IntegratedSearchSort = IntegratedSearchSort.RELEVANCE
    page: int = Field(default=1, ge=1)


class PostRequest(MetadataModel):
    url: str = Field(min_length=1, max_length=4096)
    gallery_type: GalleryType | None = None
    gallery_id: str | None = Field(default=None, max_length=100)
    post_id: str | None = Field(default=None, max_length=100)
    post_number: int | None = Field(default=None, ge=0)
    scrape_options: ScrapeOptions = Field(default_factory=ScrapeOptions)


class CommentRequest(MetadataModel):
    gallery_id: str = Field(min_length=1, max_length=100)
    post_id: str = Field(min_length=1, max_length=100)
    post_number: int | None = Field(default=None, ge=0)
    gallery_type: GalleryType | None = None


class ResumeRequest(MetadataModel):
    job_id: str | None = Field(default=None, max_length=200)


class SearchPosition(MetadataModel):
    page: int = Field(default=1, ge=1)
    search_pos: str | None = None
    cursor: str | None = None


class PostKey(MetadataModel):
    site_id: str = Field(default="dcinside", min_length=1, max_length=50)
    board_id: str = Field(min_length=1, max_length=100)
    post_id: str = Field(min_length=1, max_length=100)


class PostCandidate(MetadataModel):
    url: str = Field(min_length=1, max_length=4096)
    gallery_id: str = Field(min_length=1, max_length=100)
    post_id: str = Field(min_length=1, max_length=100)
    post_number: int | None = Field(default=None, ge=0)
    title: str | None = Field(default=None, max_length=1000)
    created_at: datetime | date | str | None = None


class GallerySearchPage(MetadataModel):
    gallery_id: str = Field(min_length=1, max_length=100)
    page: int = Field(ge=1)
    candidates: list[PostCandidate] = Field(default_factory=list)
    next_search_pos: str | None = None
    has_next: bool = False


class IntegratedSearchPage(MetadataModel):
    keyword: str = Field(min_length=1, max_length=500)
    page: int = Field(ge=1)
    candidates: list[PostCandidate] = Field(default_factory=list)
    gallery_ids: list[str] = Field(default_factory=list)
    has_next: bool = False
