# Performance Test Instructions - UOW-005 Job Runner And Checkpoint

## Status

Mandatory performance tests are not required for UOW-005 Build/Test.

## Reason

UOW-005 only implements in-process runner orchestration. Real throughput depends on:

- UOW-002 HTTP delay/retry policy
- UOW-003 collector traversal behavior
- UOW-004 detail parsing cost
- UOW-006 storage backend
- future CLI/container runtime configuration

## Current Substitute

The test suite verifies bounded execution behavior:

- worker count comes from `WorkerConfig.post_worker_count`
- queue items remain `PostCandidate`
- checkpoint save interval remains 10 completed outcomes
- no external queue framework is introduced

Full throughput benchmarking is deferred until the runnable CLI/container adapter exists.
