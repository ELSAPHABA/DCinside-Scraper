# Domain Entities - UOW-001 Core Models And Config

## Entity Overview

UOW-001 defines shared domain entities. Names here describe model contracts, not final file/class names.

## Configuration Entities

### JobConfig

Represents one scrape Job.

Fields:

- `job_id: str`
- `job_type: JobType`
- `site_id: str`
- `source: JobSource`
- `scrape_options: ScrapeOptions`
- `worker_config: WorkerConfig`
- `storage_config: StorageConfig`
- `created_at: datetime`
- `metadata: dict[str, Any]`

Relationships:

- owns one `JobSource`
- owns one `ScrapeOptions`
- owns one `WorkerConfig`
- owns one `StorageConfig`

### JobSource

Discriminated union for collection entrypoints.

Variants:

- `DirectPostSource`
- `GallerySearchSource`
- `IntegratedSearchSource`
- `DeepSearchSource`
- `NoKeywordRangeSource`
- `RealtimeKeywordSource`
- `RealtimeAllSource`

### ScrapeOptions

Controls optional scrape behavior.

Fields:

- `include_comments: bool`
- `image_mode: MediaMode`
- `dccon_mode: DcconMode`
- `request_interval_seconds: float`
- `max_post_retries: int`
- `range_filter: RangeFilter | None`
- `metadata: dict[str, Any]`

### WorkerConfig

Controls worker execution.

Fields:

- `post_worker_count: int`
- `media_worker_count: int`
- `queue_max_size: int | None`
- `metadata: dict[str, Any]`

### StorageConfig

Defines storage mode, not concrete storage implementation.

Fields:

- `output_mode: OutputMode`
- `checkpoint_mode: CheckpointMode`
- `base_output_path: str | None`
- `s3: S3StorageConfig | None`
- `postgres: PostgresCheckpointConfig | None`
- `metadata: dict[str, Any]`

## Request Entities

### GallerySearchRequest

Fields:

- `gallery_type: GalleryType`
- `gallery_id: str`
- `s_type: str`
- `keyword: str`
- `page: int`
- `search_pos: str | None`
- `head_id: str | None`
- `metadata: dict[str, Any]`

### IntegratedSearchRequest

Fields:

- `keyword: str`
- `sort_mode: IntegratedSearchSort`
- `page: int`
- `metadata: dict[str, Any]`

### PostRequest

Fields:

- `url: str`
- `gallery_type: GalleryType | None`
- `gallery_id: str | None`
- `post_id: str | None`
- `post_number: int | None`
- `scrape_options: ScrapeOptions`
- `metadata: dict[str, Any]`

### CommentRequest

Fields:

- `gallery_id: str`
- `post_id: str`
- `post_number: int | None`
- `gallery_type: GalleryType | None`
- `metadata: dict[str, Any]`

### ResumeRequest

Fields:

- `job_id: str | None`
- `metadata: dict[str, Any]`

## Result Entities

### PostResult

JSONL top-level post result.

Fields:

- `schema_version: str`
- `scrap_timestamp: datetime`
- `site_id: str`
- `gallery_id: str`
- `post_id: str`
- `post_number: int | None`
- `is_repost: bool`
- `repost: RepostInfo | None`
- `title: str`
- `author: AuthorInfo`
- `nickname_type: NicknameType`
- `date: datetime | str | None`
- `views: int | None`
- `recommendations: RecommendationInfo`
- `comment_count: int | None`
- `content: list[ContentBlock]`
- `images: list[MediaItem]`
- `comments: list[Comment]`
- `links: list[ContentLink]`
- `metadata: dict[str, Any]`

### RepostInfo

Original post metadata for `(펌)` posts.

Fields:

- `gallery_id: str`
- `gallery_name: str | None`
- `post_id: str`
- `post_number: int | None`
- `author: AuthorInfo`
- `nickname_type: NicknameType`
- `views: int | None`
- `recommendations: RecommendationInfo`
- `metadata: dict[str, Any]`

Excluded:

- original post comment count

### AuthorInfo

