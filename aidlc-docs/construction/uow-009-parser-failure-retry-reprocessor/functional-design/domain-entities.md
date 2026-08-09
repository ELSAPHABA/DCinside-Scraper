# Domain Entities - UOW-009 Parser Failure Retry Reprocessor

## ParserFailureRetryService

Importable service that prepares and runs parser failure retries.

Responsibilities:

- read failure inputs
- select eligible parser-stage post failures
- dedupe retry candidates
- skip already recovered posts when success inputs are provided
- build a `DirectPostSource`
- call the existing Job execution path
- return a retry report summary

The service must not parse post HTML itself.

## ParserFailureRetryRequest

Validated request passed from CLI, container, MCP, or library callers.

Fields:

- `failure_refs`: list of `FailureInputRef`
- `existing_post_refs`: optional list of `PostJsonlInputRef`
- `job_id`: optional retry job id
- `scrape_options`: `ScrapeOptions`
- `worker_config`: `WorkerConfig`
- `storage_config`: `StorageConfig`
- `from_report`: optional report input ref
- `from_checkpoint`: optional checkpoint input ref or job id

Rules:

- `failure_refs` must not be empty.
- `from_report` and `from_checkpoint` must not both be set unless a later design defines explicit precedence.
- explicit option fields override restored values.

## FailureInputRef

Reference to a failure JSONL input.

Fields:

- `uri`: local path, `file://` URI, or `s3://bucket/key`
- `storage_type`: `local` or `s3`

Rules:

- local paths are resolved by the adapter before reading.
- S3 refs use S3-compatible storage config.
- refs must never include credentials.

## PostJsonlInputRef

Reference to an existing successful post JSONL input used for skip indexing.

Fields:

- `uri`: local path, `file://` URI, or `s3://bucket/key`
- `storage_type`: `local` or `s3`

Rules:

- invalid post lines do not block retry selection.
- valid rows contribute `(site_id, gallery_id, post_id)` keys only.

## RetryFailureRecord

Internal validated view of an input `FailureRecord`.

Fields:

- `site_id`
- `gallery_id`
- `post_id`
- `post_number`
- `url`
- `stage`
- `reason`
- `retryable`
- `source_ref`
- `line_number`

Rules:

- `site_id` defaults to `dcinside` when absent.
- source ref and line number are diagnostics only.

## RetryCandidate

Direct-post retry target produced from an eligible failure.

Fields:

- `key`: `(site_id, gallery_id, post_id)`
- `url`
- `gallery_id`
- `post_id`
- `post_number`
- `last_failure_reason`
- `source_ref`

Rules:

- converted candidates must validate as `PostCandidate` and then as a `DirectPostSource` URL list.
- duplicate keys keep the last valid candidate.

## ExistingPostIndex

In-memory set of already successful post keys.

Fields:

- `keys`: set of `(site_id, gallery_id, post_id)`
- `invalid_record_count`

Rules:

- used only for skip decisions.
- does not persist a new database table.

## RetrySelectionSummary

Selection and filtering diagnostics before the retry job starts.

Fields:

- `initial_failure_count`
- `invalid_failure_record_count`
- `ineligible_failure_count`
- `selected_retry_count`
- `deduped_failure_count`
- `skipped_existing_count`
- `input_refs`

Rules:

- counters are included in retry report metadata.
- skipped and invalid rows are not written as new retry failures unless code generation needs a validation report.

## ParserFailureRetryReport

Return value from `ParserFailureRetryService`.

Fields:

- `job_report`: `JobReport`
- `selection_summary`: `RetrySelectionSummary`
- `retry_source_failure_refs`
- `remaining_failure_count`

Rules:

- `remaining_failure_count` comes from the retry run's normal failure count.
- successful retry outputs remain in the retry run `posts.jsonl`.

## RetryFailuresCliCommand

CLI command shape for `retry-failures`.

Arguments:

- one or more `--failure-file` or `--failure-ref`
- optional `--existing-posts`
- optional `--from-report`
- optional `--from-checkpoint`
- normal direct-post scrape options reused from `run`
- normal storage/runtime options reused from existing CLI adapter

Rules:

- CLI builds `ParserFailureRetryRequest`.
- CLI delegates all retry selection and execution to `ParserFailureRetryService`.
