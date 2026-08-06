# Unit Test Execution - UOW-003 Search And Link Collection

## Run Unit Tests

### 1. Execute All Tests

```powershell
py -3.12 -m pytest -q
```

For a clean venv, replace `py -3.12` with the venv Python path.

### 2. Review Test Results

- **Expected**: 56 tests pass, 1 optional live smoke test is skipped by default
- **Coverage**: coverage percentage is not gated in UOW-003
- **Test Report Location**: terminal output

### 3. Fix Failing Tests

If tests fail:

1. Review pytest output.
2. Identify whether the failure is URL building, BeautifulSoup parsing, subject head validation, traversal, range filtering, dedupe, safe event redaction, or public API wiring.
3. Fix the smallest affected source file.
4. Rerun `py -3.12 -m pytest -q`.

## Test Categories

| Category | Files |
|---|---|
| Search collector example tests | `tests/test_search_collection.py` |
| Search property tests | `tests/test_search_properties.py` |
| Search strategies | `tests/strategies/search.py` |
| Search fixtures | `tests/fixtures/search/` |
| Optional live smoke | `tests/test_search_live_smoke.py` |
| Existing model/API/HTTP tests | `tests/test_models.py`, `tests/test_properties.py`, `tests/test_api_ports.py`, `tests/test_http_runtime.py`, `tests/test_http_properties.py` |
