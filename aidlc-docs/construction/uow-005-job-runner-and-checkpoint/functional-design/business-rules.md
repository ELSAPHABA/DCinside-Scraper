# Business Rules - UOW-005 Job Runner And Checkpoint

## JobRunner Rules

- `JobRunner` must receive a validated `JobConfig`.
- `JobRunner` must use injected services/ports rather than creating concrete HTTP or storage dependencies itself.
- `JobRunner.run` returns one `JobReport`.
- Public adapters may call `JobRunner`, but adapter input parsing is not part of UOW-005.
- `run_job` and `resume_job` public APIs may delegate to `JobRunner` after UOW-005 implementation.

## Queue Rules

- Queue items are post candidates/links.
- A whole Job is not placed into the queue.
- Each Job has one candidate queue.
- Each Job has one sequential collector task.
- Post workers consume from the queue.
- Direct URL sources are converted into `PostCandidate` values before queue insertion.
- Completed post keys are skipped before processing.

## Collector Rules

- Link traversal remains sequential inside one Job.
- Search position and page state must be captured in checkpoint state when available.
- Collector must stop adding new candidates after stop is requested.
- Realtime collector execution is one cycle at a time; loop ownership belongs to `JobRunner`.

## Worker Rules

- Worker count comes from `WorkerConfig.post_worker_count`.
- Media download concurrency comes from `WorkerConfig.media_worker_count`.
- Workers may run post detail fetches concurrently.
- Workers must use UOW-004 post detail contracts.
- Workers must process `PostResult.images` after parsing and before `OutputStorePort.append_post`.
- `ScrapeOptions.image_mode=metadata_only` stores media metadata only; `download` downloads bytes through `HttpPort.download` and writes them through `MediaStorePort.save_media`.
- Workers must write success through `OutputStorePort.append_post`.
- Workers must write final per-post failures through `FailureStorePort.write_failure`.
- Workers must not update checkpoint completed state before output write success.

## Checkpoint Rules

- Checkpoint state advances only after storage success.
- Normal progress checkpoint save interval is 10 completed posts.
- Completed count includes successful posts and final per-post failures written to failure output.
- Storage failure leaves checkpoint at the previous committed position.
- Final checkpoint must be saved on normal completion.
- Final checkpoint must be saved on manual stop.
- Final checkpoint must be saved on CAPTCHA/block stop.
- Final checkpoint must be saved on timeout.
- Final checkpoint must be saved on realtime timer/end-at completion.

## Stop Rules

- Manual stop saves checkpoint with `status="stopped"` and `reason="manual_stop"`.
- Active workers should finish the current candidate storage before final stop when possible.
- Collector must stop producing new candidates after stop is requested.
- Remaining queue snapshot may be saved when cheaply available.
- Forced task cancellation without final checkpoint is not an acceptable normal stop path.

## Error Rules

- `CaptchaDetectedError` stops the Job.
- `BlockedResponseError` stops the Job.
- CAPTCHA stop uses `reason="captcha"`.
- Blocked response uses stopped checkpoint with safe error reason.
- Individual parse/fetch failures that are not CAPTCHA/block become failure records when retry is exhausted.
- Recoverable media download failures become `stage="media"` failure records for that candidate.
- A recoverable per-post failure must not stop the whole Job.
- Storage failure is fatal to checkpoint advancement for that candidate.

## Resume Rules

- Resume with explicit `job_id` loads that checkpoint.
- Resume without `job_id` loads latest checkpoint.
- Resume uses `job_config_snapshot`.
- Resume restores `completed_keys`.
- Resume restores `search_position` when present.
- Resume restores `remaining_queue` when present.
- Resume must not reprocess completed keys.
- Resume writes to a new UOW-006 output run.

## Realtime Rules

- Realtime loop belongs to `JobRunner`.
- UOW-003 supplies latest collection cycles.
- `duration_seconds` and `end_at` are mutually exclusive by UOW-001 validation.
- Normal realtime termination saves `status="completed"`.
- Realtime manual stop/error/CAPTCHA uses stopped checkpoint rules.

## Out Of Scope Rules

- UOW-005 does not implement concrete local/S3 storage internals.
- UOW-005 does not implement PostgreSQL checkpoint adapter.
- UOW-005 does not implement CLI prompts.
- UOW-005 does not provision Garage or containers.
- UOW-005 does not implement MCP tools.
- UOW-005 does not own parser selectors or HTTP retry internals.
