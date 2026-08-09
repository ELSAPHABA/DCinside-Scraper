# Domain Entities - UOW-008 Container, MCP, And Test Harness

## ContainerCommand

Represents one container process invocation.

Fields:

- `argv`: command-line arguments passed to the container entrypoint
- `env`: process environment mapping
- `resume`: boolean derived from `RESUME`
- `job_id`: optional checkpoint job id

Rules:

- `resume=true` selects resume flow.
- `resume=false` selects new Job flow.
- Job source/options use UOW-007 command mapping where possible.

## ContainerRuntimeConfig

Container-only runtime settings derived from environment variables.

Fields:

- `database_url`
- `s3_endpoint_url`
- `s3_bucket`
- `s3_access_key_id`
- `s3_secret_access_key`
- `s3_region`
- `s3_force_path_style`
- `job_id`
- `resume`
- `realtime_env`

Rules:

- required storage fields must be present before container run/resume starts.
- secrets are stored in memory only and are not logged.
- realtime fields keep the same semantics as UOW-007.

## PostgresCheckpointStore

Checkpoint store implementation for container mode.

Methods:

- `save(checkpoint: Checkpoint) -> None`
- `load(job_id: str) -> Checkpoint | None`
- `load_latest() -> Checkpoint | None`

Storage table:

```text
dcinside_checkpoints(
  job_id text primary key,
  updated_at timestamptz not null,
  checkpoint_json jsonb not null
)
```

Rules:

- stored JSON validates as the shared `Checkpoint` model.
- `load_latest()` orders by `updated_at desc`.
- failed database operations surface as safe checkpoint/storage failures.

## S3OutputStore

Output store implementation for S3-compatible object storage.

Responsibilities:

- append post JSONL records
- append failure JSONL records
- upload final report JSON
- upload media bytes or metadata-only refs
- return `StoredObjectRef`

Key behavior:

- object keys follow the UOW-006 `OutputRunLayout` relative key rules.
- S3 object references use `s3://<bucket>/<key>`.
- credentials never appear in refs.
- JSONL append uses local spool plus upload.

## S3ContainerStorageConfig

Container storage configuration for S3-compatible output.

Fields:

- `endpoint_url`
- `bucket`
- `access_key_id`
- `secret_access_key`
- `region`
- `force_path_style`
- `prefix`

Rules:

- Garage is the default target.
- implementation must remain S3-compatible rather than Garage-specific.
- SeaweedFS remains a future compatible target.

## McpToolRequest

Validated MCP tool input wrapper.

Common fields:

- `tool_name`
- `arguments`
- `request_id`

Tool-specific models:

- gallery search request
- integrated search request
- post fetch request
- comment fetch request
- Job run command
- Job resume command

Rules:

- arguments validate through shared models or UOW-007 builder logic.
- invalid input maps to safe validation error payloads.

## McpToolResponse

JSON-serializable MCP tool response.

Fields:

- `ok`: boolean
- `result`: JSON value when successful
- `error`: safe error object when failed

Rules:

- success results use Pydantic `model_dump(mode="json")` style structures.
- failure payloads use `ErrorMapper`.
- no stack trace, raw env, raw HTTP body, cookie, token, or credential fields.

## QualityFixtureSet

Collection of deterministic fixtures used to validate output quality.

Includes:

- ordinary post JSONL fixture
- repost post JSONL fixture
- failure JSONL fixture
- Job report fixture
- optional malformed fixture

Checks:

- required top-level fields
- repost title normalization
- null/optional field representation
- report count consistency
- safe failure context
- optional Polars loading when enabled

## OptionalSmokeConfig

Configuration for opt-in smoke tests.

Fields:

- `docker_smoke_enabled`
- `garage_smoke_enabled`
- `postgres_smoke_enabled`
- `mcp_smoke_enabled`
- `live_dcinside_smoke_enabled`

Rules:

- default test run leaves all smoke flags disabled.
- smoke tests must skip cleanly when required env vars or services are missing.

## Entity Relationships

```text
ContainerCommand
  -> ContainerRuntimeConfig
  -> JobConfig or ResumeRequest
  -> JobRunner
  -> S3OutputStore
  -> PostgresCheckpointStore

McpToolRequest
  -> shared request model or Job builder
  -> core API
  -> McpToolResponse

QualityFixtureSet
  -> JSONL/report validators
  -> optional Polars load check
```

## Boundary Summary

- Container and MCP entities are adapters over existing core models.
- Storage entities implement existing output/checkpoint ports.
- Quality harness entities validate output compatibility and do not perform scraping.
