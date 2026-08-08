# NFR Requirements - UOW-005 Job Runner And Checkpoint

## Scope

This document defines non-functional requirements for `UOW-005 Job Runner And Checkpoint`.

In scope:

- `JobRunner`
- sequential candidate collector task
- `asyncio.Queue[PostCandidate]`
- post worker pool
- checkpoint advancement
- resume flow
- manual stop and cancellation
- CAPTCHA/block stop
- realtime loop termination
- final `JobReport`

Out of scope:

- concrete local/S3 storage internals
- parser selectors
- HTTP retry policy internals
- PostgreSQL checkpoint adapter
- CLI prompt UX
- container/MCP hosting

## Confirmed Questionnaire Decisions

| Question | Answer | Decision |
|---|---|---|
| Q1 | B | Add `anyio` and use it for task group and cancellation scope management. |
| Q2 | A | Use `WorkerConfig.queue_max_size` when present; otherwise keep the existing unbounded queue contract. |
| Q3 | A | Save checkpoints every 10 completed posts and on every terminal path. |
| Q4 | A | Stop collector immediately, but let workers finish current candidate storage before shutdown. |
| Q5 | A | Save `remaining_queue` only when cheap; otherwise resume through `search_position` and `completed_keys`. |
| Q6 | A | Emit safe structured events only; exclude proxy credentials, cookies, raw headers, and raw HTML/body. |
| Q7 | A | CAPTCHA/block/storage failure stop the Job; final per-post fetch/parse failures become failure records. |
| Q8 | A | Default tests use fake collector/detail/output/checkpoint services; live DCinside and Garage/PostgreSQL are excluded. |
| Q9 | A | PBT targets pure state invariants, not randomized async scheduling. |

No follow-up question is required.

Q1 and Q2 are interpreted together: `anyio` owns task group and cancellation behavior, while the candidate queue contract remains `asyncio.Queue[PostCandidate]`.

## Performance Requirements

### NFR-UOW005-PERF-001. Sequential Link Collection

Each Job must run one sequential collector task.

The collector must not parallelize search traversal inside UOW-005.

### NFR-UOW005-PERF-002. Worker Count Bound

Concurrent post detail work must be bounded by `WorkerConfig.post_worker_count`.

The implementation must not create one task per discovered candidate without worker-count control.

### NFR-UOW005-PERF-003. Queue Backpressure

If `WorkerConfig.queue_max_size` is set, the candidate queue must be bounded and collector insertion must wait when the queue is full.

If it is not set, UOW-005 may use an unbounded queue according to the existing model contract.

### NFR-UOW005-PERF-004. Realtime Loop Wait

Realtime Jobs must wait between collection cycles using configured polling behavior from the Job configuration or later adapter defaults.

Realtime mode must not busy-loop when no new candidate exists.

## Reliability And Resiliency Requirements

### NFR-UOW005-REL-001. Checkpoint After Storage

Checkpoint completed state must advance only after `OutputStorePort.append_post` or `OutputStorePort.write_failure` succeeds.

Storage failure must leave checkpoint state at the previous committed position.

### NFR-UOW005-REL-002. Checkpoint Save Triggers

Checkpoint save is required:

- every 10 completed post outcomes
- on normal completion
- on manual stop
- on cancellation
- on CAPTCHA/block stop
- on unrecoverable Job error
- on timeout
- on realtime timer/end-at completion

### NFR-UOW005-REL-003. Graceful Stop

On stop request, the collector must stop adding new candidates.

Workers that already started a candidate should finish result or failure storage before shutdown when possible.

### NFR-UOW005-REL-004. Resume Dedupe

Resume must restore `completed_keys` and skip completed candidates before worker processing.

Resume must not append to an older UOW-006 output run.

### NFR-UOW005-REL-005. Optional Queue Snapshot

`remaining_queue` is optional.

If a complete queue snapshot is unavailable, resume must rely on `search_position` and `completed_keys`.

### NFR-UOW005-REL-006. Task Cleanup

`anyio` task groups or cancellation scopes must ensure collector and worker tasks are not leaked after Job completion, stop, or fatal error.

## Security Requirements

### NFR-UOW005-SEC-001. Safe Structured Events

JobRunner may log safe structured events for:

- job start/end
- collector cycle
- candidate queued/skipped
- worker success/failure
- checkpoint save
- stop reason
- realtime termination

### NFR-UOW005-SEC-002. Forbidden Event Data

JobRunner logs, reports, and failure handoff must not include:

- proxy ID
- proxy password
- cookies
- tokens
- raw headers
- raw HTML/body/content
- raw `.env` contents

### NFR-UOW005-SEC-003. CAPTCHA And Block Fail-Closed

CAPTCHA and blocked response errors from UOW-002 must stop the Job.

UOW-005 must not continue issuing new candidate requests after CAPTCHA/block detection.

## Maintainability Requirements

### NFR-UOW005-MAINT-001. Port Boundary

JobRunner must depend on injected services/ports from earlier units rather than concrete HTTP, parser, or storage implementations.

### NFR-UOW005-MAINT-002. AnyIO Boundary

`anyio` usage must stay inside runner lifecycle orchestration.

Model contracts and public data objects must not expose anyio-specific types.

### NFR-UOW005-MAINT-003. No External Worker Queue

UOW-005 must not introduce Celery, RQ, Redis queue, or database-backed distributed worker orchestration.

Those belong to later container/platform units if needed.

## Test Requirements

### NFR-UOW005-TEST-001. Default Test Gate

Default tests must use:

- fake collector
- fake post detail service
- fake output store
- fake checkpoint store
- fake clock when time behavior matters

Default tests must not require:

- live DCinside access
- Garage/S3
- PostgreSQL
- real proxy

### NFR-UOW005-TEST-002. Required Async Tests

Tests must cover:

- normal Job completion
- queue item skip from `completed_keys`
- checkpoint save every 10 completed outcomes
- checkpoint not advanced after storage failure
- manual stop final checkpoint
- CAPTCHA/block final checkpoint
- worker continues after recoverable per-post failure
- resume using completed-key dedupe
- realtime termination by configured condition

### NFR-UOW005-TEST-003. Property-Based Tests

PBT must cover:

- checkpoint advancement invariant
- completed-key skip/idempotence
- report counter consistency
- stop reason mapping
- realtime termination condition validation

PBT must not randomize real async scheduling or cancellation timing.

## Acceptance Criteria

- `JobRunner` can complete a fake Job and return a `JobReport`.
- Queue items are post candidates, not Jobs.
- Worker concurrency is bounded.
- Checkpoint state advances only after storage success.
- Final checkpoint is saved on every terminal path.
- Manual stop does not interrupt an already-started storage write in the normal stop path.
- Resume skips completed post keys.
- CAPTCHA/block stops new work.
- Core tests run without live network or external storage.
