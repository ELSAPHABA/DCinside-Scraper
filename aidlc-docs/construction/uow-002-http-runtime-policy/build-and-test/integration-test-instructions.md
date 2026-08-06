# Integration Test Instructions - UOW-002 HTTP Runtime Policy

## Purpose

UOW-002 is an HTTP runtime library unit. It does not yet integrate with search collectors, post parsers, JobRunner, storage, CLI, container, or MCP adapters.

Full integration tests are deferred until those units exist.

## Current Integration Substitute

UOW-002 validates integration-facing behavior with fake transport tests:

```bash
python -m pytest tests/test_http_runtime.py -q
```

Covered boundaries:

- `httpx.MockTransport` request execution
- retry and limiter interaction
- proxy config conversion
- `.env` loading without process env mutation
- cookie clear on User-Agent rotation
- typed exception behavior on CAPTCHA classification
- close behavior on cancellation

## Future Integration Scenarios

| Scenario | Target Unit |
|---|---|
| HTTP client to gallery/search collector | UOW-003 |
| HTTP client to post/comment/media parser | UOW-004 |
| retryable/non-retryable errors to JobRunner checkpoint flow | UOW-005 |
| parser result to JSONL/Garage output | UOW-004 and UOW-006 |
| CLI/container/MCP adapter to runtime config | UOW-007 and UOW-008 |
