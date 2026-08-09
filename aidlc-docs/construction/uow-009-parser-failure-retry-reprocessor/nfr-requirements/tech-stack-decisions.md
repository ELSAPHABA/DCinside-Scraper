# Tech Stack Decisions - UOW-009 Parser Failure Retry Reprocessor

## Runtime And Language

| Decision | Selection | Rationale |
|---|---|---|
| Language | Python 3.11+ | Matches the existing scraper package baseline. |
| Retry service | importable `ParserFailureRetryService` | Keeps retry logic reusable by CLI, container, MCP, and future platform code. |
| CLI command | `retry-failures` | Direct terminal entrypoint for parser failure recovery. |
| File parsing | stdlib line streaming plus `json`/Pydantic validation | Avoids loading full JSONL files and adds no dependency. |
| Execution | existing `DirectPostSource` and `JobRunner` | Reuses worker, checkpoint, HTTP, output, and stop behavior. |

## Dependency Decisions

| Dependency | Selection | Scope |
|---|---|---|
| Pydantic | existing runtime dependency | Failure/report/request validation. |
| `boto3` | reuse existing `s3` optional extra | S3/Garage input object reads when enabled. |
| `aioboto3`/`aiobotocore` | not added | Existing S3 boundary is enough for retry input reads. |
| SQLite | not added | Streaming/key-set approach is enough for first implementation. |
| Queue/DLQ dependency | not added | Distributed retry scheduling is out of scope. |
| Polars | not required | Retry selection is operational logic, not analysis processing. |

Default install remains focused on local scraper runtime. S3/Garage retry input support is available only when the existing `s3` optional extra is installed.

## Input Strategy

| Area | Decision |
|---|---|
| Local failure files | stream line by line |
| `file://` refs | treat as local files after validation |
| `s3://bucket/key` refs | read through existing S3-compatible boundary |
| Missing input | validation error before Job start |
| Malformed line | count and skip line |
| Source mutation | forbidden |

S3 prefix discovery is deferred. The first implementation accepts explicit input refs only.

## Selection Strategy

| Area | Decision |
|---|---|
| Eligibility | `stage="post"` plus parser/metadata/content reason allowlist |
| Exclusions | CAPTCHA, block, network, storage, checkpoint, cancellation |
| Dedupe key | `(site_id, gallery_id, post_id)` |
| Missing `site_id` | default to `dcinside` |
| Duplicate URL conflict | last valid failure record wins |
| Existing success skip | optional `posts.jsonl` key index |

This keeps retry scoped to parser failures after selector/parser fixes.

## Option Restoration Strategy

| Area | Decision |
|---|---|
| Default options | normal direct-post `run` defaults |
| Explicit retry options | highest precedence |
| `--from-report` | restore allowlisted compatible settings |
| `--from-checkpoint` | restore allowlisted compatible settings |
| Combined restore inputs | validation error |
| Secret restoration | forbidden |

The restore options reduce repeated CLI input. They do not replace explicit override flags.

## Report Strategy

| Area | Decision |
|---|---|
| Main report | existing `JobReport` |
| Existing fields | keep current meaning |
| Retry counters | optional metadata field if needed |
| Remaining failures | normal retry run `failures.jsonl` |
| Terminal output | safe summary counts |
| Raw input diagnostics | not printed |

Required retry counters:

- `retry_source_failure_refs`
- `initial_failure_count`
- `invalid_failure_record_count`
- `ineligible_failure_count`
- `selected_retry_count`
- `deduped_failure_count`
- `skipped_existing_count`
- `success_count`
- `remaining_failure_count`

## Test Stack

| Decision | Selection | Rationale |
|---|---|---|
| Example tests | pytest | Existing test runner. |
| PBT | Hypothesis | Existing project choice for pure selection logic. |
| Local inputs | temp files | Fast deterministic default coverage. |
| S3 inputs | fake object store by default | Avoids network requirement. |
| Runner | fake runner for selection/orchestration tests | Keeps default tests isolated from live scraping. |
| S3/Garage smoke | optional marker/env-gated | Verifies integration without slowing default gate. |
| Live retry smoke | optional marker/env-gated | Prevents flaky network dependency in default gate. |

Required default test categories:

- import side-effect safety
- failure input validation
- streaming JSONL selection
- malformed line counters
- parser reason allowlist
- duplicate last-wins behavior
- existing success skip
- option restoration precedence
- safe report metadata
- CLI safe summary

## Deferred Decisions

- SQLite staging for very large retry files
- distributed DLQ or retry scheduler
- automatic S3 prefix discovery
- async S3 SDK
- retrying network/storage/checkpoint failures
- raw HTML archive reparse
