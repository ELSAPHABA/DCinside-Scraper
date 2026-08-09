# Deployment Architecture - UOW-009 Parser Failure Retry Reprocessor

## Architecture Classification

UOW-009 is an operational retry entrypoint, not a new deployment tier.

Primary deployment shapes:

- local CLI retry
- existing worker container retry
- library/API call from future orchestration

It does not define a queue worker, scheduler, new image, or cloud infrastructure.

## Local CLI Architecture

```text
operator
  |
  +-- dcinside-scraper retry-failures
        |
        +-- failure refs
        +-- optional existing posts refs/root
        +-- optional restore ref
        |
        +-- ParserFailureRetryService
              |
              +-- stream inputs
              +-- select/dedupe/skip
              +-- build DirectPostSource
              +-- run existing JobRunner
                    |
                    +-- write new retry run output
                    +-- write checkpoint/report
```

Local mode reads local files directly and uses the configured local output/checkpoint stores unless storage options select S3/PostgreSQL.

## Container Architecture

The existing one-shot worker container is reused.

```text
docker run dcinside-scraper-worker retry-failures ...
  |
  +-- existing container/CLI entrypoint
  +-- retry-failures command
  +-- ParserFailureRetryService
  +-- existing JobRunner
  +-- S3/Garage output and PostgreSQL checkpoint when configured
```

When local input files are used in container mode, host files must be mounted:

```text
host output directory
  |
  +-- read-only volume mount
        |
        +-- container path used by --failure-file / --existing-posts / --existing-posts-root
```

S3/Garage object refs avoid input volume mounts.

## S3/Garage Input Architecture

Explicit object refs:

```text
s3://bucket/outputs/job-a/run-1/failures.jsonl
s3://bucket/outputs/job-b/run-2/posts.jsonl
s3://bucket/outputs/job-c/run-1/report.json
```

Flow:

```text
retry command
  |
  +-- S3FailureInputReader
        |
        +-- existing S3-compatible client boundary
        +-- GetObject for explicit key
        +-- stream text lines to selector
```

No S3 prefix listing is part of UOW-009.

## Existing Posts Root Architecture

`--existing-posts-root` is local-only.

```text
--existing-posts-root /inputs/outputs
  |
  +-- recursively find posts.jsonl
  +-- deterministic path order
  +-- stream keys into ExistingPostIndex
```

This option is a convenience for skip inputs only. It does not discover failure inputs and does not scan S3 prefixes.

## Restore Architecture

Restore source behavior:

```text
--from-report local-or-s3-report-ref
  -> restore allowlisted report settings

--from-checkpoint checkpoint-job-id-or-local-ref
  -> restore allowlisted checkpoint settings
```

Conflict rule:

```text
--from-report + --from-checkpoint => validation error
```

Explicit CLI/API options override restored settings.

## Output Architecture

Retry output is a new run:

```text
retry run
  |
  +-- posts.jsonl
  +-- failures.jsonl
  +-- report.json
        |
        +-- metadata.parser_failure_retry
```

The original failure input remains unchanged.

Output target follows existing `StorageConfig`:

- local output in local mode
- S3/Garage output in container/S3 mode

Checkpoint target follows existing checkpoint config:

- local checkpoint in local mode
- PostgreSQL checkpoint in container mode when configured

## Network Architecture

No inbound port is required.

| Runtime | Direction | Endpoint | Purpose |
|---|---|---|---|
| local CLI | outbound | DCinside | retry post fetch |
| local CLI | outbound | S3/Garage | optional S3 input/output |
| container | outbound | DCinside | retry post fetch |
| container | outbound | S3/Garage | input/output object access |
| container | outbound | PostgreSQL | checkpoint store |
| any | outbound | proxy | optional request routing |

No retry-specific network listener is created.

## Credential Architecture

Credentials are provided through existing runtime paths:

- local config/env for local S3/proxy use
- container `--env` or `--env-file`
- future orchestrator secret injection

Forbidden:

- embedding credentials in image
- embedding credentials in `s3://` refs
- printing credentials in retry summary
- storing credentials in `JobReport.metadata`

## Test Deployment Architecture

Default gate:

```text
pytest
  |
  +-- temp local failure files
  +-- fake S3 input reader
  +-- fake runner
  +-- selector PBT
  +-- no external services
```

Optional smoke gate:

```text
pytest -m "s3 or live"
```

Each optional smoke test must require explicit env and skip by default.

## Operational Run Examples

Local explicit retry:

```text
dcinside-scraper retry-failures \
  --failure-file outputs/job-a/run-1/failures.jsonl \
  --existing-posts outputs/job-b/run-2/posts.jsonl
```

Local skip-root convenience:

```text
dcinside-scraper retry-failures \
  --failure-file outputs/job-a/run-1/failures.jsonl \
  --existing-posts-root outputs/
```

S3/Garage input retry:

```text
dcinside-scraper retry-failures \
  --failure-ref s3://bucket/outputs/job-a/run-1/failures.jsonl \
  --existing-posts s3://bucket/outputs/job-b/run-2/posts.jsonl
```

Container local input retry:

```text
docker run --rm \
  --env-file .env \
  -v /host/outputs:/inputs:ro \
  dcinside-scraper-worker \
  retry-failures \
  --failure-file /inputs/job-a/run-1/failures.jsonl
```
