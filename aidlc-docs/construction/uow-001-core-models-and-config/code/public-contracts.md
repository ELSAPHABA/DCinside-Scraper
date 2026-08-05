# Public Contracts - UOW-001 Core Models And Config

## Package Contract

UOW-001 creates the import-safe package `dcinside_scraper`.

Importing the package must not:

- make network requests
- read `.env`
- read `user-agents.txt`
- write files
- prompt terminal input

## Public API Signatures

The public async API surface is defined in `src/dcinside_scraper/core/api.py`.

| Function | Input | Output | Runtime Status |
|---|---|---|---|
| `search_gallery` | `GallerySearchRequest` | `GallerySearchPage` | implemented in UOW-003 |
| `search_integrated` | `IntegratedSearchRequest` | `IntegratedSearchPage` | implemented in UOW-003 |
| `fetch_post` | `PostRequest` | `PostResult` | implemented in UOW-004 |
| `fetch_comments` | `CommentRequest` | `list[Comment]` | implemented in UOW-004 |
| `run_job` | `JobConfig` | `JobReport` | implemented in UOW-005 |
| `resume_job` | `ResumeRequest` | `JobReport` | implemented in UOW-005 |

Current placeholder functions raise `UnavailableContentError` without side effects.

## Persisted Schema Versions

| Model | Schema Version |
|---|---|
| `PostResult` | `dcinside.post.v1` |
| `Checkpoint` | `dcinside.checkpoint.v1` |
| `JobReport` | `dcinside.job_report.v1` |

## Core Model Families

| Area | Main Models |
|---|---|
| Job configuration | `JobConfig`, `ScrapeOptions`, `WorkerConfig`, `StorageConfig`, source models |
| Search requests/results | `GallerySearchRequest`, `IntegratedSearchRequest`, `PostCandidate`, search page models |
| Post body | ordered `ContentBlock` union |
| Media | `MediaItem`, `DcconItem` |
| Comments | `Comment`, `AuthorInfo` |
| Persistence state | `Checkpoint`, `JobReport`, `FailureRecord`, `StoredObjectRef` |
| Adapter errors | `ErrorResult` |

## Validation Rules

Implemented in UOW-001:

- `extra="forbid"` for public Pydantic models
- bounded JSON-compatible `metadata`
- job/source type matching
- date and post-number range ordering
- deep-search range requirement
- no-keyword range requirement
- realtime exactly-one termination condition
- repost consistency
- checkpoint status/reason consistency
- content block order uniqueness

## Error Mapping

Core errors are typed exceptions. Adapter boundaries should use `ErrorMapper` to convert them to `ErrorResult`.

`SecretRedactor` drops non-allowlisted detail keys and redacts secret-like allowed values.

## Ports

UOW-001 defines Protocol contracts only:

- `HttpPort`
- `OutputStorePort`
- `MediaStorePort`
- `CheckpointStorePort`
- `ClockPort`
- `LoggerPort`

Concrete adapters are deferred to later units.

