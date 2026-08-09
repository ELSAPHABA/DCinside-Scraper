# Logical Components - UOW-009 Parser Failure Retry Reprocessor

This document defines logical components for the UOW-009 implementation.

## Component Overview

| Component | Responsibility |
|---|---|
| `ParserFailureRetryService` | orchestrates failure input selection and direct-post retry execution |
| `ParserFailureRetryRequest` | validated retry command/service input |
| `FailureInputReader` | line-stream boundary for local and S3 failure inputs |
| `ExistingPostIndexBuilder` | builds skip key set from existing `posts.jsonl` inputs |
| `ParserFailureSelector` | pure parser-stage failure selection, dedupe, and counters |
| `RetryOptionResolver` | CLI/API layer restore logic for report/checkpoint options |
| `RetryJobAssembler` | creates `DirectPostSource` and `JobConfig` for retry execution |
| `RetryReportMetadataBuilder` | attaches retry counters to `JobReport.metadata` |
| `RetryFailuresCliAdapter` | `retry-failures` CLI command and safe terminal summary |
| `ParserFailureRetryTests` | default fake/fixture/PBT test set |

## ParserFailureRetryService

Location:

- `src/dcinside_scraper/retry/parser_failures.py`

Responsibilities:

- validate declared input refs through readers
- stream failure records
- call `ParserFailureSelector`
- optionally build existing success skip index
- assemble direct-post retry `JobConfig`
- call existing `run_job` path
- attach retry metadata to the returned `JobReport`

Must not:

- parse post HTML
- mutate source failure files
- print raw failure lines
- implement its own worker queue
- perform I/O on import

## ParserFailureRetryRequest

Shape:

```text
ParserFailureRetryRequest(
  failure_refs,
  existing_post_refs,
  job_id,
  scrape_options,
  worker_config,
  storage_config,
)
```

Responsibilities:

- carry already resolved scrape/worker/storage options
- keep input refs credential-free
- validate `failure_refs` is not empty

Restore refs such as `from_report` and `from_checkpoint` are adapter/request-builder concerns and should not be required by the service after request construction.

## FailureInputReader

Protocol:

```text
iter_lines(ref) -> Iterable[str]
```

Implementations:

- `LocalFailureInputReader`
- `S3FailureInputReader`
- fake reader for tests

Responsibilities:

- open declared input refs
- return text lines
- fail inaccessible inputs before retry execution
- hide credentials from errors

Default tests use local temp files or fakes. S3/Garage network reads are optional smoke.

## ExistingPostIndexBuilder

Responsibilities:

- stream optional existing `posts.jsonl` refs
- parse enough fields to build `(site_id, gallery_id, post_id)` keys
- ignore invalid post lines for skip decisions
- return key set and invalid-line counter

Must not retain full post records.

## ParserFailureSelector

Responsibilities:

- parse failure JSONL lines
- validate compatible `FailureRecord` fields
- include only retryable parser-stage post failures
- exclude CAPTCHA/block/network/storage/checkpoint/cancel failures
- dedupe by `(site_id, gallery_id, post_id)`
- keep last valid duplicate URL
- apply existing success skip
- return candidates and `RetrySelectionSummary`

This component is the main PBT target.

## RetryOptionResolver

Location:

- CLI/API adapter layer

Responsibilities:

- read `--from-report` or `--from-checkpoint` when provided
- reject both restore inputs when supplied together
- restore only allowlisted settings
- apply explicit CLI/API options last
- build final `ParserFailureRetryRequest`

Must not restore secrets, cookies, raw headers, or raw request bodies.

## RetryJobAssembler

Responsibilities:

- convert selected retry candidates to URL list
- validate URLs through `DirectPostSource`
- create direct-post `JobConfig`
- preserve selected scrape, worker, and storage options
- support fake runner injection in tests

Must not call `PostDetailService` directly.

## RetryReportMetadataBuilder

Responsibilities:

- build `metadata["parser_failure_retry"]`
- include selection counters
- include input refs in safe form
- copy final success and remaining failure counts from `JobReport`

The metadata builder must not change existing `JobReport` field meanings.

## RetryFailuresCliAdapter

Location:

- `src/dcinside_scraper/adapters/cli.py`

Responsibilities:

- register `retry-failures`
- parse failure refs and existing success refs
- reuse existing runtime option parsing where practical
- call `RetryOptionResolver`
- call `ParserFailureRetryService`
- print safe summary
- return validation/runtime exit codes consistent with existing CLI behavior

Must not contain retry selection logic.

## ParserFailureRetryTests

Default test files:

- `tests/test_parser_failure_retry.py`
- `tests/test_parser_failure_retry_properties.py`

Required coverage:

- import side-effect safety
- failure input validation
- malformed line tolerance
- parser reason allowlist
- dedupe last-wins
- existing success skip
- option precedence
- report metadata
- safe CLI summary
- fake runner direct-post invocation

Optional smoke:

- S3/Garage input read
- live post retry

Optional smoke is marker/env-gated and skipped by default.
