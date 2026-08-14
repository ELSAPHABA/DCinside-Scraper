# Infrastructure Design - UOW-005 Job Runner And Checkpoint

## Scope

UOW-005 is not a standalone scraper service. It defines an importable in-process runner library that orchestrates one validated Job through injected ports from earlier units.

In scope:

- importable `JobRunner`
- in-process async worker orchestration
- `anyio` task group lifecycle
- `asyncio.Queue[PostCandidate]`
- injected UOW-002/UOW-003/UOW-004/UOW-006 ports
- checkpoint/output port usage
- safe event handoff through `LoggerPort`
- fake-service test infrastructure

Out of scope:

- CLI signal handling
- Docker worker container
- PostgreSQL checkpoint adapter
- Garage provisioning
- MCP hosting
- distributed worker queue
- live DCinside smoke infrastructure

## Confirmed Decisions

| Area | Decision |
|---|---|
| Deployment environment | UOW-005 is an importable runner library, not a standalone service/container |
| Worker execution | single Python process, `anyio` task group, `asyncio.Queue[PostCandidate]` |
| Configuration source | caller injects validated config and ports; UOW-005 does not read `.env`, CLI, or Docker env |
| Checkpoint infrastructure | UOW-005 calls `CheckpointStorePort` only |
| Output infrastructure | UOW-005 calls `OutputStorePort`, `FailureStorePort`, and `MediaStorePort` only |
| Observability | UOW-005 emits safe events through `LoggerPort` only |
| Test infrastructure | default tests use fake services only |
| Shared infrastructure | no shared infrastructure artifact for UOW-005 |

## Runtime Environment

Required runtime environment:

- Python package/import environment
- `anyio` runtime dependency
- existing validated model/config objects
- injected collector/detail/output/checkpoint/logger/clock ports

Not required:

- Docker image owned by UOW-005
- external queue service
- Redis/Celery/RQ
- PostgreSQL
- Garage/S3 endpoint
- MCP server
- telemetry backend

## Execution Boundary

UOW-005 runs inside the caller process.

Execution shape:

```text
Caller adapter or library user
    |
    v
Validated JobConfig + injected ports
    |
    v
JobRunner
    |
    +-- anyio task group
    |     +-- sequential collector task
    |     +-- post worker task 1..N
    |
    +-- asyncio.Queue[PostCandidate]
    +-- CheckpointCoordinator
    +-- StopController
    +-- RealtimeLoopController
```

Post worker concurrency is bounded by `WorkerConfig.post_worker_count`.

Media download concurrency inside post workers is bounded by `WorkerConfig.media_worker_count`.

The Job itself is not a queue item. Queue items are post candidates.

## Configuration Boundary

UOW-005 receives already-validated objects.

Inputs:

- `JobConfig`
- `WorkerConfig`
- UOW-003 collector service or port
- UOW-004 post detail service or port
- UOW-006 output, failure, media, and checkpoint ports
- UOW-002 HTTP port for media downloads when `image_mode=download`
- safe logger and clock ports

UOW-005 must not directly read:

- `.env`
- process environment variables
- Docker runtime environment
- terminal prompts
- config files

Those input sources belong to later CLI/container/MCP adapter units.

## Checkpoint Infrastructure Boundary

UOW-005 owns checkpoint timing, not checkpoint storage implementation.

UOW-005 calls:

- `CheckpointStorePort.save`
- `CheckpointStorePort.load`
- `CheckpointStorePort.load_latest`

UOW-005 does not implement:

- local `Checkpoint.json` persistence
- file locking
- PostgreSQL schema or migrations
- cross-container checkpoint sharing

Local checkpoint persistence is already covered by UOW-006. PostgreSQL checkpoint infrastructure is deferred to a later adapter/platform unit.

## Output Infrastructure Boundary

UOW-005 owns the order of output/checkpoint calls.

UOW-005 calls:

- `OutputStorePort.append_post`
- `FailureStorePort.write_failure`
- `OutputStorePort.finalize`

UOW-005 does not implement:

- `posts.jsonl`
- `failures.jsonl`
- `report.json`
- media path layout
- Garage/S3 upload

Concrete output storage is UOW-006 or later storage adapter responsibility.

## Observability Boundary

UOW-005 emits safe structured events through `LoggerPort`.

Allowed infrastructure dependency:

- injected logger port

Deferred infrastructure:

- OpenTelemetry exporters
- metrics backend
- log collector
- file log rotation
- alerting

The runner must not pass raw exception context, proxy credentials, cookies, headers, or raw HTML/body to logs.

## Test Infrastructure

Default tests use in-memory fakes:

- fake collector
- fake post detail service
- fake output store
- fake checkpoint store
- fake logger
- fake clock when time behavior matters

Default tests do not require:

- live DCinside network access
- Garage/S3
- PostgreSQL
- Docker Compose
- proxy credentials

This keeps UOW-005 tests focused on orchestration order and failure boundaries.

## Shared Infrastructure

No shared infrastructure artifact is created by UOW-005.

Deferred shared infrastructure:

| Infrastructure | Target Unit |
|---|---|
| CLI signal handling and prompt mapping | later CLI adapter |
| Docker worker container | later container/platform unit |
| Garage provisioning | later container/platform unit |
| PostgreSQL checkpoint adapter | later adapter/platform unit |
| distributed queue or DLQ scheduler | future retry/platform unit |
| MCP hosting | later MCP adapter |
| deployed observability | later deployed runtime |

## Implementation Impact

Code generation for UOW-005 may create:

- `runner` package
- `JobRunner`
- `JobRunContext`
- `CheckpointCoordinator`
- `StopController`
- `RealtimeLoopController`
- safe event helper
- test fakes
- runner example tests
- runner PBT tests

Code generation for UOW-005 should not create:

- Docker files
- Docker Compose files
- Garage config
- PostgreSQL migrations
- Celery/RQ/Redis queue setup
- CLI prompt handlers
- MCP tools
