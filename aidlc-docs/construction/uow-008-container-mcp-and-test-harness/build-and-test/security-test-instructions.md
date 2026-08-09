# Security Test Instructions - UOW-008 Container, MCP, And Test Harness

## Purpose

UOW-008 security scope covers container env redaction, safe adapter error payloads, MCP traceback/secret suppression, safe failure fixtures, and import side-effect safety.

## Run Security-Relevant Tests

```powershell
& .\.tmp\uow008-build-venv\Scripts\python.exe -m pytest tests\test_container_adapter.py::test_container_env_config_requires_storage_and_redacts_repr tests\test_container_adapter.py::test_container_missing_required_env_returns_validation_error tests\test_mcp_adapter.py::test_mcp_validation_error_is_safe tests\test_mcp_adapter.py::test_safe_error_payload_redacts_secret_details tests\test_s3_output_and_postgres.py::test_postgres_checkpoint_store_wraps_invalid_loaded_json tests\test_quality_harness.py::test_quality_failure_and_report_fixtures_are_safe -q -p no:cacheprovider --basetemp .tmp\pytest-uow008-security-build
```

Observed result:

```text
6 passed in 4.15s
```

## Dependency Check

```powershell
& .\.tmp\uow008-build-venv\Scripts\python.exe -m pip check
```

Observed result:

```text
No broken requirements found.
```

## Import Side-Effect Check

Executed from a temporary working directory:

```powershell
$env:PYTHONPATH='D:\HongDev\ELSAPHABA\DCinside-Scraper\src'
python -c "import dcinside_scraper.adapters.container, dcinside_scraper.adapters.mcp, pathlib; print(pathlib.Path('.env').exists(), pathlib.Path('user-agents.txt').exists())"
```

Observed result:

```text
False False
```

## Security Assertions

- container env config repr does not expose DB DSN, S3 secret, or proxy password
- missing env returns validation error without secret leakage
- MCP validation errors do not return traceback text
- shared adapter error payload redacts secret details
- invalid stored checkpoint JSON is wrapped as `CheckpointFailureError`
- failure fixture metadata excludes secret/raw fields
- adapter imports do not create `.env` or `user-agents.txt`

## Deferred Security Tests

| Security Concern | Reason |
|---|---|
| real Garage bucket policy | requires deployed Garage |
| real PostgreSQL credential/permission check | requires deployed PostgreSQL |
| Docker image vulnerability scan | later release/CI gate |
| networked MCP auth | HTTP/SSE MCP transport is deferred |
