# Infrastructure Design - UOW-006 Output And Storage

## Scope

UOW-006 is not a deployable scraper worker. It defines importable storage implementations and storage boundaries used by later JobRunner, CLI, container, and MCP units.

In scope:

- local JSONL/report/media/checkpoint file layout
- local output base directory handling
- path sanitization and local path containment
- optional S3-compatible object key namespace
- optional Garage/S3 smoke test environment contract
- `.gitignore` protection expectations for local generated files

Out of scope:

- JobRunner orchestration
- HTTP media download
- PostgreSQL checkpoint adapter
- worker container and Garage provisioning
- CLI prompt UX
- MCP hosting

## Confirmed Decisions

| Area | Decision |
|---|---|
| Deployment environment | UOW-006 is an importable storage library, not a standalone service/container |
| Local output base | use `StorageConfig.base_output_path` when provided; otherwise use current working directory |
| Generated files | `outputs/`, `Checkpoint.json`, downloaded media, `.env`, and credential files must remain untracked |
| S3 runtime boundary | UOW-006 consumes validated `StorageConfig.s3` and injected credential/provider; it does not read `.env` or docker env directly |
| S3 namespace | mirror local layout as `<prefix>/outputs/<job_id>/<run_id>/...` |
| Local checkpoint | one `Checkpoint.json` under the base directory for single-process local execution |
| Garage smoke | env-gated only with all required S3 environment values present |
| Shared infrastructure | no shared infrastructure artifact for UOW-006; Garage/PostgreSQL/container compose is deferred to UOW-008 |

## Deployment Environment

UOW-006 has no standalone deployed runtime.

Required environment:

- Python package build/import environment
- local filesystem for local storage tests and local execution
- optional S3-compatible object store for smoke tests only

Not required:

- Docker image owned by UOW-006
- running scraper worker process
- PostgreSQL instance
- Garage provisioning
- queue or scheduler
- MCP server process
- monitoring backend

## Local Filesystem Boundary

`StorageConfig.base_output_path` is a configuration value, not an environment variable.

The caller may build it from CLI args, environment variables, or defaults in a later adapter unit, but UOW-006 receives the already-validated value.

Base directory rule:

- if `StorageConfig.base_output_path` exists, use it
- otherwise use current working directory

Local layout:

```text
<base_output_path>/
  outputs/
    <job_id>/
      <run_id>/
        posts.jsonl
        failures.jsonl
        report.json
        media/
          <gallery_id>/
            <post_no>/
              <media_type>/
                <filename>
  Checkpoint.json
```

Every generated local path must resolve under `<base_output_path>`.

## Version Control Boundary

UOW-006 can create local runtime files, but those files are runtime data and should not be committed.

Protected generated paths:

- `outputs/`
- `Checkpoint.json`
- downloaded media files
- `.env`
- S3 credential files

If `.gitignore` does not already cover these paths during code generation, UOW-006 code generation should add the minimal ignore entries.

## S3-Compatible Boundary

UOW-006 does not provision Garage or SeaweedFS.

It defines object write behavior against a configured S3-compatible endpoint.

Runtime input comes from:

- validated `StorageConfig.s3`
- caller-provided credential/provider object or equivalent runtime configuration

Runtime input does not come from:

- direct `.env` reads
- direct docker environment parsing
- checkpoint files
- output JSONL files

Object key layout:

```text
<prefix>/outputs/<job_id>/<run_id>/posts.jsonl
<prefix>/outputs/<job_id>/<run_id>/failures.jsonl
<prefix>/outputs/<job_id>/<run_id>/report.json
<prefix>/outputs/<job_id>/<run_id>/media/<gallery_id>/<post_no>/<media_type>/<filename>
```

When `prefix` is absent, keys start with `outputs/<job_id>/<run_id>/...`.

Garage is the default S3-compatible target. SeaweedFS remains a future replacement through the same S3-compatible boundary.

## Local Checkpoint Infrastructure

Local checkpoint mode uses:

```text
<base_output_path>/Checkpoint.json
```

Scope:

- single-process local execution
- multiple latest checkpoints keyed by `job_id`
- process-local lock
- atomic replace on save

Out of scope:

- multi-process file locking
- cross-container shared checkpoint state
- PostgreSQL checkpoint schema or migration

Container/shared checkpoint state is deferred to the PostgreSQL checkpoint adapter.

## Optional Garage Smoke Infrastructure

Default tests do not require Garage.

Garage/S3 smoke runs only when:

- `DCINSIDE_S3_SMOKE_ENABLED=true`
- S3 endpoint env exists
- bucket env exists
- access key env exists
- secret key env exists

Smoke scope:

- put one small object
- get or head the object
- delete the object

The smoke test does not run a full scraper Job.

## Monitoring Infrastructure

No external monitoring stack is defined for UOW-006.

UOW-006 should surface storage success/failure through returned values and typed exceptions. Later JobRunner/container units may log or export these events.

## Shared Infrastructure

No shared infrastructure artifact is created by UOW-006.

Deferred shared infrastructure:

| Infrastructure | Target Unit |
|---|---|
| Garage service provisioning | UOW-008 |
| PostgreSQL checkpoint adapter and schema | UOW-008 |
| worker container volume/env layout | UOW-008 |
| MCP server hosting | UOW-008 or later adapter unit |
| deployed monitoring | later deployed runtime |

## Implementation Impact

Code generation for UOW-006 may create:

- `outputs.local`
- `outputs.s3`
- JSONL writer helper
- atomic JSON writer helper
- path sanitization helpers
- local output/media/checkpoint stores
- optional S3 object store
- local storage tests
- storage PBT tests
- optional S3 smoke test

Code generation for UOW-006 should not create:

- Docker compose files
- Garage server config
- PostgreSQL migrations
- JobRunner queue orchestration
- CLI prompt handlers
- MCP tools
