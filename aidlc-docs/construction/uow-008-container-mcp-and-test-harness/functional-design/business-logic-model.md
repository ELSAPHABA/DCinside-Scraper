# Business Logic Model - UOW-008 Container, MCP, And Test Harness

## Purpose

UOW-008 provides the deployable adapter layer and validation harness around the existing scraper core.

This unit owns the one-shot worker container entrypoint, container environment mapping, PostgreSQL checkpoint store, S3-compatible output wiring for Garage, MCP tool adapter, and result quality test harness. It does not own scraping selectors, HTTP retry policy, post worker queue internals, CLI wizard UX, CAPTCHA bypass, GUI/Web UI, distributed scheduling, or production Kubernetes deployment.

## Confirmed Decisions

| Area | Decision |
|---|---|
| Container entrypoint | `dcinside_scraper.adapters.container.main()` called by Docker entrypoint |
| New container jobs | reuse UOW-007 CLI command shape and `build_job_config` path |
| Container resume | `RESUME=true` resumes by `JOB_ID` or latest PostgreSQL checkpoint |
| Environment source | storage/resume/realtime/proxy/user-agent settings come from environment variables or mounted files |
| Checkpoint storage | `PostgresCheckpointStore` stores full `Checkpoint` JSON in one table |
| S3/Garage output | add `S3OutputStore` using local spool plus durable object upload before reporting success |
| MCP tools | provide `search_gallery`, `search_integrated`, `fetch_post`, `fetch_comments`, `run_job`, `resume_job` |
| MCP execution | one-shot synchronous tool calls return JSON-serializable results |
| Error shape | adapters use `ErrorMapper`; no stack trace, raw env, raw body, or credentials in responses |
| Quality harness | fixture-based JSONL/report checks; Polars read checks are optional/test-extra gated |
| Default tests | fake clients, static fixtures, PBT, no required Docker/Garage/PostgreSQL/live network |
| Smoke tests | Docker compose, Garage, PostgreSQL, MCP server, and live DCinside checks are env-gated optional smoke tests |

## Container Flow

1. Docker entrypoint calls `dcinside_scraper.adapters.container.main(argv=None)`.
2. Container adapter reads storage and resume environment variables.
3. If `RESUME=true`, it builds `ResumeRequest(job_id=JOB_ID or None)`.
4. If `RESUME` is not true, it reuses the UOW-007 command normalization and `build_job_config` path to build `JobConfig`.
5. It builds container runtime dependencies:
   - `HttpClient`
   - `LinkCollectorService`
   - `PostDetailService`
   - `S3OutputStore`
   - `PostgresCheckpointStore`
   - `JobRunner`
6. It calls `core.api.run_job()` or `core.api.resume_job()`.
7. It writes structured logs to stdout/stderr.
8. It returns exit code `0` on completed report, `2` on validation errors, and `1` on runtime/stopped errors.

The container adapter must not parse DCinside HTML, collect links directly, write checkpoints manually, or implement a separate worker scheduler.

## Container Environment Flow

Required storage variables:

- `DATABASE_URL`
- `S3_ENDPOINT_URL`
- `S3_BUCKET`
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`

Optional variables:

- `S3_REGION`
- `S3_FORCE_PATH_STYLE`
- `RESUME`
- `JOB_ID`
- `DCINSIDE_REALTIME_ENABLED`
- `DCINSIDE_REALTIME_MODE`
- `DCINSIDE_REALTIME_KEYWORD`
- `DCINSIDE_REALTIME_DURATION_SECONDS`
- `DCINSIDE_REALTIME_END_AT`
- `DCINSIDE_REALTIME_POLL_INTERVAL_SECONDS`
- proxy/User-Agent variables or mounted `user-agents.txt`

Job-specific options should continue to use the UOW-007 argument shape where possible. Storage and container lifecycle settings stay in environment variables.

## PostgreSQL Checkpoint Flow

`PostgresCheckpointStore` implements the checkpoint port used by UOW-005.

Table:

```text
dcinside_checkpoints(
  job_id text primary key,
  updated_at timestamptz not null,
  checkpoint_json jsonb not null
)
```

Behavior:

1. `save(checkpoint)` upserts by `job_id`.
2. `load(job_id)` reads one checkpoint by primary key.
3. `load_latest()` returns the highest `updated_at` checkpoint.
4. Stored JSON is validated back into the shared `Checkpoint` model before returning.

The first implementation stores the full checkpoint document as JSON rather than normalizing every checkpoint field into separate columns.

## S3/Garage Output Flow

S3-compatible object storage is append-hostile. `S3OutputStore` therefore uses a local spool file as the working JSONL copy and uploads the full object after each append.

Flow for post/failure append:

1. Append one JSON line to local spool.
2. Upload the updated spool object to S3-compatible storage.
3. Return `StoredObjectRef` only after upload success.

Flow for report/media:

1. Serialize or receive bytes.
2. Upload the target object.
3. Return `StoredObjectRef` after upload success.

This keeps UOW-005's rule intact: checkpoint progress advances only after durable output storage succeeds.

## MCP Tool Flow

MCP tools are adapter wrappers over existing core APIs.

Tools:

- `search_gallery`
- `search_integrated`
- `fetch_post`
- `fetch_comments`
- `run_job`
- `resume_job`

Rules:

1. Validate tool input through shared models or UOW-007 builder functions.
2. Create runtime dependencies for the tool call.
3. Await the core API call.
4. Return `model_dump(mode="json")` style JSON-serializable results.
5. Map errors through `ErrorMapper`.

`run_job` and `resume_job` are one-shot calls in UOW-008. Background job registry, progress polling, cancellation tools, and distributed scheduling are deferred.

## Result Quality Harness Flow

The quality harness validates saved result shapes using small fixtures.

Checks:

- required top-level post fields
- consistent ordinary/repost post shape
- repost title has no `(펌)` marker
- optional/null fields remain representable
- report counts match fixture contents
- failure records contain safe reason fields only
- JSONL can be loaded line by line with stdlib JSON
- optional Polars read check runs only when Polars is installed or an analysis/test extra is enabled

The quality harness does not replace parser fixture tests from UOW-003/UOW-004. It verifies output compatibility and review readiness.

## Terminal And Adapter Error Flow

Container and MCP adapters use `ErrorMapper`.

Container:

- prints safe summary
- returns exit code `2` for validation errors
- returns exit code `1` for runtime/stopped errors
- returns exit code `0` for completed jobs

MCP:

- returns JSON-serializable error objects
- does not expose stack traces, proxy password, raw env, raw HTTP body, cookies, tokens, or raw headers

## Deferred Behavior

- Docker compose-based integration smoke
- live DCinside smoke
- production Kubernetes manifests
- background MCP job registry
- distributed queue and scheduler
- GUI/Web UI
- CAPTCHA bypass
