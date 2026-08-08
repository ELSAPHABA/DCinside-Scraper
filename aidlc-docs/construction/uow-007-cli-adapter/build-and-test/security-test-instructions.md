# Security Test Instructions - UOW-007 CLI Adapter

## Purpose

UOW-007 security scope covers import safety, safe error output, plaintext proxy warning/update boundaries, and runtime file handling.

## Run Security-Relevant Tests

```powershell
& .\.tmp\uow007-build-venv\Scripts\python.exe -m pytest tests\test_cli_adapter.py::test_import_user_agents_rejects_blank_without_overwriting tests\test_cli_adapter.py::test_update_proxy_env_preserves_unrelated_lines tests\test_cli_adapter.py::test_print_error_uses_safe_summary tests\test_cli_adapter.py::test_cli_import_has_no_runtime_side_effects tests\test_cli_adapter.py::test_root_main_help_runs_from_repo tests\test_models.py::test_error_redaction_drops_secret_details -q -p no:cacheprovider --basetemp .tmp\pytest-uow007-security-build
```

Observed result:

```text
6 passed in 3.19s
```

## Dependency Check

```powershell
& .\.tmp\uow007-build-venv\Scripts\python.exe -m pip check
```

Observed result:

```text
No broken requirements found.
```

## Security Assertions

- CLI import does not create `.env` or `user-agents.txt`
- User-Agent import rejects all-blank files without overwriting the existing destination
- Proxy updater preserves unrelated `.env` lines and updates only documented proxy keys
- error output uses safe mapped summaries
- proxy password and secret-like details are not exposed by mapped error summaries
- root `main.py` remains a thin wrapper around the package CLI

## Deferred Security Tests

| Security Concern | Target Unit |
|---|---|
| Docker entrypoint credential injection | UOW-008 |
| Garage credentials and bucket policy | UOW-008 |
| PostgreSQL checkpoint credentials | UOW-008 |
| MCP auth boundary | UOW-008 |
