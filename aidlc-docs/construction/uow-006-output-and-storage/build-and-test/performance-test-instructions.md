# Performance Test Instructions - UOW-006 Output And Storage

## Current Performance Scope

UOW-006 has no mandatory throughput or latency gate.

Reason:

- this unit writes local JSONL/media/checkpoint data and defines an S3-compatible boundary
- full scraper throughput depends on later JobRunner worker scheduling and media download behavior
- external S3/Garage performance depends on deployment configuration

## Current Performance-Relevant Checks

Default tests cover:

- append-only JSONL writes
- no full JSONL rewrite per record
- atomic small JSON document writes
- path/key generation through pure helpers
- checkpoint document bounded to latest checkpoint per `job_id`

Command:

```powershell
& .\.tmp\uow006-build-venv\Scripts\python.exe -m pytest tests\test_outputs_storage.py tests\test_outputs_properties.py -q -p no:cacheprovider --basetemp .tmp\pytest-uow006-focused-build
```

Expected result:

```text
10 passed
```

## Future Performance Tests

| Test Concern | Target Unit |
|---|---|
| checkpoint commit frequency under worker pool | UOW-005 |
| media download plus storage throughput | UOW-005/UOW-006 integration |
| Garage upload throughput | UOW-008 |
| full Job elapsed time | UOW-008 |
