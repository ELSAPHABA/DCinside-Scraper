# Business Rules - UOW-008 Container, MCP, And Test Harness

## Adapter Boundary Rules

- UOW-008 adapters must call existing core APIs and services.
- UOW-008 must not duplicate search traversal, post parsing, comment parsing, retry, rate limit, or worker queue logic.
- Container and MCP adapters must pass validated `JobConfig`, `ResumeRequest`, or request models into core APIs.
- Importing adapter modules must not start a Job, create files, connect to PostgreSQL, connect to S3, prompt a terminal, or perform HTTP requests.

## Container Entrypoint Rules

- Docker entrypoint must call `dcinside_scraper.adapters.container.main()`.
- Container mode runs one Job or one resume request per process invocation.
- New container Jobs reuse UOW-007 command normalization and `build_job_config` semantics where possible.
- Container-specific storage and lifecycle configuration is read from environment variables.
- Container stdout/stderr output must be structured enough for container logs.
- Container rollback is operationally handled by redeploying a previous Git tag or image.

## Container Resume Rules

- `RESUME=true` enables resume mode.
- In resume mode, `JOB_ID` is optional.
- If `JOB_ID` is present, resume that checkpoint.
- If `JOB_ID` is absent, resume the latest checkpoint from PostgreSQL.
- If `RESUME` is not true, run a new Job.
- Resume must restore the original Job config from checkpoint.
- Resume must create new output objects for the resumed run according to output store rules.

## Environment Variable Rules

- Container mode requires `DATABASE_URL` for PostgreSQL checkpoint storage.
- Container mode requires `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, and `S3_SECRET_ACCESS_KEY` for S3-compatible output storage.
- `S3_REGION` and `S3_FORCE_PATH_STYLE` are optional.
- `DCINSIDE_REALTIME_*` variables keep the same semantics as UOW-007.
- Proxy and User-Agent settings may come from environment variables or mounted files.
- Secret values must not be printed in logs, errors, reports, or MCP responses.
- Adapters must not call `load_dotenv()` as part of container environment loading.

## PostgreSQL Checkpoint Rules

- `PostgresCheckpointStore` must implement the existing checkpoint store port.
- Checkpoints are keyed by `job_id`.
- Checkpoint body is stored as validated JSON in `checkpoint_json`.
- `updated_at` is used for latest checkpoint selection.
- `save()` must upsert by `job_id`.
- `load()` must return `None` when a checkpoint does not exist.
- Loaded checkpoint JSON must validate through the shared `Checkpoint` model.
- Database connection errors are mapped to checkpoint/storage failure errors with safe details.

## S3/Garage Output Rules

- Container JSONL output and media output use S3-compatible object storage.
- Garage-specific APIs must not be required.
- SeaweedFS must remain possible later through the same S3-compatible boundary.
- `S3OutputStore.append_post()` and `write_failure()` must return only after durable object upload succeeds.
- Local spool files are implementation detail and must not define public output locations.
- Checkpoint progress must not advance until the output store reports success.
- S3 credential values must never appear in `StoredObjectRef`, logs, failures, or error details.

## MCP Tool Rules

- MCP exposes `search_gallery`, `search_integrated`, `fetch_post`, `fetch_comments`, `run_job`, and `resume_job`.
- Search/fetch tools call the existing public core API request functions.
- Job tools reuse existing `JobConfig` and `ResumeRequest` validation.
- MCP tool results must be JSON-serializable.
- MCP tool errors must be safe mapped error objects.
- MCP must not return Python traceback text to clients.
- UOW-008 MCP Job execution is one-shot and blocking for the tool call.
- Background job handles, progress polling, cancellation tools, and scheduling are out of scope.

## Result Quality Harness Rules

- Quality checks use small deterministic fixtures by default.
- JSONL fixture checks must verify required top-level fields.
- Repost fixtures must verify that `title` does not include `(펌)`.
- Ordinary and repost post fixtures must preserve the same top-level shape.
- Report fixture checks must validate success, failure, dedupe, and filtered counts.
- Failure fixtures must not include raw HTML, cookies, proxy credentials, tokens, raw headers, or raw env values.
- Polars checks are optional and must not make Polars a runtime dependency.

## Test Scope Rules

- Default tests must not require Docker, Garage, PostgreSQL, live DCinside, or a running MCP server.
- Default tests may use fakes, static fixtures, property-based strategies, temporary files, and mock ports.
- Docker compose, Garage, PostgreSQL, MCP server, and live DCinside smoke tests must be opt-in through environment variables or explicit test markers.
- Default tests must remain import-safe and deterministic.

## Error Rules

- Validation errors map to exit code `2` in container mode.
- Completed jobs map to exit code `0` in container mode.
- Stopped/runtime failures map to exit code `1` in container mode.
- MCP errors return JSON-safe error payloads.
- Error details must use allow-listed safe fields only.

## Out Of Scope Rules

- UOW-008 does not implement CAPTCHA solving or bypass.
- UOW-008 does not implement a distributed queue.
- UOW-008 does not implement production Kubernetes manifests.
- UOW-008 does not implement GUI/Web UI.
- UOW-008 does not redesign existing core APIs.
