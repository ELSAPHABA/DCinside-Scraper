# Unit Test Execution - UOW-006 Output And Storage

## Run Unit Tests

### 1. Execute All Tests

```powershell
& .\.tmp\uow006-build-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp\pytest-uow006-all-build
```

For an existing environment, replace the venv Python path with the target Python 3.11+ interpreter.

### 2. Review Test Results

- **Expected**: 76 tests pass, 2 optional live/smoke tests are skipped by default
- **Coverage**: coverage percentage is not gated in UOW-006
- **Test Report Location**: terminal output
- **Observed Result**: `76 passed, 2 skipped in 4.97s`

### 3. Fix Failing Tests

If tests fail:

1. Review pytest output.
2. Identify whether the failure is JSONL append, media save, checkpoint save/load, path traversal rejection, failure redaction, S3 object key/write boundary, or existing search/detail behavior.
3. Fix the smallest affected source file.
4. Rerun the focused failing target.
5. Rerun the full command above.

## Test Categories

| Category | Files |
|---|---|
| Storage example tests | `tests/test_outputs_storage.py` |
| Storage property tests | `tests/test_outputs_properties.py` |
| Storage strategies | `tests/strategies/outputs.py` |
| Existing model/API/HTTP/search/detail tests | `tests/test_models.py`, `tests/test_properties.py`, `tests/test_api_ports.py`, `tests/test_http_runtime.py`, `tests/test_http_properties.py`, `tests/test_search_collection.py`, `tests/test_search_properties.py`, `tests/test_post_detail_parsing.py`, `tests/test_post_detail_properties.py` |
