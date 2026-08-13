# Business Logic Model - UOW-005 Job Runner And Checkpoint

## Purpose

UOW-005 turns a validated `JobConfig` into a `JobReport` by orchestrating search/link collection, post detail fetching, optional media metadata/download processing, output storage, and checkpoint persistence.

This unit owns Job lifecycle, the post-candidate queue, worker pool execution, checkpoint update ordering, stop/cancellation behavior, resume flow, and realtime loop termination. It does not own CLI prompts, concrete storage internals, parser selectors, HTTP retry internals, PostgreSQL checkpoint implementation, container entrypoints, or MCP hosting.

## Confirmed Decisions

| Area | Decision |
|---|---|
| JobRunner contract | `JobRunner` receives validated `JobConfig` plus injected UOW-002/003/004/006 services or ports and returns `JobReport` |
| Queue topology | each Job has one sequential link collector task; queue items are `PostCandidate` values, not whole Jobs |
| Worker pool | `WorkerConfig.post_worker_count` post workers consume the candidate queue |
| Media processing | after UOW-004 parsing and before JSONL append, `MediaDownloadCoordinator` applies `ScrapeOptions.image_mode` and `WorkerConfig.media_worker_count` |
| Direct URL handling | direct URL Jobs convert URLs into `PostCandidate` values and put them into the same queue |
| Checkpoint commit ordering | completed keys and last completed position update only after result/failure storage succeeds |
| Checkpoint frequency | save every 10 completed posts and immediately on final stop/completion conditions |
| Manual stop | stop collector, stop adding new queue items, let active workers finish current post save, then save stopped checkpoint |
| CAPTCHA/block handling | CAPTCHA/block stops the Job immediately with final checkpoint; normal per-post failures become failure records |
| Resume | load selected/latest checkpoint, restore `job_config_snapshot`, `search_position`, `completed_keys`, and possible `remaining_queue` |
| Realtime | UOW-005 owns polling loop and termination; UOW-003 supplies one latest collection cycle |

## Job Run Flow

1. Caller creates a `JobRunner` with injected runtime services and storage ports.
2. Caller invokes `run(config)`.
3. `JobRunner` creates a `JobRunContext` with counters, completed key set, stop state, queue, and checkpoint draft.
4. A single collector task discovers `PostCandidate` values.
5. Collector pushes each candidate into `asyncio.Queue`.
6. Post workers consume candidates from the queue.
7. Each worker skips candidates already in `completed_keys`.
8. Each worker fetches/parses a post through UOW-004.
9. Each worker processes `PostResult.images` through the injected `MediaStorePort` when image metadata/download handling is required.
10. Each worker writes success or failure through UOW-006 output ports.
11. After storage success, checkpoint state is advanced.
12. `CheckpointScheduler` saves checkpoints every 10 completed posts.
13. On normal completion, final checkpoint and `JobReport` are written.

The queue contains post candidates/links. A Job is the outer run; it is not itself an item in the queue.

## Collector Flow

Collector behavior:

- runs one sequential task per Job
- handles direct URL, gallery search, integrated search, deep search, no-keyword range, realtime keyword, and realtime all sources through UOW-003 contracts
- applies UOW-003 dedupe/range behavior
- does not write output
- does not update completed checkpoint keys

For non-realtime Jobs, the collector completes when traversal completes or a stop condition is requested.

For realtime Jobs, `JobRunner` repeats latest collection cycles until `duration_seconds` or `end_at` is reached.

## Worker Flow

Each post worker:

1. reads one `PostCandidate` from the queue
2. skips it if the post key is already completed
3. builds `PostRequest`
4. fetches `PostResult` through UOW-004
5. processes `PostResult.images` through `MediaDownloadCoordinator`
6. writes the post result through `OutputStorePort.append_post`
7. advances checkpoint only after write success
8. records failure through `OutputStorePort.write_failure` when a post-level or media-level failure is recoverable

Worker count comes from `WorkerConfig.post_worker_count`.

Media download concurrency comes from `WorkerConfig.media_worker_count`.

Queue max size uses `WorkerConfig.queue_max_size` when present; otherwise the queue may be unbounded.

## Checkpoint Flow

Checkpoint state is updated after storage success only.

Successful post:

1. write `PostResult`
2. add `PostKey` to `completed_keys`
3. update last completed post ID/URL/board
4. increment processed count
5. save checkpoint if checkpoint interval is reached

Recoverable post failure:

1. write `FailureRecord`
2. add the post key to completed keys only when the failure is final for this run
3. update processed count
4. save checkpoint if checkpoint interval is reached

Storage failure does not advance checkpoint.

## Stop Flow

Manual stop or cancellation:

1. mark stop requested
2. stop collector from adding new candidates
3. allow active workers to finish current candidate storage
4. optionally snapshot remaining queue if available
5. save final checkpoint with `status="stopped"` and `reason="manual_stop"`
6. finalize `JobReport` as stopped

CAPTCHA/block:

1. stop collector and workers from starting new candidates
2. save final checkpoint with `status="stopped"`
3. use `reason="captcha"` for CAPTCHA
4. use `reason="error"` for block when no specific model reason exists
5. return or raise according to public API error mapping in later adapter layer

## Resume Flow

Resume uses `ResumeRequest`:

- if `job_id` is present, load that checkpoint
- otherwise load latest checkpoint

Restored values:

- `job_config_snapshot`
- `search_position`
- `completed_keys`
- `remaining_queue` when present
- counters and last completed fields

The resumed run writes to a new output run according to UOW-006. It does not append to an older JSONL run file.

## Realtime Flow

Realtime Jobs are lifecycle-managed by `JobRunner`.

Rules:

- `duration_seconds` or `end_at` is already validated by UOW-001
- exactly one termination condition exists
- `JobRunner` repeats UOW-003 latest collection cycle
- dedupe prevents already-seen posts from entering worker processing
- normal timer/end-at termination saves `status="completed"` final checkpoint
- manual stop/CAPTCHA/error uses stopped checkpoint rules

## Testable Properties

- queue items are `PostCandidate` values, not Jobs.
- checkpoint completed keys advance only after storage succeeds.
- storage failure does not move checkpoint forward.
- checkpoint save is triggered every 10 completed posts.
- final checkpoint is saved on manual stop, CAPTCHA/block, timeout, realtime completion, and normal completion.
- resume skips completed keys before worker processing.
- realtime loop stops at the configured termination condition.
