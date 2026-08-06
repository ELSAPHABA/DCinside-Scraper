# Security Test Instructions - UOW-004 Post Detail And Content Parsing

## Purpose

UOW-004 security scope covers required HTTP client injection, safe failure/event redaction, no import-time side effects, and error redaction for raw details.

## Run Security-Relevant Tests

```powershell
& .\.tmp\uow004-build-venv\Scripts\python.exe -m pytest tests\test_post_detail_parsing.py::test_public_post_detail_apis_require_client tests\test_post_detail_parsing.py::test_failure_and_event_builders_exclude_raw_values tests\test_models.py::test_import_has_no_runtime_side_effects tests\test_models.py::test_error_redaction_drops_secret_details -q -p no:cacheprovider --basetemp .tmp\pytest-uow004-security
```

Expected result:

```text
4 passed
```

## Dependency Check

```powershell
& .\.tmp\uow004-build-venv\Scripts\python.exe -m pip check
```

Expected result in a clean UOW-004 venv:

```text
No broken requirements found.
```

## Security Assertions

- public post detail APIs require a caller-injected HTTP client
- UOW-004 does not create its own HTTP client
- raw HTML and raw response details are excluded from safe failure/event surfaces
- secret-bearing error details are redacted
- imports do not perform runtime network or filesystem side effects
- live smoke is disabled unless explicitly enabled

## Deferred Security Tests

| Security Concern | Target Unit |
|---|---|
| checkpoint stop on CAPTCHA/block | UOW-005 |
| output file/object permissions | UOW-006 and UOW-008 |
| CLI proxy warning and env file creation | UOW-007 |
| container env injection and MCP auth boundary | UOW-008 |
