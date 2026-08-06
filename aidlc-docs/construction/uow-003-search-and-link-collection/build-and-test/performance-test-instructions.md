# Performance Test Instructions - UOW-003 Search And Link Collection

## Current Performance Scope

UOW-003 has no mandatory throughput or latency gate.

Reason:

- this unit is an importable search/link collection library
- live DCinside response time is outside deterministic test control
- full Job throughput depends on later worker, checkpoint, and storage units

## Current Performance-Relevant Checks

Default tests cover:

- integrated search page clamp to 120
- bounded candidate dedupe behavior
- deterministic URL building
- traversal guard behavior through collector tests
- parser fixture extraction without browser automation

Command:

```powershell
py -3.12 -m pytest tests/test_search_collection.py tests/test_search_properties.py -q
```

Expected result:

```text
16 passed
```

## Future Performance Tests

| Test Concern | Target Unit |
|---|---|
| link collector throughput against fake pages | UOW-005 |
| post worker concurrency and queue backpressure | UOW-005 |
| JSONL/Garage write throughput | UOW-006 |
| full local/container Job elapsed time | UOW-008 |
