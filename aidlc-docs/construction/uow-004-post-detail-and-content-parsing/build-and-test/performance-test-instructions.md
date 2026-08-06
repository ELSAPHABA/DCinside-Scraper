# Performance Test Instructions - UOW-004 Post Detail And Content Parsing

## Current Performance Scope

UOW-004 has no mandatory throughput or latency gate.

Reason:

- this unit is an importable post detail parsing library
- live DCinside response time is outside deterministic test control
- full Job throughput depends on later worker, checkpoint, and storage units

## Current Performance-Relevant Checks

Default tests cover:

- bounded post content segment parsing
- deterministic parser output against static fixtures
- property-based comment/reply and body segment normalization checks
- no browser automation dependency in the parser path

Command:

```powershell
& .\.tmp\uow004-build-venv\Scripts\python.exe -m pytest tests\test_post_detail_parsing.py tests\test_post_detail_properties.py -q -p no:cacheprovider --basetemp .tmp\pytest-uow004-focused
```

Expected result:

```text
10 passed
```

## Future Performance Tests

| Test Concern | Target Unit |
|---|---|
| post worker concurrency and queue backpressure | UOW-005 |
| JSONL/Garage write throughput | UOW-006 |
| full local/container Job elapsed time | UOW-008 |
