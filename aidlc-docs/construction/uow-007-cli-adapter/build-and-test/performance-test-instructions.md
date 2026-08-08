# Performance Test Instructions - UOW-007 CLI Adapter

## Current Scope

No mandatory performance benchmark is required for UOW-007.

Reason:

- CLI parsing and wizard input are not the scraper throughput bottleneck.
- HTTP latency, parser throughput, media download, storage backend speed, and worker runtime are owned by earlier/later units.
- Live throughput measurement belongs to a later test harness.

## Basic Performance Sanity

The default full suite includes parser/model construction and property tests. No CLI dependency such as Click, Typer, Rich, prompt-toolkit, or curses wrapper was added.

## Deferred Benchmarks

| Benchmark | Target Unit |
|---|---|
| full local Job elapsed time | UOW-008 |
| container Job throughput | UOW-008 |
| Garage write throughput | UOW-008 |
| worker count/request delay tuning | UOW-008 or later performance pass |
