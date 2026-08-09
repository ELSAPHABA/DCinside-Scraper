# Security Test Instructions - UOW-009 Parser Failure Retry Reprocessor

## Security-Relevant Tests

```text
.\.tmp\uow009-build-venv312\Scripts\python.exe -m pytest tests\test_parser_failure_retry.py::test_retry_restore_sources_are_mutually_exclusive tests\test_parser_failure_retry.py::test_retry_modules_import_without_runtime_side_effects tests\test_cli_adapter.py::test_print_error_uses_safe_summary tests\test_container_adapter.py::test_container_env_config_requires_storage_and_redacts_repr tests\test_container_adapter.py::test_container_missing_required_env_returns_validation_error tests\test_s3_output_and_postgres.py::test_postgres_checkpoint_store_wraps_invalid_loaded_json -q -p no:cacheprovider --basetemp .tmp\pytest-uow009-security-build
```

Expected current result:

```text
6 passed
```

## Security Boundaries Checked

- retry modules import without creating `.env`, `Checkpoint.json`, or `user-agents.txt`
- `--from-report` and `--from-checkpoint` cannot be combined
- CLI safe error output redacts secret details
- container env validation and redaction remain intact
- invalid checkpoint JSON is wrapped safely

Raw failure JSONL line content, credentials, cookies, raw headers, raw env, and raw HTML must not be printed in retry summaries.
