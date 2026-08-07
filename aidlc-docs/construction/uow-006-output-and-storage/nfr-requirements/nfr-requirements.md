# NFR Requirements - UOW-006 Output And Storage

## Scope

This document defines non-functional requirements for `UOW-006 Output And Storage`.

In scope:

- Job JSONL output
- failure JSONL output
- final Job report output
- local media storage
- S3-compatible object storage boundary
- Garage default object storage target
- local `Checkpoint.json` persistence

Out of scope:

- worker queue lifecycle
- retry scheduling
- HTTP media download
- PostgreSQL checkpoint adapter
- CLI prompt UX
- container/MCP hosting

## Confirmed Questionnaire Decisions

| Question | Answer | Decision |
|---|---|---|
| Q1 | A | JSONL appends flush after each record; OS-level fsync is optional and disabled by default. |
| Q2 | A | `Checkpoint.json` and `report.json` use temp-file replace; JSONL remains append-only and recoverable by line validation. |
| Q3 | A | All path segments from user or remote input are allow-list sanitized, and resolved local paths must remain under the base output directory. |
| Q4 | A | Failure redaction uses allow-list fields only: safe post key, stage, retryable, status code, proxy host, and user-agent. |
| Q5 | A | S3-compatible upload dependency is optional extra, not core dependency; use a proven S3 client instead of hand-written signing. |
| Q6 | A | Local checkpoint concurrency targets single process/single Job writes with process-local locking and atomic replace. |
| Q7 | A | Default tests cover local storage, JSONL round trip, media save, checkpoint load/save/latest, traversal rejection, redaction, and S3 key generation. |
| Q8 | A | PBT targets pure storage transforms: path sanitize, object key generation, JSONL round trip, checkpoint document round trip, and redaction idempotence. |

No follow-up question is required. The answers are internally consistent.

## Performance Requirements

### NFR-UOW006-PERF-001. Append-Only JSONL

Post and failure outputs must append one line at a time.

The implementation must not rewrite the whole JSONL file per record.

### NFR-UOW006-PERF-002. Default Flush Policy

Each JSONL append must flush Python/user-space buffers after the record is written.

OS-level `fsync` must be available as an option but disabled by default.

### NFR-UOW006-PERF-003. Bounded Local Checkpoint Size

`Checkpoint.json` stores only the latest checkpoint per `job_id`.

It must not store historical checkpoint snapshots for every update.

## Reliability And Resiliency Requirements

### NFR-UOW006-REL-001. Atomic Single-Document Writes

`Checkpoint.json` and `report.json` must be written through:

1. write temp file in the same directory
2. flush file content
3. replace target file atomically

### NFR-UOW006-REL-002. JSONL Recovery Boundary

JSONL files are append-only.

If a process stops during append, later recovery may ignore the final invalid partial line. UOW-006 does not rewrite the full file to repair it.

### NFR-UOW006-REL-003. Resume-Safe Output Layout

Resume must use the same `job_id` and a new `run_id`.

The resumed run must write to a new run directory and must not append to the previous run's `posts.jsonl` or `failures.jsonl`.

### NFR-UOW006-REL-004. Storage Error Propagation

Local write, serialization, media write, checkpoint write, and S3 upload failures must be surfaced as typed storage errors with safe details.

The storage layer must not silently drop failed writes.

### NFR-UOW006-REL-005. Local Checkpoint Concurrency Boundary

Local checkpoint writes must be protected by a process-local lock.

Multi-process checkpoint concurrency is out of scope for local mode and belongs to the PostgreSQL checkpoint adapter.

## Security Requirements

### NFR-UOW006-SEC-001. Path Traversal Prevention

Every user or remote input used in a local path segment must be sanitized with an allow-list rule.

After joining paths, the resolved path must be verified to stay under the configured output base directory.

### NFR-UOW006-SEC-002. Safe Failure Context

Failure output may contain:

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

Failure output must not contain:

- proxy ID
- proxy password
- cookies
- tokens
- raw headers
- raw HTML/body/content
- credential file contents

### NFR-UOW006-SEC-003. Allow-List Redaction

Failure redaction must use allow-list serialization.

Unknown context fields must be dropped unless explicitly added to the safe list.

### NFR-UOW006-SEC-004. Credential-Free Storage Metadata

`StoredObjectRef`, `MediaItem.file_path`, `MediaItem.object_key`, JSONL records, and report files must not contain S3 credentials or proxy credentials.

### NFR-UOW006-SEC-005. Local Output Ignore Policy

Local runtime outputs must remain excluded from version control:

- `.env`
- `Checkpoint.json`
- `outputs/`
- downloaded media files
- generated object-store credentials

## Maintainability Requirements

### NFR-UOW006-MAINT-001. Port Boundary

All storage implementations must satisfy UOW-001 ports:

- `OutputStorePort`
- `MediaStorePort`
- `CheckpointStorePort`

Adapters and JobRunner code must depend on these ports, not concrete file/S3 implementations.

### NFR-UOW006-MAINT-002. Standard Library First

Local storage must use Python standard library primitives where sufficient:

- `json`
- `pathlib`
- `tempfile`
- `os.replace`
- process-local locks

### NFR-UOW006-MAINT-003. S3 Optional Dependency

S3-compatible storage dependencies must be optional and installed only when S3 output is used.

Core local JSONL/checkpoint usage must work without S3 client packages.

## Test Requirements

### NFR-UOW006-TEST-001. Default Test Gate

Default tests must cover:

- local `posts.jsonl` append
- local `failures.jsonl` append
- `report.json` atomic write
- JSONL round trip
- media bytes save
- metadata-only media save
- checkpoint save/load
- checkpoint `load_latest`
- path traversal rejection
- failure redaction
- S3 object key generation

### NFR-UOW006-TEST-002. Property-Based Tests

PBT must cover:

- path segment sanitization
- output key generation
- JSONL serialization round trip
- checkpoint document round trip
- failure redaction idempotence

### NFR-UOW006-TEST-003. Optional Garage Smoke

Actual Garage/S3-compatible integration test must be optional and env-gated.

It must not be part of default unit tests or mandatory local CI.

## Acceptance Criteria

- Local output writes one valid JSON object per line.
- Resume output uses a new `run_id` directory.
- `Checkpoint.json` can save/load multiple latest Job checkpoints.
- `load_latest()` returns the newest checkpoint.
- Unsafe local paths are rejected.
- Failure records omit credentials and raw response data.
- Media storage does not perform HTTP download.
- Core package still imports without S3 extra installed.
