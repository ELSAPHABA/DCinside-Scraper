# Security Test Instructions - UOW-003 Search And Link Collection

## Purpose

UOW-003 security scope covers safe collector logging, no import-time side effects, required HTTP client injection, subject head validation, bounded dedupe, and parser failure safety.

## Run Security-Relevant Tests

```powershell
py -3.12 -m pytest tests/test_search_collection.py::test_public_search_gallery_requires_client tests/test_search_collection.py::test_gallery_collect_page_validates_subject_head tests/test_search_collection.py::test_deduper_and_safe_event_bounds tests/test_search_properties.py::test_safe_collector_event_redacts_query_and_secret_fields -q
```

Expected result:

```text
4 passed
```

## Dependency Check

```powershell
py -3.12 -m pip check
```

Expected result in a clean UOW-003 venv:

```text
No broken requirements found.
```

## Security Assertions

- public search APIs require a caller-injected HTTP client
- UOW-003 does not create its own HTTP client
- major gallery subject head requests fail validation
- invalid active subject head evidence fails validation
- `SafeCollectorEventBuilder` redacts URL query strings
- `SafeCollectorEventBuilder` drops `ci_t`, raw HTML/body/content/cookie/header fields
- candidate dedupe bound raises a typed validation failure
- live smoke is disabled unless explicitly enabled

## Deferred Security Tests

| Security Concern | Target Unit |
|---|---|
| post body/comment/media parser sanitization | UOW-004 |
| checkpoint stop on CAPTCHA/block | UOW-005 |
| output file/object permissions | UOW-006 and UOW-008 |
| CLI proxy warning and env file creation | UOW-007 |
| container env injection and MCP auth boundary | UOW-008 |
