# Integration Test Instructions - UOW-009 Parser Failure Retry Reprocessor

## Default Integration-Like Coverage

UOW-009 default integration-like tests use:

- local temp failure files
- local temp existing posts files
- fake runner
- existing CLI adapter
- existing container parser wiring
- report metadata assertions

Run:

```text
.\.tmp\uow009-build-venv312\Scripts\python.exe -m pytest tests\test_parser_failure_retry.py tests\test_cli_adapter.py tests\test_container_adapter.py -q
```

## Optional Smoke

Optional smoke checks are not part of the default gate:

- S3/Garage explicit object input read
- live DCinside retry of a small failure fixture
- container execution with mounted local inputs

These checks must be marker/env-gated when added or run manually.
