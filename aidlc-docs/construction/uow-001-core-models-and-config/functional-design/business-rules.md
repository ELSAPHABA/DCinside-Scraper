# Business Rules - UOW-001 Core Models And Config

## Model Rules

### BR-001. Pydantic Version

All models in this unit must target Pydantic v2.

Implementation implications:

- Use `BaseModel`.
- Use `ConfigDict(extra="forbid")`.
- Use `model_dump(mode="json")` for JSONL/checkpoint serialization boundaries.

### BR-002. Extra Field Policy

Public input, config, and scrape result models must reject unknown fields.

Allowed extension path:

- `metadata: dict[str, Any] = {}`

Unknown fields must not be silently accepted at top-level.

### BR-003. Import Side Effects

Importing `dcinside_scraper` must not:

- start network requests
- read or write files
- prompt terminal input
- create output directories
- load `.env` or `user-agents.txt`

Runtime side effects occur only when an API, CLI command, container entrypoint, or MCP tool is invoked.

## Job Config Rules

### BR-004. Job Type And Source Must Match

`JobConfig.job_type` must match the discriminator of `JobConfig.source`.

Invalid example:

- `job_type="deep_search"` with `source.type="gallery_search"`

This must fail validation.

### BR-005. Direct Post Source

`direct_post` source must include at least one valid DCinside post URL.

Each URL must contain enough information to derive:

- `gallery_id`
- `post_id`
- gallery type when available

### BR-006. Gallery Search Source

`gallery_search` source must include:

- `gallery_type`
- `gallery_id`
- `s_type`
- `keyword`

`search_pos` may be omitted or empty on the first request.

### BR-007. Integrated Search Source

`integrated_search` source must include a non-empty keyword.

Sort mode must be one of the supported integrated search modes defined by later search design.

### BR-008. Deep Search Source

`deep_search` source must include:

- non-empty keyword
- date range or post-number range

If both date range and post-number range are absent, validation must fail.

### BR-009. No-Keyword Range Source

`no_keyword_range` source must include:

- `gallery_type`
- `gallery_id`
- date range and/or post-number range

It must not require a keyword.

### BR-010. Realtime Source

Realtime sources must include exactly one termination condition:

- `duration_seconds`
- `end_at`

If both are present or both are missing, validation must fail.

`realtime_keyword` must include a non-empty keyword.

## Range Rules

### BR-011. Date Range

If both `date_from` and `date_to` exist, `date_from <= date_to` must hold.

Dates should be stored as ISO date strings or date values serializable by Pydantic v2.

### BR-012. Post Number Range

If both `min_post_number` and `max_post_number` exist, `min_post_number <= max_post_number` must hold.

Original `post_id` remains a string even when `post_number` is available.

## Content Rules

### BR-013. Content Order

`PostResult.content` must preserve source body order by `order`.

Each content block must have a unique non-negative `order` within one post.

### BR-014. Content Block Discriminator

Each content block must have a `type` matching one supported content block variant.

Unknown or unsupported embed content may use `unknown_embed` with raw-safe metadata, but must not include full raw HTML unless explicitly allowed by a later parser design.

### BR-015. DC Video Description

`dc_video` block description is nullable.

When the source has no description, store `description=null`.

## Result Schema Rules

### BR-016. PostResult Required Top-Level Fields

`PostResult` must include:

- `schema_version`
- `scrap_timestamp`
- `site_id`
- `gallery_id`
- `post_id`
- `post_number`
- `is_repost`
- `repost`
- `title`
- `author`
- `nickname_type`
- `date`
- `views`
- `recommendations`
- `content`
- `images`
- `comments`
- `metadata`

### BR-017. Repost Consistency

If `is_repost=false`, `repost` must be `null`.

If `is_repost=true`, `repost` must be present.

`repost` must not include original post comment count.

### BR-018. Comments

Top-level comments and replies use the same `Comment` model.

Replies must have a parent identifier when it is available from source data.

## Checkpoint Rules

### BR-019. Checkpoint Status

Checkpoint status must be one of:

- `running`
- `stopped`
- `completed`

### BR-020. Stop Reason

Stopped checkpoint reason must be one of:

- `captcha`
- `manual_stop`
- `error`
- `timeout`
- `lease_expired`

When status is `stopped`, `reason` is required. When status is not `stopped`, `reason` must be `null`.

### BR-021. Retry After

CAPTCHA retry time is optional.

If present, `retry_after` must be UTC ISO-8601 compatible.

## Error Rules

### BR-022. Typed Core Exceptions

Core code may raise typed exceptions for validation, unsupported source, unavailable content, CAPTCHA/block, network, parser, storage, and checkpoint failures.

### BR-023. Adapter Error Result

Adapters must convert exceptions to `ErrorResult` before returning through CLI, container, or MCP boundaries.

`ErrorResult.message` must be safe for users. Secret-bearing values must be omitted from `details`.

## Port Rules

### BR-024. Port Boundaries

Ports must define behavior, not implementation policy.

Concrete HTTP, local file, S3-compatible, PostgreSQL, and logger behavior belongs to later units.

### BR-025. Async Boundary

Public scrape APIs and I/O ports are async by default.

Pure validation and model conversion functions may remain synchronous.

