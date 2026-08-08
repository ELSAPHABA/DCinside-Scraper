# Unit Test Instructions - UOW-005 Job Runner And Checkpoint

## Focused Tests

Run UOW-005 focused tests:

```powershell
& .\.tmp\uow005-build-venv\Scripts\python.exe -m pytest tests\test_job_runner.py tests\test_job_runner_properties.py -q -p no:cacheprovider --basetemp .tmp\pytest-uow005-focused-build
```

Expected result:

```text
11 passed
```

## Full Suite

Run all default tests:

```powershell
& .\.tmp\uow005-build-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp\pytest-uow005-all-build
```

Expected result:

```text
87 passed, 2 skipped
```

## Covered Unit Behavior

- normal fake Job completion
- bounded post worker execution
- completed-key skip
- checkpoint save every 10 completed outcomes
- checkpoint not advanced after storage failure
- manual stop final checkpoint
- CAPTCHA/block final checkpoint
- recoverable per-post failure record
- resume dedupe
- pure runner state properties
