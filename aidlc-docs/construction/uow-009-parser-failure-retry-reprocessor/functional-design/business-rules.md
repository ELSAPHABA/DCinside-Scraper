# Business Rules - UOW-009 Parser Failure Retry Reprocessor

## Boundary Rules

- UOW-009 must compose existing UOW-005 runner and UOW-004 post parsing behavior.
- UOW-009 must not implement a second post parser, HTTP client, worker scheduler, checkpoint format, or output writer.
- CLI `retry-failures` must be a thin adapter over `ParserFailureRetryService`.
- Importing retry modules must not start a scrape, read files, connect to S3, prompt a terminal, or create output files.

## Failure Input Rules

- Failure inputs may be local paths, `file://` URIs, or `s3://bucket/key` URIs.
- Inputs must be read as JSONL, one JSON object per line.
- Empty lines are ignored.
- Malformed JSON lines are counted as invalid input records and excluded from retry candidates.
- Original failure inputs are read-only evidence and must not be edited, compacted, or deleted.
- S3/Garage reads must use S3-compatible behavior and must not rely on Garage-only APIs.

## Retry Eligibility Rules

- A retry candidate must come from a failure record with `stage="post"`.
- The failure reason must match the parser/metadata/content allowlist.
- Eligible reasons include:
  - `post title missing`
  - `post author missing`
  - `post identity missing`
  - `metadata parse failure`
  - `content parse failure`
  - `comment parse failure` only when the failed unit is still a post-detail scrape result
- CAPTCHA, block, network, storage, checkpoint, validation setup, and user cancellation failures are not eligible.
- Records without a usable `url` must only be included if `gallery_id` and `post_id` can safely reconstruct a canonical post URL.
- Reconstructed URLs must still validate through `DirectPostSource`.

## Existing Success Skip Rules

- Existing success inputs are optional.
- When provided, existing `posts.jsonl` records are indexed by `(site_id, gallery_id, post_id)`.
- A retry candidate whose key already exists in the success index is skipped.
- If no existing success input is provided, all eligible candidates are retried after dedupe.
- Invalid existing success records are ignored for skip purposes and counted in selection diagnostics.

## Dedupe Rules

- Retry candidates are deduped by `(site_id, gallery_id, post_id)`.
- If `site_id` is absent on an input record, use the current project default `dcinside`.
- If duplicate keys have different URLs, the last valid failure record wins.
- Dedupe happens before existing success skip.
- `deduped_failure_count` is the number of eligible duplicate records removed from the retry batch.

## Option Rules

- Retry accepts the same scrape options that matter for direct post scraping:
  - comments on/off
  - image mode
  - dccon mode
  - request interval
  - post worker count
  - User-Agent and proxy settings through existing runtime config
- Explicit retry options override restored options.
- `--from-report` may restore compatible scrape, worker, and storage defaults from a prior report if the report contains them.
- `--from-checkpoint` may restore compatible job config from a prior checkpoint.
- If both restore sources are supplied, validation must fail unless code generation defines a single explicit precedence.
- Missing restore data falls back to normal `run` defaults rather than guessing.

## Output Rules

- Every retry execution writes a new output run.
- Retry must not append to the old run's `posts.jsonl`.
- Retry must not remove successful records from old `failures.jsonl`.
- Remaining failures use the normal retry run `failures.jsonl` contract.
- Retry reports must preserve existing `JobReport` fields and add retry-specific counters only where needed.
- Failure records written by retry must still be sanitized by the existing safe failure builder.

## Stop And Checkpoint Rules

- CAPTCHA or block detection stops retry execution immediately through the existing `JobRunner` stop path.
- Manual interruption follows the existing checkpoint save behavior.
- Parser-stage failure for one post may be recorded and the retry batch may continue.
- Checkpoint progress must advance only after output storage succeeds.
- Resume of a stopped retry run is owned by the existing resume flow, not by a separate retry scheduler.

## Security Rules

- Retry reports and failures must not contain raw HTML, cookies, proxy passwords, tokens, raw headers, raw env values, or stack traces.
- S3 credentials must come through existing storage config/environment handling and must not be printed.
- CLI errors must use safe summaries.
- Library errors may include structured safe details, but not secret values.

## Out Of Scope Rules

- UOW-009 does not solve CAPTCHA.
- UOW-009 does not create a distributed DLQ.
- UOW-009 does not monitor prior jobs automatically.
- UOW-009 does not retry non-parser infrastructure failures.
- UOW-009 does not redesign the community-specific URL/query parser.
