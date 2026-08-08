# Integration Test Instructions - UOW-005 Job Runner And Checkpoint

## Current Integration Scope

UOW-005 has no live infrastructure integration gate.

The current integration-like coverage uses injected fake services to verify runner orchestration across ports:

- fake collector
- fake post detail service
- fake output store
- fake checkpoint store
- fake clock/logger

## Command

The full default test suite includes the current integration-like runner coverage:

```powershell
& .\.tmp\uow005-build-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp\pytest-uow005-all-build
```

## Out Of Scope

Default UOW-005 integration tests do not require:

- live DCinside requests
- real local JSONL output store
- Garage/S3
- PostgreSQL
- Docker Compose
- proxy credentials

Those integrations belong to later adapter/container/platform units.
