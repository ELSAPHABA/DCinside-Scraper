# Business Rules - UOW-006 Output And Storage

## Output Store Rules

- UOW-006 must implement storage behind UOW-001 ports.
- `append_post` must store one `PostResult` per JSONL line.
- `finalize` must write one final `report.json` for the run.
- `OutputStorePort` must not fetch URLs, parse HTML, retry HTTP requests, or update checkpoints.
- Storage failure must surface as a typed error to the caller.

## Failure Store Rules

- `write_failure` must store one failure per JSONL line.
- `read_failures` must read persisted failure JSONL records when the backend supports retry input.
- `FailureStorePort` must not fetch URLs, parse HTML, retry HTTP requests, or update checkpoints.

## Path Rules

- Default run directory is `outputs/<job_id>/<run_id>/`.
- Post output file is `posts.jsonl`.
- Failure output file is `failures.jsonl`.
- Report output file is `report.json`.
- Media directory is `media/<gallery_id>/<post_no>/<media_type>/`.
- `job_id`, `run_id`, `gallery_id`, `post_no`, `media_type`, and filenames must be path-safe before use.
- Path resolution must stay under the configured output base directory.
- Resume must create a new `run_id`; it must not append to an earlier run's JSONL files.

## JSONL Rules

- JSONL encoding must use UTF-8.
- Each record must be one valid JSON object followed by a newline.
- `PostResult.model_dump(mode="json")` is the canonical post serialization input.
- Nullable fields must remain `null`.
- Empty arrays must remain arrays.
- Nested `content`, `images`, `comments`, `links`, and `repost` objects must not be flattened in UOW-006.
- Polars/common-schema normalization is deferred to a later platform processing step.

## Failure Record Rules

- Failure output may include `proxy_host` and `user_agent` as safe request context.
- Failure output must not include proxy ID.
- Failure output must not include proxy password.
- Failure output must not include cookies.
- Failure output must not include tokens.
- Failure output must not include raw headers.
- Failure output must not include raw HTML/body/content.
- Failure output must not include credential file contents.
- If unsafe fields are present, they must be dropped or redacted before writing.

## Media Rules

- Media storage receives bytes or metadata from the caller.
- Media storage must not create an HTTP client.
- Media storage must not download URLs directly.
- `save_media` must set either `file_path` or `object_key` on the returned media model.
- `save_metadata_only` must not write file bytes.
- Filename fallback may use media type and deterministic extension when the source URL has no usable name.
- Existing files with the same path should be overwritten only when they belong to the same Job run and media key.

## Local Checkpoint Rules

- Local checkpoint file name is `Checkpoint.json`.
- The file stores multiple latest checkpoints keyed by `job_id`.
- Save must use temporary-file write and atomic replace.
- `load(job_id)` returns the requested checkpoint or `null`.
- `load_latest()` returns the newest checkpoint by `updated_at`.
- Checkpoint status/reason validation remains the responsibility of the `Checkpoint` model.
- PostgreSQL checkpoint storage is not part of UOW-006.

## S3-Compatible Rules

- S3-compatible object keys must mirror local relative paths.
- Garage is the default S3-compatible deployment target.
- Garage-specific APIs must not be required.
- Endpoint, bucket, prefix, region, and credentials must come from configuration.
- S3 credential values must not be written to output files or logs.
- SeaweedFS must remain replaceable through the same S3-compatible port.

## Idempotency Rules

- UOW-006 output stores are append-only.
- UOW-006 must not scan JSONL files to deduplicate records.
- Duplicate prevention belongs to UOW-005 completed-key/checkpoint logic.
- Stored post records must include enough keys for later dedupe and normalization: `site_id`, `gallery_id`, `post_id`, and `post_number` when available.

## Error Handling Rules

- Directory creation failure is fatal for the run store.
- JSON serialization failure is fatal for the record being written.
- Local file write failure is fatal and must not be silently swallowed.
- S3 upload failure is fatal and must return enough safe detail for retry/reporting.
- Partial media write failure must not corrupt `posts.jsonl`; the caller decides whether to write post metadata after media failure.

## Out Of Scope Rules

- UOW-006 does not decide worker count.
- UOW-006 does not decide retry count.
- UOW-006 does not classify CAPTCHA.
- UOW-006 does not parse DCinside pages.
- UOW-006 does not expose terminal prompts.
- UOW-006 does not implement MCP tools.
