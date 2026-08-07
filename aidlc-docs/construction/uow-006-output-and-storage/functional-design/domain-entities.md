# Domain Entities - UOW-006 Output And Storage

## Existing Contract Entities

UOW-006 reuses the UOW-001 model and port contracts below.

| Entity | Source | Role |
|---|---|---|
| `StorageConfig` | `models/job.py` | selects local or S3 output and local or PostgreSQL checkpoint mode |
| `S3StorageConfig` | `models/job.py` | contains endpoint, bucket, prefix, and region for S3-compatible output |
| `PostResult` | `models/post.py` | successful post scrape output written to `posts.jsonl` |
| `FailureRecord` | `models/report.py` | failed item output written to `failures.jsonl` |
| `JobReport` | `models/report.py` | final run report written to `report.json` |
| `StoredObjectRef` | `models/report.py` | reference returned after writing an object |
| `MediaItem` | `models/media.py` | media metadata updated with local path or object key |
| `Checkpoint` | `models/checkpoint.py` | local checkpoint payload saved in `Checkpoint.json` |
| `OutputStorePort` | `core/ports.py` | output store protocol |
| `MediaStorePort` | `core/ports.py` | media store protocol |
| `CheckpointStorePort` | `core/ports.py` | checkpoint store protocol |

## Store Components

### LocalOutputStore

Concrete local implementation of `OutputStorePort`.

Responsibilities:

- create `outputs/<job_id>/<run_id>/`
- append posts to `posts.jsonl`
- append failures to `failures.jsonl`
- write `report.json`
- return local `StoredObjectRef` values

### JsonlWriter

Small helper for newline-delimited JSON writes.

Responsibilities:

- serialize one model/dict per line
- write UTF-8
- append newline
- flush records according to the concrete writer policy

### LocalMediaStore

Concrete local implementation of `MediaStorePort`.

Responsibilities:

- save bytes under the run media directory
- derive safe filenames
- set `MediaItem.file_path`
- support metadata-only pass-through

### LocalCheckpointStore

Concrete local implementation of `CheckpointStorePort`.

Responsibilities:

- save multiple latest checkpoints in `Checkpoint.json`
- load by `job_id`
- load latest by `updated_at`
- write through same-directory temp file and atomic replace

### S3ObjectStore

S3-compatible implementation shared by output and media storage.

Responsibilities:

- put JSONL/report/media objects into configured bucket
- build object keys from the same relative paths as local mode
- return S3-style `StoredObjectRef` values
- work with Garage by configuration only

## Output Layout Entity

### OutputRunLayout

Derived value object for run-relative paths.

Fields:

- `job_id`
- `run_id`
- `base_path` or S3 `prefix`
- `posts_path`
- `failures_path`
- `report_path`
- `media_prefix`

Rules:

- all paths are relative below `outputs/<job_id>/<run_id>/`
- path segments are sanitized before joining
- resume uses a new `run_id`

## Failure Context Entity

### SafeFailureContext

Optional safe context that can be merged into `FailureRecord` serialization.

Allowed fields:

- `proxy_host`
- `user_agent`
- `request_url`
- `http_status`

Forbidden fields:

- `proxy_id`
- `proxy_password`
- `cookie`
- `token`
- `headers`
- `raw_html`
- `raw_body`

## Checkpoint File Entity

### LocalCheckpointDocument

Logical JSON document stored as `Checkpoint.json`.

Fields:

- `schema_version`
- `updated_at`
- `checkpoints`

`checkpoints` is keyed by `job_id` and stores serialized `Checkpoint` objects.

## Stored Object Reference Rules

Local objects:

- `storage_type`: `local`
- `local_path`: absolute or base-relative local path
- `object_key`: relative run path
- `uri`: local path string

S3-compatible objects:

- `storage_type`: `s3`
- `object_key`: bucket object key
- `local_path`: `null`
- `uri`: `s3://<bucket>/<object_key>`

## Entity Boundaries

- `PostResult` remains scraper-native and nested.
- `FailureRecord` remains safe and retry-oriented.
- `Checkpoint` remains lifecycle state, not output data.
- `MediaItem` stores metadata plus storage reference, not raw bytes.
- S3 credentials are configuration/runtime data, not domain data.
