# Code Generation Plan - UOW-001 Core Models And Config

이 문서는 `UOW-001 Core Models And Config` 코드 생성을 위한 단일 기준 계획입니다. 실제 코드 생성은 이 계획 승인 후 아래 순서대로만 진행합니다.

## Unit Context

- **Unit**: UOW-001 Core Models And Config
- **Project Type**: Greenfield Python package
- **Workspace Root**: `D:\HongDev\ELSAPHABA\DCinside-Scraper`
- **Code Location**: workspace root의 `src/`, `tests/`, `pyproject.toml`
- **Documentation Location**: `aidlc-docs/construction/uow-001-core-models-and-config/code/`
- **Primary Story**: US-017 Python 라이브러리 API를 제공한다
- **Supporting Role**: UOW-002 to UOW-008이 공유할 모델, 설정, 오류, schema, port 계약 제공

## Dependencies

| Dependency | Status |
|---|---|
| Prior unit dependency | None |
| Functional Design | Approved |
| NFR Requirements | Approved |
| NFR Design | Approved |
| Infrastructure Design | Approved |

## Scope

UOW-001 implements:

- Pydantic v2 strict base model
- enums and shared value models
- Job source, request, config, result, checkpoint, report, and error models
- metadata bounds validation
- typed core exceptions
- adapter-safe error mapping and secret redaction
- schema registry, snapshot, diff checker, and migration note registry
- port protocols
- import-safe public package exports
- example tests and property-based test strategies

UOW-001 does not implement:

- HTTP requests
- DCinside HTML parsing
- file/object/database storage
- worker queue runtime
- CLI command parsing
- container entrypoint
- MCP tools
- Docker, Terraform, or deployed infrastructure

## Expected Interfaces And Contracts

| Contract | Target Path |
|---|---|
| Package metadata | `pyproject.toml` |
| Public package exports | `src/dcinside_scraper/__init__.py` |
| Core API placeholder signatures | `src/dcinside_scraper/core/api.py` |
| Typed exceptions | `src/dcinside_scraper/core/errors.py` |
| Validation helpers | `src/dcinside_scraper/core/validation.py` |
| Port protocols | `src/dcinside_scraper/core/ports.py` |
| Schema compatibility helpers | `src/dcinside_scraper/core/schema.py` |
| Base model and enums | `src/dcinside_scraper/models/base.py`, `src/dcinside_scraper/models/enums.py` |
| Job/request/config models | `src/dcinside_scraper/models/job.py` |
| Content/media/comment/post models | `src/dcinside_scraper/models/content.py`, `src/dcinside_scraper/models/media.py`, `src/dcinside_scraper/models/comment.py`, `src/dcinside_scraper/models/post.py` |
| Checkpoint/report/error models | `src/dcinside_scraper/models/checkpoint.py`, `src/dcinside_scraper/models/report.py`, `src/dcinside_scraper/models/error.py` |

## Database Entities

No database entities or migration scripts are owned by UOW-001.

Persisted JSON-compatible contracts are:

- `PostResult`
- `Checkpoint`
- `JobReport`

Concrete PostgreSQL checkpoint storage is deferred to UOW-008.

## Step Sequence

### Step 1. Project Structure Setup

- [x] Create `pyproject.toml` with Python 3.11+, Pydantic v2 runtime dependency, and pytest/Hypothesis test dependencies.
- [x] Create `src/dcinside_scraper/` package directories: `core/`, `models/`.
- [x] Create `tests/` and `tests/strategies/`.
- [x] Create empty package marker files where needed.

### Step 2. Business Logic Generation - Base Models And Enums

- [x] Create `src/dcinside_scraper/models/base.py` with `StrictBaseModel` and shared metadata defaults.
- [x] Create `src/dcinside_scraper/models/enums.py` with Job, gallery, media, content, checkpoint, stop reason, output, and report enums.
- [x] Ensure public models reject unknown fields with Pydantic v2 `extra="forbid"`.

### Step 3. Business Logic Generation - Job And Request Models

- [x] Create `src/dcinside_scraper/models/job.py`.
- [x] Implement `JobConfig`, `ScrapeOptions`, `WorkerConfig`, `StorageConfig`, `RangeFilter`, realtime termination options, source discriminated unions, and public request models.
- [x] Validate job/source type matching, range ordering, deep-search range requirement, no-keyword range requirement, and realtime exactly-one termination condition.

