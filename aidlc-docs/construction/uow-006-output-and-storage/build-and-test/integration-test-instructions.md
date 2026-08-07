# Integration Test Instructions - UOW-006 Output And Storage

## Current Integration Scope

UOW-006 has no full deployed integration environment.

Current substitutes:

- local filesystem tests through pytest `tmp_path`
- JSONL write/read round trip
- local media byte write/read
- local checkpoint save/load/load_latest
- S3 object key and injected-client `put_object` tests
- optional Garage/S3 smoke test boundary, disabled by default

## Default Integration-Like Test Command

```powershell
& .\.tmp\uow006-build-venv\Scripts\python.exe -m pytest tests\test_outputs_storage.py -q -p no:cacheprovider --basetemp .tmp\pytest-uow006-storage
```

Expected result:

```text
6 passed
```

## Optional Garage/S3 Smoke

```powershell
$env:DCINSIDE_S3_SMOKE_ENABLED = "true"
& .\.tmp\uow006-build-venv\Scripts\python.exe -m pytest tests\test_outputs_s3_smoke.py -q
```

Smoke rules:

- not part of mandatory CI gate
- requires endpoint, bucket, access key, and secret key environment values
- performs only a small object put/head/delete check
- does not run a scraper Job

## Deferred Integration Tests

| Integration Concern | Target Unit |
|---|---|
| JobRunner checkpoint commit ordering | UOW-005 |
| HTTP media download before storage | UOW-005 or UOW-007 |
| CLI output path/env mapping | UOW-007 |
| Garage container provisioning | UOW-008 |
| PostgreSQL checkpoint adapter | UOW-008 |
