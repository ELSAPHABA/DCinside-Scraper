# Code Generation Summary - UOW-009 Parser Failure Retry Reprocessor

## Generated Code

| Area | Files |
|---|---|
| retry service | `src/dcinside_scraper/retry/parser_failures.py`, `src/dcinside_scraper/retry/__init__.py` |
| package exports | `src/dcinside_scraper/__init__.py` |
| CLI adapter | `src/dcinside_scraper/adapters/cli.py` |
| container adapter | `src/dcinside_scraper/adapters/container.py` |
| direct-post capacity | `src/dcinside_scraper/models/job.py` |
| report metadata propagation | `src/dcinside_scraper/runner/core.py` |
| tests | `tests/test_parser_failure_retry.py`, `tests/test_parser_failure_retry_properties.py`, `tests/test_cli_adapter.py` |
| user docs | `README.md` |

## Implemented Behavior

- import-safe `ParserFailureRetryService`
- streaming local/S3 failure input reader boundary
- parser-stage post failure allowlist filtering
- malformed failure line counting and exclusion
- duplicate retry candidate dedupe with last valid record winning
- optional existing success skip from explicit `posts.jsonl` refs
- local-only `--existing-posts-root` convenience scan
- direct-post retry Job creation through existing `JobConfig` and `JobRunner`
- retry report counters under `JobReport.metadata["parser_failure_retry"]`
- CLI `retry-failures` subcommand through the existing console script
- container `retry-failures` argv support through the existing worker image/entrypoint
- S3/Garage retry input reads through existing optional S3 dependency boundary
- default tests with temp files, fake runner, and Hypothesis PBT

## Verification

Focused UOW-009 tests:

```text
python -m pytest tests/test_parser_failure_retry.py tests/test_parser_failure_retry_properties.py tests/test_cli_adapter.py tests/test_job_runner.py -q
```

Result:

```text
27 passed in 15.03s
```

Full default test suite:

```text
python -m pytest -q
```

Result:

```text
123 passed, 2 skipped in 37.68s
```

Additional checks:

```text
python -m compileall -q src\dcinside_scraper
git diff --check
```

Results:

```text
compileall passed
git diff --check passed with existing LF/CRLF warnings only
```

## Notes

No new production infrastructure, container image, database table, DLQ, or scheduler was added.

`--existing-posts-root` is local filesystem only. S3/Garage inputs use explicit `s3://bucket/key` object refs and do not perform prefix listing.
