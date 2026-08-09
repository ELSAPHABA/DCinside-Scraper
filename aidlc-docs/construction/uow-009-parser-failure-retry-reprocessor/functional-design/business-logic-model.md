# Business Logic Model - UOW-009 Parser Failure Retry Reprocessor

## Purpose

UOW-009 adds a focused reprocessing path for post-level parser failures found in previous scrape runs.

The unit reads one or more failure inputs, selects only parser-stage post failures, builds a direct-post retry batch, and executes that batch through the existing `JobRunner` and `PostDetailService` path. It must preserve the original failure files and write retry results as a new run with normal `posts.jsonl`, `failures.jsonl`, and `report.json` outputs.

This unit does not change parser selectors, HTTP retry policy, checkpoint semantics, output JSON schema, CAPTCHA handling, or distributed queue behavior.

## Confirmed Decisions

| Area | Decision |
|---|---|
| Retry input | local `failures.jsonl` files and S3/Garage object URIs are supported |
| Retry selection | include only `stage="post"` parser/metadata/content failures by allowlist |
| Existing success skip | optional existing `posts.jsonl` inputs skip already recovered `(site_id, gallery_id, post_id)` keys |
| Output semantics | never mutate original failures; write a new retry run/report |
| Execution path | convert candidates to `DirectPostSource` and reuse existing `JobRunner` |
| Scrape options | accept normal CLI/API scrape options; optionally restore them with `--from-report` or `--from-checkpoint` |
| Duplicate failures | dedupe by `(site_id, gallery_id, post_id)`; the last failure URL wins |
| Public boundary | provide importable `ParserFailureRetryService` plus CLI `retry-failures` |
| Remaining failures | use normal retry run `failures.jsonl`; add retry counters to report metadata |
| Stop conditions | reuse existing CAPTCHA/block/manual stop checkpoint behavior |

## Retry Flow

1. User calls `retry-failures` or `ParserFailureRetryService.retry_failures()`.
2. The adapter validates failure input refs, optional existing success refs, output/storage settings, and scrape options.
3. The service reads failure inputs line by line as UTF-8 JSONL.
4. Each line validates as a failure record compatible with `FailureRecord`.
5. The service keeps only eligible retry records:
   - `stage` is `post`
   - the failure reason matches the parser/metadata/content allowlist
   - a post URL or enough post identity exists to build a post URL
6. The service reads optional existing `posts.jsonl` inputs and builds an `ExistingPostIndex`.
7. The service dedupes retry candidates by `(site_id, gallery_id, post_id)`.
8. Candidates already present in `ExistingPostIndex` are skipped.
9. Remaining candidates become a `DirectPostSource`.
10. A new `JobConfig` is created with `job_type="direct_post"`, the selected `DirectPostSource`, normal scrape options, worker config, and storage config.
11. The service calls existing `run_job(config, runner=...)` or the equivalent `JobRunner.run(config)` path.
12. The returned `JobReport` is enriched with retry metadata counters and stored through the normal output store finalization flow.

## Input Source Flow

Failure inputs may be:

- local filesystem paths
- `file://` URIs
- `s3://bucket/key` URIs backed by the existing S3-compatible object storage implementation

Local reads use simple streaming file reads. S3/Garage reads use the existing S3-compatible object boundary; Garage-specific APIs are not required.

The first implementation reads explicit inputs only. Automatic recursive discovery of failure files under an output root is not part of the core flow unless an adapter resolves those paths before calling the service.

## Option Restoration Flow

Retry can be configured in three ways:

- explicit retry options passed through CLI/API
- `--from-report` to restore compatible options from a prior `report.json`
- `--from-checkpoint` to restore compatible options from a prior checkpoint

Precedence is:

1. explicit retry CLI/API options
2. restored report/checkpoint options
3. normal `run` defaults

The service must not require report/checkpoint restoration because failure records alone do not carry every original scrape option.

## Report Metadata Flow

Retry report metadata must include:

- `retry_source_failure_refs`
- `initial_failure_count`
- `selected_retry_count`
- `skipped_existing_count`
- `deduped_failure_count`
- `success_count`
- `remaining_failure_count`

If the current `JobReport` model cannot store metadata directly, code generation may add the smallest compatible field needed for this unit. Existing report fields keep their current meaning.

## Deferred Behavior

- distributed DLQ or scheduler
- automatic background retry daemon
- mutating or compacting old `failures.jsonl`
- retrying network, storage, checkpoint, CAPTCHA, or block failures
- HTML archive reparse without a network request
- S3 prefix discovery beyond explicit object refs
