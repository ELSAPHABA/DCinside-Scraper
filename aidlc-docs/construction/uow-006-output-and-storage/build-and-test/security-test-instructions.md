# Security Test Instructions - UOW-006 Output And Storage

## Purpose

UOW-006 security scope covers path traversal rejection, failure context redaction, import safety without S3 dependency, and S3 writes through injected/lazy clients without credential leakage.

## Run Security-Relevant Tests

```powershell
& .\.tmp\uow006-build-venv\Scripts\python.exe -m pytest tests\test_outputs_storage.py::test_local_output_store_writes_posts_failures_and_report tests\test_outputs_storage.py::test_path_traversal_is_rejected tests\test_outputs_storage.py::test_s3_put_bytes_uses_injected_client tests\test_models.py::test_import_has_no_runtime_side_effects -q -p no:cacheprovider --basetemp .tmp\pytest-uow006-security-build
```

Expected result:

```text
4 passed
```

## Dependency Check

```powershell
& .\.tmp\uow006-build-venv\Scripts\python.exe -m pip check
```

Expected result in a clean UOW-006 venv:

```text
No broken requirements found.
```

## Security Assertions

- local path traversal is rejected
- failure metadata keeps only safe allow-list fields
- proxy password, cookie, and raw HTML are not written to failure JSONL metadata
- package import does not create runtime files
- S3 dependency is lazy and local mode works without S3 extra
- S3 object refs do not include credentials

## Deferred Security Tests

| Security Concern | Target Unit |
|---|---|
| checkpoint commit after storage success | UOW-005 |
| CLI `.env` warning and credential input flow | UOW-007 |
| container env injection and Garage credentials | UOW-008 |
| PostgreSQL checkpoint auth boundary | UOW-008 |