Fields:

- `name: str | None`
- `user_id: str | None`
- `ip: str | None`
- `nickname_type: NicknameType`
- `metadata: dict[str, Any]`

### RecommendationInfo

Fields:

- `upvotes: int | None`
- `downvotes: int | None`
- `metadata: dict[str, Any]`

## Content Entities

### ContentBlock

Discriminated union by `type`.

Common fields:

- `type: ContentBlockType`
- `order: int`
- `metadata: dict[str, Any]`

Variants:

- `TextBlock`
- `ImageBlock`
- `DcVideoBlock`
- `YouTubeBlock`
- `LinkBlock`
- `SeriesBlock`
- `UnknownEmbedBlock`

### MediaItem

Fields:

- `media_id: str | None`
- `media_type: MediaType`
- `url: str`
- `source_url: str | None`
- `file_path: str | None`
- `object_key: str | None`
- `description: str | None`
- `metadata: dict[str, Any]`

### DcconItem

Fields:

- `src: str | None`
- `alt: str | None`
- `title: str | None`
- `conalt: str | None`
- `file_path: str | None`
- `object_key: str | None`
- `metadata: dict[str, Any]`

### Comment

Fields:

- `comment_id: str`
- `comment_number: int | None`
- `parent_comment_id: str | None`
- `parent_comment_number: int | None`
- `depth: int`
- `author: AuthorInfo`
- `memo_text: str | None`
- `dccons: list[DcconItem]`
- `created_at: datetime | str | None`
- `metadata: dict[str, Any]`

## Checkpoint Entities

### Checkpoint

Fields:

- `schema_version: str`
- `job_id: str`
- `site_id: str`
- `board_id: str | None`
- `last_completed_post_id: str | None`
- `last_completed_url: str | None`
- `scraping_processed_count: int`
- `worker_id: str | None`
- `lease_until: datetime | None`
- `status: CheckpointStatus`
- `reason: StopReason | None`
- `retry_after: datetime | None`
- `job_config_snapshot: JobConfig`
- `search_position: SearchPosition | None`
- `completed_keys: list[PostKey]`
- `remaining_queue: list[PostCandidate] | None`
- `updated_at: datetime`
- `metadata: dict[str, Any]`

### PostKey

Deduplication key.

Fields:

- `site_id: str`
- `board_id: str`
- `post_id: str`

## Report And Error Entities

### FailureRecord

Fields:

- `gallery_id: str | None`
- `post_id: str | None`
- `post_number: int | None`
- `url: str | None`
- `reason: str`
- `stage: str`
- `retryable: bool`
- `metadata: dict[str, Any]`

### JobReport

Fields:

- `schema_version: str`
- `job_id: str`
- `status: JobReportStatus`
- `success_count: int`
- `failure_count: int`
- `deduped_count: int`
- `filtered_count: int`
- `started_at: datetime`
- `finished_at: datetime | None`
- `failures: list[FailureRecord]`
- `output_refs: list[StoredObjectRef]`
- `metadata: dict[str, Any]`

### ErrorResult

Fields:

- `code: str`
- `message: str`
- `details: dict[str, Any]`
- `retryable: bool`
- `safe_to_log: bool`

## Enum Entities

Required enums:

- `JobType`
- `GalleryType`
- `MediaMode`
- `DcconMode`
- `OutputMode`
- `CheckpointMode`
- `CheckpointStatus`
- `StopReason`
- `ContentBlockType`
- `MediaType`
- `NicknameType`
- `IntegratedSearchSort`
- `JobReportStatus`

## Port Entities

### HttpPort

Async operations:

- `get`
- `post`
- `download`
- `close`

### OutputStorePort

Async operations:

- `append_post`
- `write_failure`
- `finalize`

### MediaStorePort

Async operations:

- `save_media`
- `save_metadata_only`

### CheckpointStorePort

Async operations:

- `save`
- `load`
- `load_latest`

### ClockPort

Sync operations:

- `now_utc`

### LoggerPort

Sync operations:

- `debug`
- `info`
- `warning`
- `error`
