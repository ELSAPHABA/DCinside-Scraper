# Unit Test Instructions - UOW-009 Parser Failure Retry Reprocessor

## Focused Tests

```text
.\.tmp\uow009-build-venv312\Scripts\python.exe -m pytest tests\test_parser_failure_retry.py tests\test_parser_failure_retry_properties.py tests\test_cli_adapter.py tests\test_container_adapter.py -q -p no:cacheprovider --basetemp .tmp\pytest-uow009-focused-build
```

Expected current result:

```text
24 passed
```

## Full Default Test Suite

```text
.\.tmp\uow009-build-venv312\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp\pytest-uow009-all-build
```

Expected current result:

```text
122 passed, 3 skipped
```

Default tests must not require Docker, Garage, S3 network, PostgreSQL, MCP server, or live DCinside.
