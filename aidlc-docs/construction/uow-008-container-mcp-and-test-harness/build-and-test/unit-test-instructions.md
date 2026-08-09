# Unit Test Execution - UOW-008 Container, MCP, And Test Harness

## Focused UOW-008 Tests

```powershell
& .\.tmp\uow008-build-venv\Scripts\python.exe -m pytest tests\test_container_adapter.py tests\test_s3_output_and_postgres.py tests\test_mcp_adapter.py tests\test_quality_harness.py -q -p no:cacheprovider --basetemp .tmp\pytest-uow008-focused-build
```

Observed result:

```text
12 passed, 1 skipped in 6.93s
```

## Full Default Suite

```powershell
& .\.tmp\uow008-build-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp\pytest-uow008-all-build
```

Observed result:

```text
113 passed, 3 skipped in 19.14s
```

## Compile Check

```powershell
& .\.tmp\uow008-build-venv\Scripts\python.exe -m compileall -q src\dcinside_scraper
```

Observed result:

```text
passed
```

## Test Categories

| Category | Files |
|---|---|
| Container adapter tests | `tests/test_container_adapter.py` |
| S3/PostgreSQL adapter tests | `tests/test_s3_output_and_postgres.py` |
| MCP adapter tests | `tests/test_mcp_adapter.py` |
| Quality harness tests | `tests/test_quality_harness.py` |
| Quality fixtures | `tests/fixtures/quality/` |
| Existing default suite | `tests/test_*.py` |
