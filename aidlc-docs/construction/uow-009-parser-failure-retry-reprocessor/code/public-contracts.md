# Public Contracts - UOW-009 Parser Failure Retry Reprocessor

## CLI Contract

`retry-failures` is available through the existing CLI entrypoint:

```powershell
dcinside-scraper retry-failures --failure-file .\outputs\job-a\run-1\failures.jsonl
```

Equivalent module form:

```powershell
python -m dcinside_scraper.adapters.cli retry-failures --failure-file .\outputs\job-a\run-1\failures.jsonl
```

Supported inputs:

- `--failure-file <local-path>`
- `--failure-ref <local-path|file://...|s3://bucket/key>`
- `--existing-posts <local-path|file://...|s3://bucket/key>`
- `--existing-posts-root <local-directory>`
- `--job-id <id>`
- normal runtime options such as `--output-path`, `--no-comments`, `--image-mode`, `--dccon-mode`, `--request-interval-seconds`, `--post-worker-count`, User-Agent, and proxy options

Rules:

- at least one failure input is required
- source `failures.jsonl` files are read-only
- retry results are written as a new run output
- `--existing-posts-root` is local filesystem only
- S3/Garage refs must be explicit object refs
- S3/Garage prefix listing is not performed

## Library Contract

```python
from dcinside_scraper.retry import ParserFailureRetryRequest, ParserFailureRetryService
```

Primary service:

```python
report = await ParserFailureRetryService().retry(request, execute_job=execute_job)
```

`execute_job` receives a prepared direct-post `JobConfig` and returns a `JobReport`.

Request shape:

```python
ParserFailureRetryRequest(
    failure_refs=("outputs/job-a/run-1/failures.jsonl",),
    existing_post_refs=("outputs/job-b/run-2/posts.jsonl",),
    existing_post_roots=(),
    job_id="retry-1",
    scrape_options=ScrapeOptions(),
    worker_config=WorkerConfig(),
    storage_config=StorageConfig(),
)
```

## Selection Contract

`select_parser_failure_retries()` is pure selection logic for tests and reuse.

It includes only:

- `stage == "post"`
- parser/metadata/content/comment parse failure reason allowlist

It excludes:

- CAPTCHA
- block
- network
- storage
- checkpoint
- manual/cancel failures

Duplicate keys are deduped by `(site_id, gallery_id, post_id)`. The last valid duplicate record wins.

## Existing Success Skip Contract

Existing success inputs are successful `posts.jsonl` files.

Only these fields are used:

- `site_id`, defaulting to `dcinside`
- `gallery_id`
- `post_id`

Invalid post lines are counted but ignored for skip decisions.

## Report Metadata Contract

Retry metadata is stored at:

```text
JobReport.metadata["parser_failure_retry"]
```

Keys:

- `retry_source_failure_refs`
- `initial_failure_count`
- `invalid_failure_record_count`
- `ineligible_failure_count`
- `selected_retry_count`
- `deduped_failure_count`
- `skipped_existing_count`
- `existing_post_invalid_record_count`
- `success_count`
- `remaining_failure_count`

Existing `JobReport` top-level fields keep their existing meaning.

## Container Contract

The existing worker container accepts the same subcommand:

```powershell
docker run --rm `
  --env-file .\.env.container `
  -v D:\scraper-outputs:/inputs:ro `
  dcinside-scraper-worker `
  retry-failures `
  --failure-file /inputs/job-a/run-1/failures.jsonl
```

Rules:

- local input paths are container paths
- host inputs should be mounted read-only
- S3/Garage inputs use container S3 env and require no input volume mount
- no retry-specific image is required

## Test Contract

Default tests require no live network, Docker, Garage, PostgreSQL, or MCP server.

Required default coverage:

- selection allowlist/exclusion
- malformed line tolerance
- dedupe last-wins
- existing success skip
- local `--existing-posts-root`
- CLI command with fake runner
- restore-source conflict validation
- import side-effect safety
- Hypothesis properties for dedupe and skip monotonicity
