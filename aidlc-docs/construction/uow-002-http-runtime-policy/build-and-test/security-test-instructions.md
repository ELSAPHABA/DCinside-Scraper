# Security Test Instructions - UOW-002 HTTP Runtime Policy

## Purpose

UOW-002 security scope covers proxy secret safety, `.env` loading safety, cookie handling, safe structured HTTP events, and CAPTCHA/block fail-closed behavior.

## Run Security-Relevant Tests

```bash
python -m pytest tests/test_http_runtime.py::test_dotenv_loader_reads_allowlist_without_mutating_environment tests/test_http_runtime.py::test_explicit_proxy_wins_over_env_file tests/test_http_runtime.py::test_captcha_response_is_not_retried_and_closes_client tests/test_http_runtime.py::test_cancelled_request_closes_client tests/test_http_runtime.py::test_safe_http_event_builder_redacts_query_and_proxy_secret tests/test_http_properties.py::test_safe_event_builder_drops_secret_like_fields -q
```

Expected result:

```text
6 passed
```

## Dependency Check

```bash
python -m pip check
```

Expected result:

```text
No broken requirements found.
```

## Security Assertions

- `.env` is loaded with `dotenv_values()` only
- `load_dotenv()` is not used
- process environment is not mutated
- raw `.env`, proxy password, credential URL, raw cookies, raw headers, and raw body are excluded from safe HTTP events
- CAPTCHA response is not retried
- cancellation closes the client

## Deferred Security Tests

| Security Concern | Target Unit |
|---|---|
| CLI proxy prompt warning and `.env` creation | UOW-007 |
| container env injection and `.env` generation | UOW-008 |
| output storage permissions | UOW-006 and UOW-008 |
| checkpoint persistence permission and recovery | UOW-005 and UOW-008 |
