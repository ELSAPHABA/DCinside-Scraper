# Performance Test Instructions

## Purpose

UOW-001 has no runtime throughput target. It only validates and serializes Pydantic model contracts.

Performance tests are not a required gate for this unit.

## Optional Smoke Check

The current practical performance signal is the property-based test suite:

```bash
python -m pytest tests/test_properties.py -q
```

## Deferred Performance Gates

| Performance Concern | Target Unit |
|---|---|
| request delay and retry overhead | UOW-002 |
| search pagination throughput | UOW-003 |
| post/comment parser throughput | UOW-004 |
| worker queue throughput | UOW-005 |
| JSONL/Garage write throughput | UOW-006 |

