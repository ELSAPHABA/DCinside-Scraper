# Logical Components - UOW-005 Job Runner And Checkpoint

## Component Overview

UOW-005 logical components orchestrate one scraper Job. They do not fetch HTTP directly, parse DCinside HTML directly, or implement concrete storage.

| Component | Purpose |
|---|---|
| `JobRunner` | owns one Job run lifecycle |
| `JobRunContext` | holds in-memory runtime state for a Job |
| `CandidateQueue` | wraps or directly uses `asyncio.Queue[PostCandidate]` plus private sentinel |
| `CollectorTask` | sequential producer of post candidates |
| `PostWorker` | bounded consumer that fetches/parses/stores one candidate at a time |
| `CheckpointCoordinator` | advances and saves checkpoint state |
| `ResumeCoordinator` | reconstructs a run from checkpoint state |
| `StopController` | tracks stop requests and maps stop reasons |
| `RealtimeLoopController` | owns realtime polling lifecycle |
| `RunnerEventBuilder` | creates safe structured event payloads |
| `tests/strategies/job_runner.py` | reusable Hypothesis strategies for pure runner state |

## JobRunner

Responsibilities:

- accept validated `JobConfig`
- create `JobRunContext`
- open one `anyio` task group
- start one collector task
- start configured worker tasks
- coordinate stop/fatal error flow
- finalize checkpoint and `JobReport`

Dependencies:

- UOW-003 collector contract
- UOW-004 post detail contract
- UOW-006 output/checkpoint ports
- logger and clock ports

## JobRunContext

Runtime state for one Job.

Fields:

- `job_id`
- `job_config`
- `queue`
- `completed_keys`
- `search_position`
- `processed_count`
- `success_count`
- `failure_count`
- `deduped_count`
- `filtered_count`
- `stop_requested`
- `stop_reason`
- `started_at`
- `finished_at`

The context is in-memory only. Persisted state belongs to `Checkpoint`.

## CandidateQueue

Queue item:

- `PostCandidate`

Internal-only item:

- private sentinel object

Responsibilities:

- apply optional `WorkerConfig.queue_max_size`
- allow collector backpressure when bounded
- provide sentinel shutdown for each worker
- keep Job objects out of the queue

## CollectorTask

Responsibilities:

- call the configured UOW-003 collection source
- preserve sequential traversal
- update in-memory `search_position`
- skip candidate enqueue after stop is requested
- enqueue worker sentinels on completion or stop path

Boundaries:

- does not fetch post detail
- does not write output
- does not advance completed checkpoint keys

## PostWorker

Responsibilities:

- read one candidate at a time
- exit on sentinel
- skip candidates already in `completed_keys`
- build UOW-004 post detail request
- write successful `PostResult`
- write final per-post `FailureRecord`
- notify `CheckpointCoordinator` only after storage success
- signal Job-level stop on CAPTCHA/block/storage failure

## CheckpointCoordinator

Responsibilities:

- own checkpoint draft
- restore completed keys into runtime state
- advance completed state after storage success
- save every 10 completed outcomes
- save final checkpoint on terminal paths

Terminal paths:

- normal completion
- manual stop
- cancellation
- CAPTCHA/block
- unrecoverable error
- timeout
- realtime timer/end-at completion

## ResumeCoordinator

Responsibilities:

- load checkpoint by explicit `job_id` or latest
- restore `job_config_snapshot`
- restore `search_position`
- restore `completed_keys`
- restore `remaining_queue` when available
- start a new output run through UOW-006 rules

If queue snapshot is missing, resume relies on re-traversal plus completed-key skip.

## StopController

Responsibilities:

- track whether stop is requested
- store stop reason
- prevent collector from adding new work
- map fatal conditions to checkpoint status/reason
- support graceful current-candidate finish

Stop reasons include:

- `manual_stop`
- `captcha`
- `error`
- timeout/realtime completion mapping through final checkpoint status

## RealtimeLoopController

Responsibilities:

- run UOW-003 latest collection cycle repeatedly
- evaluate `duration_seconds` or `end_at`
- dedupe already seen/completed keys
- avoid busy loop when no candidate exists
- trigger completed final checkpoint on normal realtime termination

## RunnerEventBuilder

Responsibilities:

- build safe event payloads
- allow-list fields
- drop unknown exception context
- keep credentials and raw response data out of logger calls

Events:

- job start/end
- collector cycle
- candidate queued
- candidate skipped
- worker success/failure
- checkpoint saved
- stop requested
- realtime termination

## Test Components

### `tests/test_job_runner.py`

Covers:

- normal fake Job completion
- bounded worker consumption
- completed-key skip
- checkpoint save interval
- checkpoint not advanced after storage failure
- manual stop
- CAPTCHA/block stop
- recoverable per-post failure
- resume dedupe
- realtime termination

### `tests/test_job_runner_properties.py`

Covers pure state properties:

- checkpoint advancement invariant
- completed-key skip/idempotence
- report counter consistency
- stop reason mapping
- realtime termination condition validation

### `tests/strategies/job_runner.py`

Provides strategies for:

- post keys
- outcome sequences
- stop reasons
- completed-key sets
- simple checkpoint state
- realtime termination inputs

## Component Boundaries

- UOW-002 owns HTTP retry, rate limiting, proxy, User-Agent, CAPTCHA/block classification.
- UOW-003 owns candidate discovery and search traversal primitives.
- UOW-004 owns post detail parsing and partial detail failure shape.
- UOW-006 owns output and checkpoint persistence implementations.
- UOW-005 owns orchestration order, concurrency, stop flow, and checkpoint timing.
- A separate DLQ/retry scheduler is not part of UOW-005; future retry units may consume `failures.jsonl`.
