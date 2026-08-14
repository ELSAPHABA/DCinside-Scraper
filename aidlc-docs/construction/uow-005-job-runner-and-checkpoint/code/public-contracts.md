# Public Contracts - UOW-005 Job Runner And Checkpoint

## Package Exports

UOW-005 adds import-safe runner components under:

```python
dcinside_scraper.runner
```

Root package exports were also updated for common runner classes:

- `JobRunner`
- `MediaDownloadCoordinator`
- `CheckpointCoordinator`
- `StopController`
- `RunnerEventBuilder`

## JobRunner

```python
from dcinside_scraper.runner import JobRunner

runner = JobRunner(
    collector=collector,
    post_detail=post_detail,
    output_store=output_store,
    failure_store=failure_store,
    media_store=media_store,
    http=http_client,
    checkpoint_store=checkpoint_store,
    logger=logger,
    clock=clock,
)

report = await runner.run(job_config)
```

Contract:

- receives a validated `JobConfig`
- runs one sequential collector task
- runs `WorkerConfig.post_worker_count` post workers
- limits media downloads with `WorkerConfig.media_worker_count`
- uses `asyncio.Queue[PostCandidate]`
- manages task lifecycle with `anyio`
- processes `PostResult.images` through `MediaStorePort` before JSONL append
- writes post results through `OutputStorePort`
- writes per-post failures through `FailureStorePort`
- advances checkpoints only after output/failure storage succeeds
- saves final checkpoints on terminal paths
- returns `JobReport`

## Resume

```python
from dcinside_scraper.models.job import ResumeRequest

report = await runner.resume(ResumeRequest(job_id="job-1"))
```

Contract:

- loads explicit checkpoint by `job_id`, or latest checkpoint when omitted
- restores `job_config_snapshot`
- restores completed keys
- restores remaining queue when available
- skips completed candidates before post processing
- writes to the injected output store for the new run

## Public API Delegation

```python
from dcinside_scraper.core.api import run_job, resume_job

report = await run_job(
    job_config,
    collector=collector,
    post_detail=post_detail,
    output_store=output_store,
    failure_store=failure_store,
    media_store=media_store,
    http=http_client,
    checkpoint_store=checkpoint_store,
)
```

`run_job` and `resume_job` can also receive a prebuilt `runner`.

If runner dependencies are missing, they raise `ValidationFailure` with `reason="runner_dependencies_required"`.

## Stop Request

```python
runner.request_stop()
```

Contract:

- requests graceful manual stop
- prevents new candidate processing when observed
- lets already-started storage finish on the normal stop path
- saves a final stopped checkpoint with `reason="manual_stop"`

## Error Boundaries

Job-level stop:

- CAPTCHA
- blocked response
- storage failure
- checkpoint failure
- unexpected runner/worker error

Per-post failure:

- `ScraperError` from post detail that is not CAPTCHA/block/storage/checkpoint

Per-post failures are stored as `FailureRecord` and do not require a separate DLQ in UOW-005.

## Pure Helpers

The runner package exposes small pure helpers used by tests:

- `candidate_post_key`
- `post_key_identity`
- `should_skip_candidate`
- `stop_reason_for_error`
- `report_status_for_checkpoint`

## Boundaries

UOW-005 does not:

- read `.env`
- parse CLI input
- create HTTP clients
- implement local/S3 storage
- implement PostgreSQL checkpoint storage
- provision containers
- implement distributed queue or DLQ scheduling
- host MCP tools
