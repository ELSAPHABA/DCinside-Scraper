# Infrastructure Design - UOW-009 Parser Failure Retry Reprocessor

## Scope

UOW-009 adds a retry/reprocessor entrypoint on top of existing scraper runtime infrastructure.

In scope:

- `retry-failures` CLI subcommand
- local failure input paths
- explicit S3/Garage failure input object refs
- explicit existing `posts.jsonl` skip refs
- optional local `--existing-posts-root` convenience scan
- `--from-report` and `--from-checkpoint` restore input refs
- existing local/container output and checkpoint runtime
- optional S3/Garage and live retry smoke gates

Out of scope:

- new production service
- new container image
- new database table
- distributed DLQ or queue
- background scheduler
- S3 prefix scan for failure input discovery
- AWS CDK implementation

## Confirmed Decisions

| Area | Decision |
|---|---|
| New infrastructure | none; reuse existing local filesystem, S3/Garage, PostgreSQL, CLI, and worker container runtime |
| CLI exposure | expose `retry-failures` through existing console script and `python -m dcinside_scraper.adapters.cli` |
| Container runtime | reuse existing worker image/entrypoint and pass `retry-failures` as argv/subcommand |
| Local failure input | require explicit local paths; no automatic failure-file discovery |
| S3 failure input | require explicit `s3://bucket/key` object refs; no bucket listing or prefix scan |
| Existing posts skip input | accept explicit local/S3 `posts.jsonl` refs; additionally support local-only `--existing-posts-root` |
| Option restore | `--from-report` accepts local/S3 report refs; `--from-checkpoint` accepts checkpoint job id or local checkpoint ref; not both |
| Output/checkpoint | use normal `StorageConfig` and existing container env contract; retry writes a new run output |
| Smoke infrastructure | default tests use temp files/fakes; S3/Garage and live retry smoke are marker/env-gated |
| Shared infrastructure | no new shared infrastructure artifact; summarize reuse in this UOW's infrastructure docs |

## CLI Runtime Boundary

The retry entrypoint is part of the existing CLI:

```text
dcinside-scraper retry-failures ...
python -m dcinside_scraper.adapters.cli retry-failures ...
```

The command accepts:

- one or more explicit failure input refs
- optional explicit existing `posts.jsonl` skip refs
- optional local `--existing-posts-root`
- optional `--from-report`
- optional `--from-checkpoint`
- normal direct-post scrape/runtime/output options

The command must not create a second executable unless later packaging needs prove it useful.

## Local Input Boundary

Local failure inputs are explicit files.

Allowed:

```text
--failure-file outputs/job-a/run-1/failures.jsonl
--failure-ref file:///absolute/path/failures.jsonl
```

Not included in UOW-009:

- automatic failure discovery from output root
- glob expansion inside the application
- latest-run detection

Shell-level globbing is outside the application contract.

## S3/Garage Input Boundary

S3/Garage failure inputs are explicit object refs.

Allowed:

```text
--failure-ref s3://bucket/outputs/job-a/run-1/failures.jsonl
```

Not allowed in UOW-009:

- `s3://bucket/prefix/` listing
- bucket-wide discovery
- S3 failure-root scan

The object reader uses the existing S3-compatible optional dependency boundary and runtime credentials. User-visible refs must not include credentials or signed URLs.

## Existing Posts Skip Boundary

Skip inputs are successful `posts.jsonl` records used to avoid retrying already recovered posts.

Primary mode:

```text
--existing-posts outputs/job-b/run-2/posts.jsonl
--existing-posts s3://bucket/outputs/job-c/run-1/posts.jsonl
```

Convenience mode:

```text
--existing-posts-root outputs/
```

`--existing-posts-root` is local filesystem only in UOW-009. It may recursively discover files named `posts.jsonl` under the given local root, using deterministic path ordering.

It must not perform S3 prefix listing. This preserves the Q5 decision that S3/Garage refs are explicit object refs only.

## Container Runtime Boundary

The existing worker container image is reused.

Example:

```text
docker run --rm \
  --env-file .env \
  -v /host/scraper-outputs:/inputs:ro \
  dcinside-scraper-worker \
  retry-failures \
  --failure-file /inputs/job-a/run-1/failures.jsonl
```

Rules:

- local input paths inside a container are container paths
- host output directories must be mounted into the container when local refs are used
- source failure and posts files should be mounted read-only
- S3/Garage refs do not require input volume mounts
- output/checkpoint env follows existing container runtime rules

No retry-specific image or sidecar is required.

## Restore Input Boundary

`--from-report`:

- accepts local report path
- accepts explicit `s3://bucket/key` report ref
- restores only allowlisted scrape/worker/storage settings

`--from-checkpoint`:

- accepts existing checkpoint job id when a checkpoint store is configured
- may accept a local checkpoint ref if supported by the local checkpoint adapter
- restores only allowlisted settings

Both options must not be supplied together.

Explicit CLI/API options override restored values.

## Output And Checkpoint Boundary

Retry results use the normal output/checkpoint infrastructure.

Rules:

- write retry results to a new run output
- do not append to the original run
- do not mutate original failure input files
- write remaining failures through normal `failures.jsonl`
- store retry counters in `JobReport.metadata["parser_failure_retry"]`
- checkpoint progress follows existing `JobRunner` rules

Local mode uses local output/checkpoint stores. Container mode uses existing S3/Garage output and PostgreSQL checkpoint env when configured.

## Network And Credential Boundary

No new inbound ports are introduced.

Runtime may need outbound access to:

- DCinside
- S3/Garage endpoint when S3 input/output is used
- PostgreSQL when container checkpoint mode is used
- proxy endpoint when configured

Credentials enter through existing environment/config paths and must not be printed.

## Smoke Boundary

Default tests use:

- temp local files
- fake input readers
- fake runner
- fixture JSONL
- PBT for pure selector logic

Optional smoke tests are marker/env-gated:

- S3/Garage input object read
- live post retry

Default `pytest` must pass without Docker, Garage, S3 network, PostgreSQL, MCP, or live DCinside.

## Shared Infrastructure Decision

No separate shared infrastructure artifact is needed for UOW-009.

Reason:

- UOW-009 adds no new persistent service
- existing UOW-008 PostgreSQL/Garage/container boundaries are reused
- AWS CDK/cloud provisioning is explicitly deferred to UOW-010

This document is the source of infrastructure changes for UOW-009.
