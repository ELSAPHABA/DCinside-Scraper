# Deployment Architecture - UOW-006 Output And Storage

## Architecture Classification

UOW-006 has no standalone deployed runtime architecture.

It is a storage package layer consumed by later runtime units.

```text
Developer, tests, or later JobRunner
    |
    v
UOW-006 storage package
    |
    +-- LocalOutputStore
    +-- LocalMediaStore
    +-- LocalCheckpointStore
    +-- JsonlWriter
    +-- AtomicJsonWriter
    +-- OutputRunLayout/path helpers
    +-- optional S3ObjectStore
    |
    +--> local filesystem
    |
    +--> optional S3-compatible object store
```

## Environment Topology

| Environment | UOW-006 Role | Infrastructure |
|---|---|---|
| Local development | write test/local outputs under configured base path | local filesystem |
| CI | run local storage and PBT tests | CI filesystem temp dirs |
| Runtime scraper | imported by JobRunner/CLI/container units | local filesystem or configured S3-compatible endpoint |
| Optional Garage smoke | verify S3-compatible put/head/delete | external Garage/S3 endpoint supplied by env |

## Runtime Boundaries

UOW-006 import must not:

- read `.env`
- read docker environment variables
- open S3 connections
- create output directories
- create `Checkpoint.json`
- write files
- start a scraper Job

At explicit runtime calls, UOW-006 may:

- create local output directories
- append JSONL records
- write report JSON
- save media bytes
- save/load local checkpoints
- put objects through a configured S3-compatible client

## Local Deployment Shape

Default local shape:

```text
working-directory/
  outputs/
    <job_id>/
      <run_id>/
        posts.jsonl
        failures.jsonl
        report.json
        media/
  Checkpoint.json
```

When `StorageConfig.base_output_path` is set, replace `working-directory` with that configured path.

The value is supplied by the caller as configuration. It may later be derived from CLI arguments or environment variables by adapter code, but UOW-006 does not read those sources directly.

## S3-Compatible Deployment Shape

Object store shape:

```text
s3://<bucket>/<prefix>/outputs/<job_id>/<run_id>/posts.jsonl
s3://<bucket>/<prefix>/outputs/<job_id>/<run_id>/failures.jsonl
s3://<bucket>/<prefix>/outputs/<job_id>/<run_id>/report.json
s3://<bucket>/<prefix>/outputs/<job_id>/<run_id>/media/...
```

If `prefix` is not configured:

```text
s3://<bucket>/outputs/<job_id>/<run_id>/...
```

Garage is the intended default object store for container deployment, but the UOW-006 component depends only on S3-compatible semantics.

## External Services

| Service Type | Status | Reason |
|---|---|---|
| Local filesystem | Required for local mode | local JSONL, report, media, and checkpoint files |
| S3-compatible object store | Optional | Garage/SeaweedFS-compatible output target |
| Garage server | Deferred provisioning | actual deployment belongs to UOW-008 |
| PostgreSQL | Deferred | container checkpoint adapter belongs to UOW-008 |
| DCinside HTTP | Not used by UOW-006 | HTTP download belongs to UOW-002/UOW-005 |
| Queue/scheduler | Deferred | worker orchestration belongs to UOW-005/UOW-008 |
| Monitoring backend | Deferred | deployed observability belongs to later runtime work |

## Dependency Flow

```text
StorageConfig
    |
    +-- base_output_path -> LocalOutputStore / LocalMediaStore / LocalCheckpointStore
    |
    +-- s3 config -> S3ObjectStore

PostResult -> OutputStorePort.append_post -> posts.jsonl or S3 object
FailureRecord -> OutputStorePort.write_failure -> failures.jsonl or S3 object
JobReport -> OutputStorePort.finalize -> report.json or S3 object
MediaItem + bytes -> MediaStorePort.save_media -> local path or S3 object key
Checkpoint -> CheckpointStorePort.save -> Checkpoint.json
```

Checkpoint commit ordering is owned by UOW-005. UOW-006 only confirms whether storage succeeded.

## Test Architecture

Default test path:

```text
pytest / Hypothesis
    |
    +-- tmp_path local filesystem
    +-- fake sample PostResult/FailureRecord/Checkpoint
    +-- path/key/redaction strategies
    |
    v
deterministic local storage and pure transform tests
```

Optional S3 smoke path:

```text
DCINSIDE_S3_SMOKE_ENABLED=true
S3 env values present
    |
    v
marked smoke test
    |
    v
put/head/delete one small object
```

Optional smoke is not a default CI gate.

## Security Boundary

The deployment boundary for UOW-006 is the caller process plus configured storage backend.

Required behavior:

- sanitize path segments
- verify local path containment
- do not write proxy credentials
- do not write S3 credentials
- do not write cookies or tokens
- drop raw headers and raw body/html from failure context
- keep generated runtime files out of git

## Infrastructure Handoff

UOW-006 hands off storage capability to later units:

- local output store
- local media store
- local checkpoint store
- optional S3 object store
- path/key generation rules
- safe failure storage behavior

Later units decide:

- JobRunner checkpoint commit timing
- output base path CLI/env mapping
- image/dccon download selection
- PostgreSQL checkpoint adapter
- Garage container provisioning
- worker container environment variables
- MCP storage-facing commands
- deployed monitoring
