# Unit Test Execution

## Run Unit Tests

### 1. Execute All Unit Tests

```bash
python -m pytest -q
```

### 2. Review Test Results

- **Expected**: 29 tests pass, 0 failures
- **Coverage**: coverage percentage is not gated in UOW-001
- **Test Report Location**: terminal output

### 3. Fix Failing Tests

If tests fail:

1. Review pytest output.
2. Identify whether the failure is model validation, property generation, public API placeholder, or port protocol related.
3. Fix the smallest affected source file.
4. Rerun `python -m pytest -q`.

## Test Categories

| Category | Files |
|---|---|
| Example model tests | `tests/test_models.py` |
| Property-based tests | `tests/test_properties.py` |
| API and port tests | `tests/test_api_ports.py` |
| Hypothesis strategies | `tests/strategies/*.py` |

