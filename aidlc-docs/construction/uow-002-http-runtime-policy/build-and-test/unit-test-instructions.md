# Unit Test Execution - UOW-002 HTTP Runtime Policy

## Run Unit Tests

### 1. Execute All Tests

```bash
python -m pytest -q
```

### 2. Review Test Results

- **Expected**: 41 tests pass, 0 failures
- **Coverage**: coverage percentage is not gated in UOW-002
- **Test Report Location**: terminal output

### 3. Fix Failing Tests

If tests fail:

1. Review pytest output.
2. Identify whether the failure is proxy loading, User-Agent rotation, limiter/retry, classification, redaction, import safety, or model contract behavior.
3. Fix the smallest affected source file.
4. Rerun `python -m pytest -q`.

## Test Categories

| Category | Files |
|---|---|
| HTTP runtime example tests | `tests/test_http_runtime.py` |
| HTTP runtime property tests | `tests/test_http_properties.py` |
| HTTP runtime strategies | `tests/strategies/http_runtime.py` |
| Existing model/API tests | `tests/test_models.py`, `tests/test_properties.py`, `tests/test_api_ports.py` |
