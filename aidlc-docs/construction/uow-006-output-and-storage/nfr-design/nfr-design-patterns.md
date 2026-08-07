# NFR Design Patterns - UOW-006 Output And Storage

## Scope

This document translates UOW-006 NFR requirements into implementation patterns. It covers local output stores, JSONL writes, path sanitization, safe failure context, atomic JSON writes, optional S3 dependency loading, test organization, and optional Garage smoke tests.

## Confirmed Design Decisions

| Question | Answer | Design Decision |
|---|---|---|
| Q1 | A | Put `LocalOutputStore`, `LocalMediaStore`, and `LocalCheckpointStore` in `outputs.local`; share path/key calculation through a small layout/path utility. |
| Q2 | A | Use a small `JsonlWriter` with Pydantic JSON mode, stdlib `json`, newline append, flush, and optional fsync. |
| Q3 | A | Use `sanitize_path_segment(value, fallback)` with allow-list characters and verify resolved local paths stay below the base output directory. |
| Q4 | A | Use `SafeFailureRecordBuilder` or `sanitize_failure_context` with allow-list fields and default-drop unknown context. |
| Q5 | A | Use `AtomicJsonWriter` for `Checkpoint.json` and `report.json`; do not use it for JSONL append. |
| Q6 | A | Lazy import S3 optional dependency inside `S3ObjectStore`; local imports must work without S3 packages. |
| Q7 | A | Put example tests in `tests/test_outputs_storage.py`, PBT in `tests/test_outputs_properties.py`, strategies in `tests/strategies/outputs.py`, and S3 smoke in an env-gated test file. |
| Q8 | A | Run Garage/S3 smoke only when `DCINSIDE_S3_SMOKE_ENABLED=true` and all required S3 env vars exist. |

No follow-up question is required.

## Pattern 1. Local Store Components

Local storage is split by existing UOW-001 ports:

- `LocalOutputStore` implements `OutputStorePort`
- `LocalMediaStore` implements `MediaStorePort`
- `LocalCheckpointStore` implements `CheckpointStorePort`

Shared path/key work stays in small helpers:

- `OutputRunLayout`
- `sanitize_path_segment`
- `ensure_under_base`

The stores do not fetch URLs, parse HTML, retry requests, or update Job lifecycle state.

## Pattern 2. JSONL Writer

`JsonlWriter` owns newline-delimited JSON append.

Responsibilities:

- accept a Pydantic model or dict
- call `model_dump(mode="json")` for Pydantic models
- encode through stdlib `json.dumps(ensure_ascii=False)`
- append one newline
- flush after each record
- optionally call `fsync` when configured

It does not validate scraper business rules. Model validation remains in UOW-001 models.

## Pattern 3. Path Sanitization And Containment

`sanitize_path_segment(value, fallback)`:

- converts input to string
- keeps only `[A-Za-z0-9._-]`
- replaces all other characters with `_`
- strips leading/trailing unsafe separators
- returns `fallback` when the result is empty

`ensure_under_base(base, target)` resolves both paths and rejects targets outside `base`.

Use this for:

- `job_id`
- `run_id`
- `gallery_id`
- `post_no`
- `media_type`
- media filenames

## Pattern 4. Safe Failure Context

Failure context uses allow-list serialization.

Allowed fields:

- `site_id`
- `gallery_id`
- `post_id`
- `post_number`
- `url`
- `stage`
- `reason`
- `retryable`
- `http_status`
- `proxy_host`
- `user_agent`

Forbidden fields:

- proxy ID
- proxy password
- cookies
- tokens
- raw headers
- raw HTML/body/content
- credential file contents

Unknown fields are dropped by default.

## Pattern 5. Atomic JSON Writer

`AtomicJsonWriter` writes small single-document JSON files.

Flow:

1. create temp file in the target directory
2. write UTF-8 JSON
3. flush the file
4. replace the target with `os.replace`

Used for:

- `Checkpoint.json`
- `report.json`

Not used for:

- `posts.jsonl`
- `failures.jsonl`
- media files

## Pattern 6. S3 Optional Dependency Boundary

`S3ObjectStore` lazy-loads the S3 client dependency.

Rules:

- package import must succeed without S3 dependencies
- local storage tests must run without S3 dependencies
- S3 mode without the dependency raises a clear configuration error
- object keys mirror local relative paths
- Garage-specific APIs are not required

The first implementation should prefer a proven S3 client over custom signing.

## Pattern 7. Local Checkpoint Lock

`LocalCheckpointStore` uses one process-local lock around save/load mutation.

Scope:

- protects concurrent tasks in the same process
- does not claim multi-process safety
- keeps multi-process/container coordination for PostgreSQL checkpoint adapter

## Pattern 8. Test Organization

Default tests:

- `tests/test_outputs_storage.py`
- `tests/test_outputs_properties.py`
- `tests/strategies/outputs.py`

Optional smoke:

- `tests/test_outputs_s3_smoke.py`

Default pytest must not require Garage, S3 credentials, or external services.

## Pattern 9. Garage Smoke Guard

Garage/S3 smoke runs only when:

- `DCINSIDE_S3_SMOKE_ENABLED=true`
- endpoint env exists
- bucket env exists
- access key env exists
- secret key env exists

Smoke scope:

- put one small object
- get or head the object
- delete the object

It does not run a full scraper Job.

## Compliance Mapping

| Requirement Area | Design Pattern |
|---|---|
| append-only JSONL | `JsonlWriter` |
| atomic checkpoint/report | `AtomicJsonWriter` |
| path traversal prevention | `sanitize_path_segment`, `ensure_under_base` |
| failure redaction | safe failure context allow-list |
| local checkpoint concurrency | process-local lock |
| optional S3 dependency | lazy import in `S3ObjectStore` |
| deterministic tests | local example tests and PBT |
| optional external test | env-gated Garage smoke |
