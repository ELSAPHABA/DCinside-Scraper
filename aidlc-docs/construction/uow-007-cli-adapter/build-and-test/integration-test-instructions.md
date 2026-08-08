# Integration Test Instructions - UOW-007 CLI Adapter

## Current Scope

UOW-007 integration-like coverage validates CLI-to-core wiring without live DCinside requests.

Default integration substitutes:

- fake runner injection for `run_scrape_command_async`
- parser-to-`JobConfig` mapping
- parser-to-`ResumeRequest` mapping
- local `.env` proxy file update with `tmp_path`
- local `user-agents.txt` import with `tmp_path`
- root `main.py` help execution from the repository
- installed console script help execution from the build venv

## Run Current Integration-Like Checks

```powershell
& .\.tmp\uow007-build-venv\Scripts\python.exe -m pytest tests\test_cli_adapter.py -q -p no:cacheprovider --basetemp .tmp\pytest-uow007-integration-build
```

Expected result:

```text
12 passed
```

## Deferred Integration

| Concern | Target Unit |
|---|---|
| live DCinside end-to-end scrape | UOW-008 or optional smoke harness |
| Docker entrypoint env injection | UOW-008 |
| Garage object storage smoke | UOW-008 |
| PostgreSQL checkpoint adapter | UOW-008 |
| MCP tool execution | UOW-008 |
