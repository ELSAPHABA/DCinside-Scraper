# Logical Components - UOW-006 Output And Storage

## Component Overview

UOW-006 logical components store already-produced scraper results. They do not collect links, fetch posts, download media, run workers, or own checkpoint commit ordering.

| Component | Purpose |
|---|---|
| `OutputRunLayout` | derives sanitized local paths and S3 object keys for one `job_id`/`run_id` |
| `JsonlWriter` | appends one validated model/dict as one JSONL record |
| `AtomicJsonWriter` | writes small JSON documents with temp-file replace |
| `LocalOutputStore` | writes `posts.jsonl` and `report.json` locally |
| `LocalFailureStore` | writes and reads `failures.jsonl` locally |
| `LocalMediaStore` | writes media bytes locally or returns metadata-only media |
| `LocalCheckpointStore` | saves and loads local `Checkpoint.json` |
| `S3ObjectStore` | writes output/media objects through an optional S3-compatible client |
| `SafeFailureRecordBuilder` | builds/redacts safe failure records or safe failure context |
| `outputs.pathing` | path sanitization and containment helpers |
| `tests/strategies/outputs.py` | reusable Hypothesis strategies for storage transforms |

## OutputRunLayout

Responsibilities:

- accept `job_id`, `run_id`, and optional base/prefix
- sanitize path segments
- provide paths for `posts.jsonl`, `failures.jsonl`, `report.json`, and media
- provide matching S3 object keys
- reject local paths that escape the base output directory

Default local structure:

```text
outputs/<job_id>/<run_id>/
  posts.jsonl
  failures.jsonl
  report.json
  media/<gallery_id>/<post_no>/<media_type>/<filename>
```

## JsonlWriter

Responsibilities:

- serialize Pydantic models with `model_dump(mode="json")`
- serialize dict values through stdlib `json`
- write UTF-8
- append newline
- flush per record
- optionally fsync per record

Consumers:

- `LocalOutputStore.append_post`
- `LocalFailureStore.write_failure`

## AtomicJsonWriter

Responsibilities:

- write JSON to a temp file in the target directory
- flush the temp file
- atomically replace the target path with `os.replace`

Consumers:

- `LocalOutputStore.finalize`
- `LocalCheckpointStore.save`

## LocalOutputStore

Implements `OutputStorePort`.

Responsibilities:

- create the run directory
- append `PostResult` to `posts.jsonl`
- write final `JobReport` to `report.json`
- return `StoredObjectRef` values with `storage_type="local"`

Boundaries:

- does not deduplicate posts
- does not update checkpoints
- does not download media
- does not store secrets

## LocalFailureStore

Implements `FailureStorePort`.

Responsibilities:

- append safe `FailureRecord` to `failures.jsonl`
- read persisted failure records for retry input
- return `StoredObjectRef` values with `storage_type="local"`

Boundaries:

- does not deduplicate failures
- does not update checkpoints
- does not fetch or retry posts

## LocalMediaStore

Implements `MediaStorePort`.

Responsibilities:

- receive `MediaItem` and bytes from caller
- save bytes under the run media directory
- return `MediaItem` with `file_path`
- return unchanged or metadata-only updated `MediaItem` for metadata mode

Boundaries:

- does not create HTTP clients
- does not fetch URLs
- does not decide which media should be downloaded

## LocalCheckpointStore

Implements `CheckpointStorePort`.

Responsibilities:

- save multiple latest checkpoints in `Checkpoint.json`
- load by `job_id`
- load latest by `updated_at`
- guard in-process access with a local lock
- write using `AtomicJsonWriter`

Logical file shape:

```json
{
  "schema_version": "dcinside.local_checkpoint.v1",
  "updated_at": "2026-08-07T00:00:00Z",
  "checkpoints": {
    "<job_id>": {}
  }
}
```

## S3ObjectStore

Implements S3-compatible object writing.

Responsibilities:

- lazy import S3 client dependency
- validate S3 mode has required config
- write JSONL/report/media objects to configured bucket
- return `StoredObjectRef` values with `storage_type="s3"`
- build keys from `OutputRunLayout`

Boundaries:

- no Garage-specific API dependency
- no custom S3 signing
- no package-level S3 import
- no default test dependency on Garage

## SafeFailureRecordBuilder

Responsibilities:

- accept failure context from callers
- keep only allow-list fields
- drop unknown fields by default
- preserve `proxy_host` and `user_agent`
- reject proxy credentials, cookies, tokens, raw headers, and raw HTML/body/content

Output:

- safe `FailureRecord`
- or a safe metadata dict merged by the store before serialization

## Pathing Helpers

`sanitize_path_segment(value, fallback)`:

- allow-list characters
- replace unsafe characters with `_`
- return fallback if empty

`ensure_under_base(base, target)`:

- resolve paths
- reject traversal outside base

These helpers are pure enough for PBT.

## Test Components

### `tests/test_outputs_storage.py`

Covers:

- local post append
- local failure append
- report atomic write
- media bytes save
- metadata-only media save
- checkpoint save/load/load_latest
- path traversal rejection
- safe failure redaction

### `tests/test_outputs_properties.py`

Covers:

- path segment sanitization properties
- output key generation properties
- JSONL round trip properties
- checkpoint document round trip properties
- failure redaction idempotence

### `tests/test_outputs_s3_smoke.py`

Skipped by default.

Runs only when `DCINSIDE_S3_SMOKE_ENABLED=true` and all required S3 env values exist.

## Component Boundaries

- JobRunner decides when to call output and checkpoint stores.
- UOW-006 only reports storage success or failure.
- Duplicate prevention belongs to UOW-005.
- PostgreSQL checkpoint storage belongs to UOW-008 or later adapter work.
- Polars normalization belongs to future platform processing.
