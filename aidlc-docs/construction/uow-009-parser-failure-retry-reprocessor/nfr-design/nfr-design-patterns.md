# NFR Design Patterns - UOW-009 Parser Failure Retry Reprocessor

This document translates UOW-009 NFR requirements into implementation patterns.

## Confirmed Design Answers

| Question | Answer | Design Pattern |
|---|---|---|
| Q1 | A | Use one small retry module, existing CLI adapter extension, and focused tests. |
| Q2 | A | Use small local/S3 input reader boundary; service consumes line iterators. |
| Q3 | A | Keep failure selection as pure streaming logic that returns candidates and counters. |
| Q4 | A | Build existing success skip index by streaming only post keys. |
| Q5 | A | Restore options in request builder layer, not inside retry selection. |
| Q6 | A | Add optional `JobReport.metadata` and store retry counters under `parser_failure_retry`. |
| Q7 | A | Build `DirectPostSource` and reuse existing `JobConfig` + `run_job` path. |
| Q8 | A | Print only safe CLI summary counts and report location. |
| Q9 | A | Apply PBT to pure selector/option precedence logic. |
| Q10 | A | Keep local fixture retry smoke in default tests; gate S3/Garage/live smoke. |

No follow-up question is required.

## Module Layout Pattern

First implementation uses a small layout:

```text
src/dcinside_scraper/retry/
  parser_failures.py

src/dcinside_scraper/adapters/
  cli.py

tests/
  test_parser_failure_retry.py
  test_parser_failure_retry_properties.py
```

Do not create multiple retry submodules until file size or repeated patterns justify it.

The CLI adds only a `retry-failures` subcommand and delegates retry behavior to `ParserFailureRetryService`.

## Input Reader Pattern

Use a small reader boundary:

```text
FailureInputReader.iter_lines(ref) -> Iterator[str]
```

Implementations:

- `LocalFailureInputReader`
- `S3FailureInputReader`

Rules:

- local files stream line by line
- S3/Garage objects use the existing S3-compatible optional dependency boundary
- inaccessible declared inputs fail validation before retry Job start
- raw credentials never appear in refs or errors

Tests use fake readers by default.

## Streaming Selector Pattern

Keep selection independent from file/S3/runner I/O.

Pattern:

1. receive failure JSONL line iterators
2. parse one line at a time
3. validate compatible failure fields
4. include only `stage="post"` parser/metadata/content allowlist reasons
5. update invalid/ineligible counters
6. dedupe eligible candidates by `(site_id, gallery_id, post_id)`
7. keep the last valid duplicate candidate
8. return `RetrySelectionSummary` and selected candidates

Invalid and ineligible raw records are not retained.

## Existing Success Index Pattern

Existing `posts.jsonl` inputs are optional.

Pattern:

1. stream each post JSONL line
2. extract only `(site_id, gallery_id, post_id)`
3. add valid keys to a set
4. count invalid lines
5. skip retry candidates whose keys are in the set

Do not load full post bodies into memory.

## Option Restoration Pattern

`--from-report` and `--from-checkpoint` are handled before service execution.

Pattern:

1. CLI/API request builder reads restore source when provided
2. restore only allowlisted scrape, worker, and storage settings
3. reject combined `--from-report` and `--from-checkpoint`
4. apply explicit CLI/API options last
5. pass a completed `ParserFailureRetryRequest` to the service

The service does not know whether options were explicit or restored.

## Report Metadata Pattern

Add the smallest report extension:

```text
JobReport.metadata: dict[str, Any] = {}
```

Retry counters are stored under:

```text
metadata["parser_failure_retry"]
```

Required metadata keys:

- `retry_source_failure_refs`
- `initial_failure_count`
- `invalid_failure_record_count`
- `ineligible_failure_count`
- `selected_retry_count`
- `deduped_failure_count`
- `skipped_existing_count`
- `success_count`
- `remaining_failure_count`

Existing `JobReport` fields keep their current meaning.

## Direct Post Retry Pattern

Retry execution reuses existing direct-post flow.

Pattern:

1. convert selected candidates to URL list
2. validate with `DirectPostSource`
3. build `JobConfig(job_type="direct_post")`
4. inject or build an existing `JobRunner`
5. call `run_job(config, runner=runner)`
6. attach retry metadata to returned report

Do not implement a retry-specific worker queue or direct parser loop.

## CLI Summary Pattern

`retry-failures` prints a safe summary only:

```text
retry selected=<n> skipped_existing=<n> success=<n> remaining_failure=<n>
report: <safe report path or object ref>
```

Do not print:

- raw JSONL lines
- raw HTML
- raw headers
- raw env
- credentials
- stack traces

## Test Pattern

Default tests cover:

- import side-effect safety
- local fixture retry smoke
- fake input readers
- fake runner
- malformed line counters
- inaccessible input validation
- dedupe last-wins
- existing success skip
- option restoration precedence
- safe CLI summary
- report metadata

PBT focuses on pure selector and precedence logic.

Optional smoke tests:

- S3/Garage input read
- live post retry

They are marker/env-gated and skipped by default.

## Compliance Check

| Requirement Area | Design Compliance |
|---|---|
| Security | safe CLI summary, no raw line output, S3 credential isolation, allowlisted restore |
| Resiliency | source files are read-only, inaccessible refs fail early, malformed lines are counted |
| Performance | streaming input reads, key-only success index, no raw record retention |
| Maintainability | small retry module, thin CLI adapter, existing runner/output reuse |
| PBT | selector and option precedence are pure enough for property tests |
| Import safety | retry modules do no I/O on import |
