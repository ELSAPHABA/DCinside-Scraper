# Unit Test Execution - UOW-004 Post Detail And Content Parsing

## Run Unit Tests

### 1. Execute All Tests

```powershell
& .\.tmp\uow004-build-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp\pytest-uow004-all
```

For an existing environment, replace the venv Python path with the target Python 3.11+ interpreter.

### 2. Review Test Results

- **Expected**: 66 tests pass, 2 optional live smoke tests are skipped by default
- **Coverage**: coverage percentage is not gated in UOW-004
- **Test Report Location**: terminal output
- **Observed Result**: `66 passed, 2 skipped in 6.48s`

### 3. Fix Failing Tests

If tests fail:

1. Review pytest output.
2. Identify whether the failure is body segment parsing, media metadata, repost metadata, comment/reply hierarchy, safe event redaction, or public API wiring.
3. Fix the smallest affected source file.
4. Rerun the focused failing target.
5. Rerun the full command above.

## Test Categories

| Category | Files |
|---|---|
| Post detail parser example tests | `tests/test_post_detail_parsing.py` |
| Post detail property tests | `tests/test_post_detail_properties.py` |
| Post detail strategies | `tests/strategies/post_detail.py` |
| Post detail fixtures | `tests/fixtures/post_detail/` |
| Optional post live smoke | `tests/test_post_detail_live_smoke.py` |
| Existing model/API/HTTP/search tests | `tests/test_models.py`, `tests/test_properties.py`, `tests/test_api_ports.py`, `tests/test_http_runtime.py`, `tests/test_http_properties.py`, `tests/test_search_collection.py`, `tests/test_search_properties.py` |
