# Domain Entities - UOW-005 Job Runner And Checkpoint

## Existing Contract Entities

UOW-005 reuses existing contracts from earlier units.

| Entity | Source | Role |
|---|---|---|
| `JobConfig` | `models/job.py` | validated Job input |
| `WorkerConfig` | `models/job.py` | post worker count and queue max size |
| `PostCandidate` | `models/job.py` | queue item representing one post link/candidate |
| `PostKey` | `models/job.py` | completed-key identity for dedupe/resume |
| `SearchPosition` | `models/job.py` | traversal cursor saved in checkpoint |
| `ResumeRequest` | `models/job.py` | resume input |
| `PostRequest` | `models/job.py` | post detail request derived from candidate |
| `Checkpoint` | `models/checkpoint.py` | persisted Job lifecycle state |
| `PostResult` | `models/post.py` | successful worker output |
| `FailureRecord` | `models/report.py` | final per-post failure output |
| `JobReport` | `models/report.py` | final run summary |
| `HttpPort` | `core/ports.py` | UOW-002 HTTP runtime boundary |
| `OutputStorePort` | `core/ports.py` | result/failure/report output boundary |
| `CheckpointStorePort` | `core/ports.py` | checkpoint persistence boundary |
| `ClockPort` | `core/ports.py` | testable time source |
| `LoggerPort` | `core/ports.py` | safe logging boundary |

## New Logical Components

### JobRunner

Primary orchestration component.

Responsibilities:

- start a Job from `JobConfig`
- resume a Job from checkpoint
- own collector and worker task lifecycle
- own candidate queue
- coordinate output writes and checkpoint updates
- produce `JobReport`

### JobRunContext

In-memory state for one running Job.

Fields:

- `job_config`
- `job_id`
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

### CandidateQueue

`asyncio.Queue[PostCandidate]` wrapper or direct queue usage.

Rules:

- items are post candidates
- queue is scoped to one Job run
- max size comes from `WorkerConfig.queue_max_size`
- queue receives sentinel/shutdown signal when collector completes or stop is requested

### CollectorTask

Sequential producer for `PostCandidate` values.

Responsibilities:

- dispatch to UOW-003 collector for the configured source
- push candidates into queue
- update in-memory traversal/search position
- stop on requested cancellation

### PostWorker

Consumer task for one candidate at a time.

Responsibilities:

- skip already completed keys
- fetch `PostResult`
- write success output
- write failure output when appropriate
- notify checkpoint coordinator after storage success

### CheckpointCoordinator

Owns checkpoint draft and save decisions.

Responsibilities:

- advance checkpoint only after storage success
- save every 10 completed posts
- save final checkpoints
- restore completed keys/search position/remaining queue from checkpoint

### StopController

Tracks stop and cancellation intent.

Responsibilities:

- expose stop requested state
- map stop causes to checkpoint status/reason
- prevent collector from adding new work
- let active workers complete current item when possible

### RealtimeLoopController

Owns realtime polling lifecycle.

Responsibilities:

- repeat UOW-003 latest collection cycle
- evaluate `duration_seconds` or `end_at`
- avoid reprocessing seen/completed keys
- save completed checkpoint on normal realtime termination

## State Transitions

| From | Trigger | To |
|---|---|---|
| initialized | run starts | running |
| running | normal traversal complete and queue drained | completed |
| running | realtime timer/end-at reached | completed |
| running | manual stop/cancellation | stopped |
| running | CAPTCHA detected | stopped |
| running | blocked response detected | stopped |
| running | unrecoverable Job error | stopped |

## Checkpoint Mapping

| Runtime State | Checkpoint Field |
|---|---|
| Job identity | `job_id`, `site_id` |
| latest board/post | `board_id`, `last_completed_post_id`, `last_completed_url` |
| progress count | `scraping_processed_count` |
| lifecycle | `status`, `reason`, `retry_after` |
| source config | `job_config_snapshot` |
| traversal cursor | `search_position` |
| completed dedupe set | `completed_keys` |
| possible queue snapshot | `remaining_queue` |
| update time | `updated_at` |

## Report Mapping

`JobReport` is finalized from `JobRunContext`.

Fields:

- `job_id`
- `status`
- `success_count`
- `failure_count`
- `deduped_count`
- `filtered_count`
- `started_at`
- `finished_at`
- `failures`
- `output_refs`

## Entity Boundaries

- `JobRunner` owns orchestration, not scraping selectors.
- `PostWorker` owns candidate processing, not link traversal.
- `CheckpointCoordinator` owns checkpoint advancement, not file implementation.
- `OutputStorePort` owns writes, not checkpoint timing.
- `RealtimeLoopController` owns lifecycle loop, not UOW-003 parsing logic.
