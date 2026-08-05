# Logical Components - UOW-001 Core Models And Config

## Component Overview

UOW-001 logical components define shared contracts used by later runtime, parser, storage, CLI, container, and MCP units.

| Component | Purpose |
|---|---|
| `StrictBaseModel` | common Pydantic v2 configuration |
| `MetadataValidator` | reusable metadata depth/type/size validation |
| `JobConfigValidator` | raw adapter input to validated JobConfig |
| `ErrorMapper` | typed exception to ErrorResult mapping |
| `SecretRedactor` | allowlist-based safe details redaction |
| `SchemaRegistry` | persisted schema registration |
| `SchemaSnapshot` | generated schema snapshot representation |
| `SchemaDiffChecker` | compatibility check between schema snapshots |
| `MigrationRegistry` | version transition and migration note registry |
| `DomainStrategies` | reusable Hypothesis strategies for model tests |
| `SmokeBenchmark` | optional model validation/serialization timing |
| `Ports` | protocol definitions for external dependencies |

## StrictBaseModel

Responsibilities:

- set `extra="forbid"`
- provide JSON serialization convention
- centralize shared model config

Consumers:

- all request models
- all result models
- all checkpoint/report models

## MetadataValidator

Responsibilities:

- validate metadata is JSON-compatible
- enforce maximum depth
- enforce serialized byte size
- reject unsafe Python objects

Inputs:

- `metadata: dict[str, Any]`
- `max_depth`
- `max_bytes`

Output:

- normalized metadata dict

Used by:

- model validators on every model with `metadata`

## JobConfigValidator

Responsibilities:

- convert CLI/env/MCP/library raw input into `JobConfig`
- enforce adapter-level input normalization
- delegate local model invariants to Pydantic
- return typed validation errors with field paths

It does not:

- perform network checks
- test if a DCinside URL currently exists
- create output directories
- load proxy or user-agent files at import time

## ErrorMapper

Responsibilities:

- map typed exceptions to stable error codes
- create user-safe messages
- attach candidate safe details
- mark retryability

Example exception mappings:

| Exception | Error Code | Retryable |
|---|---|---|
| `ValidationFailure` | `validation_error` | false |
| `UnsupportedSourceError` | `unsupported_source` | false |
| `CaptchaDetectedError` | `captcha_detected` | true |
| `BlockedResponseError` | `blocked_response` | true |
| `ParseFailureError` | `parse_failure` | false |
| `StorageFailureError` | `storage_failure` | true |

## SecretRedactor

Responsibilities:

- drop raw input values by default
- allow only known-safe detail keys
- redact secret-like keys by name
- redact secret-like string values by pattern when possible

Default allowlist:

- `field_path`
- `reason`
- `stage`
- `source_type`
- `retryable`
- `schema_version`

## SchemaRegistry

Responsibilities:

- register persisted top-level schemas
- map schema names to current versions
- expose schema metadata for snapshot generation

Initial registry entries:

- `dcinside.post.v1`
- `dcinside.checkpoint.v1`
- `dcinside.job_report.v1`

## SchemaSnapshot

Responsibilities:

- store generated schema structure
- store schema version
- store model name
- store stable hash for comparison

Persistence:

- committed fixture under tests or schema snapshot directory during code generation

## SchemaDiffChecker

Responsibilities:

- compare current schema snapshot to committed snapshot
- classify changes
- fail on same-major breaking changes
- report migration-note-required changes

Change classes:

- compatible
- migration_note_required
- breaking

## MigrationRegistry

Responsibilities:

- record version transitions
- link schema changes to migration notes
- provide a lookup for future normalizer/migration work

First implementation limit:

- no full persisted data migration runner
- no automatic JSONL rewrite
- no checkpoint auto-upgrade beyond explicitly implemented version transitions

## DomainStrategies

Responsibilities:

- provide reusable Hypothesis strategies
- generate structurally valid domain models
- include boundary values
- preserve business constraints

Strategy modules:

- `tests/strategies/job_configs.py`
- `tests/strategies/post_results.py`
- `tests/strategies/content_blocks.py`
- `tests/strategies/checkpoints.py`
- `tests/strategies/errors.py`

## SmokeBenchmark

Responsibilities:

- validate representative model payloads
- serialize representative model payloads
- report elapsed time for local inspection

Rules:

- not a CI gate in UOW-001
- may become a thresholded integration guard after UOW-004/UOW-005

## Ports

### HttpPort

Defines async HTTP call contract for later runtime unit.

Methods:

- `get`
- `post`
- `download`
- `close`

### OutputStorePort

Defines async result output contract.

Methods:

- `append_post`
- `write_failure`
- `finalize`

### MediaStorePort

Defines async media save contract.

Methods:

- `save_media`
- `save_metadata_only`

### CheckpointStorePort

Defines async checkpoint persistence contract.

Methods:

- `save`
- `load`
- `load_latest`

### ClockPort

Defines time source contract.

Methods:

- `now_utc`

### LoggerPort

Defines structured logging contract.

Methods:

- `debug`
- `info`
- `warning`
- `error`

## Interaction Flows

### Validation Flow

1. Adapter receives raw input.
2. Adapter passes raw input to `JobConfigValidator`.
3. `JobConfigValidator` normalizes raw input.
4. Pydantic models enforce field/model invariants.
5. Validated `JobConfig` is passed to later units.

### Error Flow

1. Core component raises typed exception.
2. Adapter catches exception.
3. `ErrorMapper` creates candidate `ErrorResult`.
4. `SecretRedactor` filters details.
5. Adapter returns or prints safe error.

### Schema Compatibility Flow

1. Code generation creates Pydantic model.
2. `SchemaRegistry` registers persisted model.
3. `SchemaSnapshot` captures current structure.
4. `SchemaDiffChecker` compares against committed snapshot.
5. `MigrationRegistry` verifies migration note for breaking or enum changes.

### PBT Flow

1. `DomainStrategies` generates valid model inputs.
2. PBT executes round trip or invariant property.
3. Hypothesis shrinks failures.
4. Failing seed and minimal counterexample are logged by test runner.

