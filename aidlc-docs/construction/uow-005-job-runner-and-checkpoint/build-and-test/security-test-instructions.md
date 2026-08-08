# Security Test Instructions - UOW-005 Job Runner And Checkpoint

## Security-Relevant Test Command

```powershell
& .\.tmp\uow005-build-venv\Scripts\python.exe -m pytest tests\test_job_runner.py::test_blocked_response_stops_new_work tests\test_job_runner.py::test_storage_failure_stops_without_advancing_completed_key tests\test_models.py::test_import_has_no_runtime_side_effects tests\test_outputs_storage.py::test_local_output_store_writes_posts_failures_and_report -q -p no:cacheprovider --basetemp .tmp\pytest-uow005-security-build
```

Expected result:

```text
4 passed
```

## Covered Security Behavior

- blocked response stops new work
- storage failure does not advance completed checkpoint keys
- package import has no `.env` or user-agent file side effects
- failure output redacts proxy password, cookies, and raw HTML through UOW-006 storage boundary

## Deferred Security Tests

Live CAPTCHA handling and deployed secret injection are deferred to later runtime adapter/container units.
