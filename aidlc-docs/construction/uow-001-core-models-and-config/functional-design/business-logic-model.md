# Business Logic Model - UOW-001 Core Models And Config

## Purpose

UOW-001은 scraper runtime의 shared contract를 정의합니다. 이 unit은 네트워크 요청, HTML 파싱, 파일 저장을 구현하지 않고, 모든 adapter와 service가 공유할 Pydantic 모델, validation, error model, port protocol을 고정합니다.

## Design Decisions

| Area | Decision |
|---|---|
| Model library | Pydantic v2 |
| Extra fields | Input/config/result 모델은 `extra="forbid"` |
| Extension point | 명시적 `metadata: dict[str, Any]` 필드만 허용 |
| Job config | `JobConfig.job_type` + `source` discriminated union |
| Content blocks | `type` 기반 discriminated union |
| Identifiers | 원본 ID는 `str`, 숫자 비교용 normalized field는 `int | None` |
| Error handling | Core 내부 typed exception, adapter boundary에서 `ErrorResult` |
| Schema version | `PostResult`, `Checkpoint`, `JobReport` top-level에 version 포함 |

## Public API Logic

Public API는 import side effect가 없어야 합니다. 함수 호출 전까지 network, file write, terminal prompt가 발생하면 안 됩니다.

| API | Input Model | Output Model | Error Behavior |
|---|---|---|---|
| `search_gallery` | `GallerySearchRequest` | `GallerySearchPage` | typed exception |
| `search_integrated` | `IntegratedSearchRequest` | `IntegratedSearchPage` | typed exception |
| `fetch_post` | `PostRequest` | `PostResult` | typed exception |
| `fetch_comments` | `CommentRequest` | `list[Comment]` | typed exception |
| `run_job` | `JobConfig` | `JobReport` | typed exception |
| `resume_job` | `ResumeRequest` | `JobReport` | typed exception |

Adapters convert typed exceptions into `ErrorResult`.

## Job Config Model

`JobConfig` contains common execution options and one source-specific payload.

Required common fields:

- `job_id`
- `job_type`
- `site_id`
- `source`
- `scrape_options`
- `worker_config`
- `storage_config`
- `created_at`
- `metadata`

`source` is a discriminated union:

| Source Type | Required Data |
|---|---|
| `direct_post` | one or more post URLs |
| `gallery_search` | gallery type, gallery ID, search type, keyword, optional `search_pos`, page |
| `integrated_search` | keyword, sort mode, page range |
| `deep_search` | keyword, integrated search seed options, required date or post-number range |
| `no_keyword_range` | gallery type, gallery ID, date range and/or post-number range |
| `realtime_keyword` | gallery/search scope, keyword, poll interval, exactly one termination condition |
| `realtime_all` | gallery scope, poll interval, exactly one termination condition |

## Content Block Logic

`PostResult.content` preserves body order through a list of content blocks.

Content block variants:

- `text`
- `image`
- `dc_video`
- `youtube`
- `link`
- `series`
- `unknown_embed`

Every block has:

- `type`
- `order`
- `metadata`

Variant-specific payload is stored only on the matching variant. For example, a `dc_video` block may contain `url`, `thumbnail_url`, `description`, and `duration`, while a `text` block contains `text`.

## Identifier Logic

DCinside identifiers are preserved as source strings.

Examples:

- `gallery_id: str`
- `post_id: str`
- `comment_id: str`
- `parent_comment_id: str | None`

Where range comparison or sorting is required, normalized integer fields are also provided:

- `post_number: int | None`
- `comment_number: int | None`
- `parent_comment_number: int | None`

If conversion fails, the source string is retained and the normalized integer is `null`.

## Schema Version Logic

Top-level version fields:

| Model | Version Field | Initial Value |
|---|---|---|
| `PostResult` | `schema_version` | `dcinside.post.v1` |
| `Checkpoint` | `schema_version` | `dcinside.checkpoint.v1` |
| `JobReport` | `schema_version` | `dcinside.job_report.v1` |

Nested models do not need independent schema versions unless they become separately persisted artifacts.

## Error Logic

Core services raise typed exceptions:

- `ValidationError`
- `UnsupportedSourceError`
- `UnavailableContentError`
- `CaptchaDetectedError`
- `BlockedResponseError`
- `NetworkFailureError`
- `ParseFailureError`
- `StorageFailureError`
- `CheckpointFailureError`

Adapter boundary errors use:

- `code`
- `message`
- `details`
- `retryable`
- `safe_to_log`

`details` must not include Proxy password, raw cookie, token, full credential file content, or raw private environment data.

## Port Logic

Ports are protocols, not concrete implementations.

Required ports:

- `HttpPort`
- `OutputStorePort`
- `MediaStorePort`
- `CheckpointStorePort`
- `ClockPort`
- `LoggerPort`

UOW-001 defines method contracts only. UOW-002, UOW-006, UOW-008 provide concrete implementations.

