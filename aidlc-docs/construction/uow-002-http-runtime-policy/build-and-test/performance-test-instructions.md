# Performance Test Instructions - UOW-002 HTTP Runtime Policy

## Purpose

UOW-002 has no full Job throughput target. It only owns per-client request interval, retry/backoff behavior, and deterministic policy execution.

Performance tests are not a required gate for this unit.

## Current Practical Check

Run the HTTP runtime property tests:

```bash
python -m pytest tests/test_http_properties.py -q
```

These tests exercise policy logic without live network delay.

## Deferred Performance Gates

| Performance Concern | Target Unit |
|---|---|
| search pagination throughput | UOW-003 |
| post/comment parser throughput | UOW-004 |
| worker queue throughput | UOW-005 |
| JSONL/Garage write throughput | UOW-006 |
| container runtime throughput | UOW-008 |

## Notes

The request interval default remains 1 second. Full throughput measurement starts after collector, parser, and storage units are integrated.
