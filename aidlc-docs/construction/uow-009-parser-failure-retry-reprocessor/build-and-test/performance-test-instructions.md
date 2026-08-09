# Performance Test Instructions - UOW-009 Parser Failure Retry Reprocessor

## Default Gate

No mandatory benchmark is required for UOW-009.

The implemented performance-sensitive behavior is covered structurally:

- failure files stream line by line
- existing posts skip index stores keys only
- raw invalid/ineligible records are not retained
- retry uses existing request interval and worker policy

## Future Benchmark Trigger

Add a benchmark when real failure inputs exceed hundreds of thousands of lines or selector memory usage becomes visible.

Suggested future check:

```text
generate large failures.jsonl -> run selector -> assert bounded memory and acceptable elapsed time
```

SQLite staging or external queues remain deferred until measurement shows they are needed.
