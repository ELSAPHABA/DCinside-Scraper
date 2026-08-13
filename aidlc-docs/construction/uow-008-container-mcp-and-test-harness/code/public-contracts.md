# Public Contracts - UOW-008 Container, MCP, And Test Harness

## Container Entrypoint

```powershell
python -m dcinside_scraper.adapters.container run --source direct-post --url "https://gall.dcinside.com/board/view/?id=dcbest&no=1"
```

Docker entrypoint:

```text
ENTRYPOINT ["/app/docker-entrypoint.sh"]
```

Contract:

- `/app/docker-entrypoint.sh` is a thin Docker bootstrap script
- the script preserves argv and executes `python -m dcinside_scraper.adapters.container "$@"`
- importing `dcinside_scraper.adapters.container` has no runtime side effects
- `main(argv=None) -> int` returns `0`, `1`, or `2`
- container mode runs one Job or one resume request per process
- `RESUME=true` selects resume mode and uses `JOB_ID` when present
- new Jobs reuse UOW-007 CLI command parsing and `build_job_config`
- SIGINT/SIGTERM request graceful stop through `JobRunner.request_stop()`

## Container Environment

```python
from dcinside_scraper.adapters.container import ContainerEnvConfig

env_config = ContainerEnvConfig.from_env(env)
storage = env_config.storage_config()
```

Required env:

- `DATABASE_URL`
- `S3_ENDPOINT_URL`
- `S3_BUCKET`
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`

Optional env:

- `S3_REGION`
- `S3_FORCE_PATH_STYLE`
- `RESUME`
- `JOB_ID`
- `DCINSIDE_USER_AGENT_FILE`
- `DCINSIDE_USER_AGENT_ROTATE_EVERY`
- `DCINSIDE_PROXY_HOST`
- `DCINSIDE_PROXY_ID`
- `DCINSIDE_PROXY_PW`
- `DCINSIDE_REALTIME_*`

Contract:

- missing required env raises `ValidationFailure`
- invalid boolean/integer env raises `ValidationFailure`
- DSN, S3 keys, and proxy password are hidden from dataclass repr
- storage config maps to `OutputMode.S3` and `CheckpointMode.POSTGRES`

## Container Runtime Builder

```python
from dcinside_scraper.adapters.container import build_container_runtime

runtime = build_container_runtime(job_config, env_config)
```

Creates:

- `HttpClient`
- `LinkCollectorService`
- `PostDetailService`
- `S3OutputStore`
- `PostgresCheckpointStore`
- `JobRunner`

The builder accepts fake HTTP, S3, and PostgreSQL connection dependencies for tests.

## PostgreSQL Checkpoint Store

```python
from dcinside_scraper.outputs.postgres_checkpoint import PostgresCheckpointStore

store = PostgresCheckpointStore("postgresql://...")
await store.save(checkpoint)
checkpoint = await store.load("job-1")
latest = await store.load_latest()
```

Contract:

- implements `CheckpointStorePort`
- lazily imports `psycopg`
- wraps sync DB calls with `anyio.to_thread.run_sync`
- runs idempotent `CREATE TABLE IF NOT EXISTS`
- upserts by `job_id`
- stores full checkpoint JSON in `checkpoint_json`
- validates loaded JSON back into `Checkpoint`
- maps DB/load failures to `CheckpointFailureError`

## S3 Output Store

```python
from dcinside_scraper.outputs import OutputRunLayout, S3ObjectStore, S3OutputStore

layout = OutputRunLayout.create(job_id="job-1", run_id="run-1", prefix="prod")
object_store = S3ObjectStore(bucket="bucket", layout=layout, endpoint_url="http://garage:3900")
output_store = S3OutputStore(layout, object_store)
```

Contract:

- implements output-store behavior for posts, failures, and final report
- implements media-store behavior for bytes and metadata-only media
- appends JSONL to a process-local spool
- uploads the full JSONL object after each append
- returns only after durable S3-compatible upload succeeds
- sanitizes failure metadata before upload
- returns `StoredObjectRef` without credentials or signed URLs
- cleans spool directory best-effort after final report upload

## S3 Object Store

`S3ObjectStore.put_bytes()` now wraps blocking client upload calls with `anyio.to_thread.run_sync`.

It still supports injected fake clients for default tests and lazy `boto3` import for real S3/Garage usage.

## MCP Adapter

```python
from dcinside_scraper.adapters.mcp import McpToolHandlers

handlers = McpToolHandlers()
result = await handlers.resume_job({"job_id": "job-1"}, runner=fake_runner)
```

Tools:

- `search_gallery`
- `search_integrated`
- `fetch_post`
- `fetch_comments`
- `run_job`
- `resume_job`

Contract:

- importing `dcinside_scraper.adapters.mcp` does not import or start an MCP server
- tool handlers are async and testable without MCP runtime
- handlers return `{"ok": true, "data": ...}` or `{"ok": false, "error": ...}`
- success data is JSON-serializable
- errors use shared safe adapter payloads
- server binding lazily imports `mcp` only in `create_mcp_server()`
- default transport target is local stdio through the MCP runtime

## Safe Adapter Errors

```python
from dcinside_scraper.adapters.safe_errors import safe_error_payload
```

Contract:

- uses `ErrorMapper`
- returns JSON-safe dicts
- omits traceback and secret details
- shared by container and MCP adapters

## Docker Artifact

`Dockerfile` builds one worker image:

```text
python:3.11-slim
docker-entrypoint.sh
pip install .[s3,postgres]
ENTRYPOINT ["/app/docker-entrypoint.sh"]
```

`.dockerignore` excludes repository metadata, virtual environments, test caches, output/checkpoint files, `.env` secret candidates, docs, AI-DLC workflow artifacts, and build outputs from the Docker build context. The Dockerfile still copies only explicit runtime inputs.

No compose file is generated in UOW-008 code generation. Compose remains optional smoke/dev infrastructure only.

## Optional Extras

`pyproject.toml` optional extras:

- `s3`
- `postgres`
- `mcp`
- `analysis`
- `test`

Default install remains free of PostgreSQL, MCP, and Polars dependencies.

## Test Contracts

Default tests use:

- fake runner
- fake S3 client
- fake PostgreSQL connection/cursor
- fixture JSONL/report files
- optional Polars skip

Default tests do not require:

- Docker
- Garage
- PostgreSQL
- MCP runtime
- live DCinside network
- Polars
