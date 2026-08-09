# Performance Test Instructions - UOW-008 Container, MCP, And Test Harness

## Status

Mandatory performance tests are not required for UOW-008.

Reason:

- UOW-008 adds adapter/storage/runtime boundaries.
- Scraping throughput remains governed by UOW-002 request policy and UOW-005 worker orchestration.
- S3 JSONL append uses full-object upload by design for first implementation durability.

## Suggested Future Checks

Run these only after real output sizes or deployed worker pressure justify them:

- S3 JSONL append/upload cost by object size
- PostgreSQL checkpoint save/load latency
- container cold-start time
- MCP one-shot tool call latency
- Garage vs future SeaweedFS behavior for large media sets

## Current Gate

The current gate verifies correctness, import safety, packaging, and secret redaction. No benchmark was executed.
