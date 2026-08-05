# Security Test Instructions

## Purpose

UOW-001 security scope is limited to model validation, import side-effect safety, schema-safe serialization, and adapter-facing error redaction.

## Run Security-Relevant Contract Tests

```bash
python -m pytest tests/test_models.py::test_error_redaction_drops_secret_details tests/test_models.py::test_import_has_no_runtime_side_effects -q
```

## Dependency Check

```bash
python -m pip check
```

## Deferred Security Tests

| Security Concern | Target Unit |
|---|---|
| Proxy and User-Agent runtime behavior | UOW-002 |
| CAPTCHA/block fail-closed behavior | UOW-002 and UOW-005 |
| file/object/database permission behavior | UOW-006 and UOW-008 |
| CLI/container secret input handling | UOW-007 and UOW-008 |