### Step 4. Business Logic Generation - Post, Comment, Media, Checkpoint, Report, Error Models

- [x] Create `src/dcinside_scraper/models/content.py`, `media.py`, `comment.py`, `post.py`, `checkpoint.py`, `report.py`, and `error.py`.
- [x] Implement ordered content blocks for text, image, DC video, YouTube, link, series, and unknown embeds.
- [x] Implement repost consistency, checkpoint status/reason consistency, and schema version defaults.

### Step 5. Business Logic Generation - Validation And Error Helpers

- [x] Create `src/dcinside_scraper/core/validation.py` with `MetadataValidator`, `JobConfigValidator`, and bounded metadata checks.
- [x] Create `src/dcinside_scraper/core/errors.py` with typed core exceptions.
- [x] Implement `ErrorMapper` and `SecretRedactor` for adapter-safe `ErrorResult` creation.

### Step 6. Business Logic Generation - Schema Compatibility Helpers

- [x] Create `src/dcinside_scraper/core/schema.py`.
- [x] Implement `SchemaRegistry`, `SchemaSnapshot`, `SchemaDiffChecker`, and `MigrationRegistry`.
- [x] Add initial schema version registrations for post, checkpoint, and job report.

### Step 7. API Layer Generation - Ports And Public API

- [x] Create `src/dcinside_scraper/core/ports.py` with `HttpPort`, `OutputStorePort`, `MediaStorePort`, `CheckpointStorePort`, `ClockPort`, and `LoggerPort` protocols.
- [x] Create `src/dcinside_scraper/core/api.py` with import-safe public async function signatures for search, fetch, run, and resume entrypoints.
- [x] Export stable public names from `src/dcinside_scraper/__init__.py`.

### Step 8. Business Logic Unit Testing - Example Tests

- [x] Create example tests for valid minimal `JobConfig` per source type.
- [x] Test invalid job/source mismatch, invalid realtime termination options, invalid deep-search/no-keyword range, stopped checkpoint without reason, repost consistency, and error redaction.
- [x] Test package import side-effect safety.

### Step 9. Business Logic Unit Testing - Property-Based Strategies

- [x] Create `tests/strategies/job_configs.py`.
- [x] Create `tests/strategies/post_results.py`.
- [x] Create `tests/strategies/content_blocks.py`.
- [x] Create `tests/strategies/checkpoints.py`.
- [x] Create `tests/strategies/errors.py`.

### Step 10. Business Logic Unit Testing - Property-Based Tests

- [x] Create property tests for JSON round trip, range invariants, content order invariants, repost consistency, checkpoint status/reason consistency, and schema version preservation.
- [x] Keep Hypothesis shrinking and seed reproducibility enabled.

### Step 11. API Layer Unit Testing

- [x] Test port protocols are importable and structurally usable by simple fake implementations.
- [x] Test public API placeholders are import-safe and do not trigger network, file, terminal, `.env`, or `user-agents.txt` side effects.

### Step 12. Documentation Generation

- [x] Create `aidlc-docs/construction/uow-001-core-models-and-config/code/public-contracts.md`.
- [x] Create `aidlc-docs/construction/uow-001-core-models-and-config/code/code-generation-summary.md`.
- [x] Document generated public models, schema versions, error mapping, and deferred runtime responsibilities.

### Step 13. Deployment Artifacts Generation

- [x] Do not create Docker, Terraform, database migration, object storage, queue, or monitoring artifacts for UOW-001.
- [x] Record this as N/A in the code generation summary.

## Story Traceability

| Story | Coverage In This Unit |
|---|---|
| US-017 Python 라이브러리 API를 제공한다 | public package exports, core API signatures, strict request/result models |
| US-001 to US-016, US-018, US-019 | shared contracts only; executable behavior belongs to later units |

## Completion Criteria

- All planned source files exist under `src/dcinside_scraper/`.
- Tests for UOW-001 contracts exist under `tests/`.
- Documentation summary exists under `aidlc-docs/construction/uow-001-core-models-and-config/code/`.
- No runtime infrastructure artifact is created for UOW-001.
- All checkboxes in this plan are marked complete after generation.
