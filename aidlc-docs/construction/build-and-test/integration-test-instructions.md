# Integration Test Instructions

## Purpose

UOW-001 is a model/config contract package with no concrete HTTP, parser, storage, worker, CLI, container, or MCP runtime.

Integration tests are N/A for this unit.

## Future Integration Scenarios

| Scenario | Target Unit |
|---|---|
| HTTP client to search collector | UOW-002 and UOW-003 |
| HTTP client to post parser | UOW-002 and UOW-004 |
| parser result to JSONL/Garage output | UOW-004 and UOW-006 |
| collector, parser workers, output, checkpoint | UOW-003 to UOW-006 |
| CLI/container/MCP adapter to JobRunner | UOW-007 and UOW-008 |

## Current Verification Replacement

For UOW-001, contract tests cover integration-facing boundaries:

```bash
python -m pytest tests/test_api_ports.py -q
```

