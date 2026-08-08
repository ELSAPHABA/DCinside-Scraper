# Unit Test Execution - UOW-007 CLI Adapter

## Run Unit Tests

### Focused CLI Tests

```powershell
& .\.tmp\uow007-build-venv\Scripts\python.exe -m pytest tests\test_cli_adapter.py tests\test_cli_properties.py -q -p no:cacheprovider --basetemp .tmp\pytest-uow007-focused-build
```

Observed result:

```text
14 passed in 3.97s
```

### Full Default Suite

```powershell
& .\.tmp\uow007-build-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp\pytest-uow007-all-build
```

Observed result:

```text
101 passed, 2 skipped in 8.17s
```

## Test Categories

| Category | Files |
|---|---|
| CLI example tests | `tests/test_cli_adapter.py` |
| CLI property tests | `tests/test_cli_properties.py` |
| CLI strategies | `tests/strategies/cli.py` |
| Existing core tests | `tests/test_models.py`, `tests/test_api_ports.py`, `tests/test_http_runtime.py`, `tests/test_search_collection.py`, `tests/test_post_detail_parsing.py`, `tests/test_outputs_storage.py`, `tests/test_job_runner.py` |
