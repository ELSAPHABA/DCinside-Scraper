# NFR Design Patterns - UOW-005 Job Runner And Checkpoint

## Scope

This document translates UOW-005 NFR requirements into implementation patterns. It covers runner component layout, `anyio` task lifecycle, candidate queue shutdown, checkpoint coordination, resume reconstruction, error boundaries, safe events, test organization, and PBT state modeling.

## Confirmed Design Decisions

| Question | Answer | Design Decision |
|---|---|---|
| Q1 | A | Put runner components in a `runner` package and let public `run_job`/`resume_job` delegate to `JobRunner`. |
| Q2 | A | Open one `anyio` task group inside `JobRunner.run` and manage collector/workers through that group. |
| Q3 | A | Use a private sentinel per worker to end queue consumption after collector completion or stop. |
| Q4 | A | Centralize checkpoint draft, completed keys, save interval, and final save in `CheckpointCoordinator`. |
| Q5 | A | Rebuild resume state from checkpoint snapshot, search position, completed keys, and optional remaining queue. |
| Q6 | A | Classify Job-level and per-post errors in worker flow, then route stop decisions through runner state. |
| Q7 | A | Build safe structured events through a small allow-list event builder. |
| Q8 | A | Put async examples in `tests/test_job_runner.py`, PBT in `tests/test_job_runner_properties.py`, and strategies in `tests/strategies/job_runner.py`. |
| Q9 | A | Use pure state reducers for PBT instead of randomizing real async scheduling. |

No follow-up question is required.

## Pattern 1. Runner Package Boundary

UOW-005 implementation lives under a small `runner` package.

Primary components:

- `JobRunner`
- `JobRunContext`
- `CheckpointCoordinator`
- `StopController`
- `RealtimeLoopController`
- small event/state helpers

Public APIs such as `run_job` and `resume_job` delegate to `JobRunner`.

The runner package does not implement parser selectors, HTTP retry policy, concrete storage, CLI prompts, container entrypoints, or MCP tools.

## Pattern 2. AnyIO Task Group

`JobRunner.run` opens one `anyio` task group per Job run.

The task group owns:

- one sequential collector task
- `WorkerConfig.post_worker_count` worker tasks

Stop and fatal errors are routed through:

- `StopController`
- task group cancel scope when needed
- final checkpoint save before returning or raising through adapter mapping

The candidate queue remains `asyncio.Queue[PostCandidate]` according to the existing contract.

## Pattern 3. Queue Sentinel Shutdown

The queue transports post candidates.

Shutdown uses a private sentinel object that is never exposed as a public model.

Rules:

- collector enqueues candidates while stop is not requested
- collector enqueues one sentinel per worker when traversal completes
- stop path prevents new candidates and enqueues required sentinels
- workers exit when they receive sentinel
- workers call `queue.task_done()` for consumed items when used

The sentinel is an internal implementation detail, not a serialized value.

## Pattern 4. Checkpoint Coordinator

`CheckpointCoordinator` owns checkpoint state transitions.

Responsibilities:

- keep in-memory checkpoint draft
- keep `completed_keys`
- advance only after storage success
- count successful and final failed outcomes
- save every 10 completed outcomes
- save final checkpoint on terminal paths
- expose small pure helpers for PBT where possible

Workers do not directly mutate persisted checkpoints.

## Pattern 5. Resume Reconstruction

Resume starts from `CheckpointStorePort.load(job_id)` or `load_latest()`.

Restored values:

- `job_config_snapshot`
- `search_position`
- `completed_keys`
- `remaining_queue` when available
- counters when useful for report continuity

If `remaining_queue` is unavailable, the collector may re-traverse from checkpoint position and skip completed keys before processing.

The resumed run writes to a new UOW-006 output run.

## Pattern 6. Error Boundary

Worker flow classifies errors into two groups.

Job-level stop:

- CAPTCHA
- blocked response
- storage failure after result/failure write attempt
- unrecoverable runner error

Per-post failure:

- exhausted fetch failure that is not CAPTCHA/block
- parse failure that can be represented as `FailureRecord`
- optional detail failure after UOW-004 returns a partial result

Per-post failures are written through `FailureStorePort.write_failure` and do not require a separate DLQ in UOW-005.

Future retry work may read `failures.jsonl` and create a new retry Job.

## Pattern 7. Safe Runner Events

`RunnerEvent` or a small safe event builder creates allow-list logging payloads.

Allowed event fields:

- `job_id`
- `event`
- `stage`
- `gallery_id`
- `post_id`
- `post_number`
- `worker_id`
- `queued_count`
- `processed_count`
- `success_count`
- `failure_count`
- `stop_reason`
- `checkpoint_saved`

Forbidden fields:

- proxy ID/password
- cookies
- tokens
- raw headers
- raw HTML/body/content
- raw `.env` contents

Raw exception context dicts are not passed directly to the logger port.

## Pattern 8. Test Organization

Default tests:

- `tests/test_job_runner.py`
- `tests/test_job_runner_properties.py`
- `tests/strategies/job_runner.py`

Fakes stay local to the example test file while they remain small:

- fake collector
- fake post detail service
- fake output store
- fake checkpoint store
- fake logger
- fake clock when needed

No live DCinside, Garage, PostgreSQL, or proxy is required for default tests.

## Pattern 9. PBT State Reducers

PBT targets pure state behavior:

- checkpoint advancement after storage success
- completed-key skip/idempotence
- report counter consistency
- stop reason mapping
- realtime termination condition validation

Actual async task scheduling and cancellation timing are covered by focused example tests.

## Compliance Mapping

| Requirement Area | Design Pattern |
|---|---|
| worker concurrency bound | anyio task group plus fixed worker count |
| queue shutdown | private sentinel per worker |
| checkpoint-after-storage | `CheckpointCoordinator` |
| terminal final checkpoint | `CheckpointCoordinator` plus `StopController` |
| resume dedupe | resume reconstruction with completed keys |
| CAPTCHA/block fail-closed | error boundary and stop controller |
| safe observability | safe runner event builder |
| deterministic tests | fake services and pure PBT reducers |
