# Integration Test Instructions - UOW-003 Search And Link Collection

## Current Integration Scope

UOW-003 has no full deployed integration environment.

Current substitutes:

- fake UOW-002-compatible HTTP client in search collector tests
- static gallery/integrated/search-date fixtures
- public `search_gallery` and `search_integrated` API wiring tests
- optional live smoke test, disabled by default

## Default Integration-Like Test Command

```powershell
py -3.12 -m pytest tests/test_search_collection.py -q
```

Expected result:

```text
12 passed
```

## Optional Live Smoke

```powershell
$env:DCINSIDE_LIVE_SMOKE_ENABLED = "true"
py -3.12 -m pytest tests/test_search_live_smoke.py -q
```

Live smoke rules:

- not part of mandatory CI gate
- performs one gallery search request
- does not bypass CAPTCHA
- does not persist cookies

## Deferred Integration Tests

| Integration Concern | Target Unit |
|---|---|
| post/comment/media detail scraping | UOW-004 |
| queue, repeated realtime loop, checkpoint handoff | UOW-005 |
| JSONL/media/Garage output persistence | UOW-006 |
| CLI prompt and runtime option parsing | UOW-007 |
| container, PostgreSQL checkpoint, MCP, deployed monitoring | UOW-008 or later adapter unit |
