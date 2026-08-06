# Integration Test Instructions - UOW-004 Post Detail And Content Parsing

## Current Integration Scope

UOW-004 has no full deployed integration environment.

Current substitutes:

- fake UOW-002-compatible HTTP client in post detail API tests
- static DCinside post/detail/comment/media fixtures
- public `fetch_post_detail` API wiring tests
- parser tests covering post metadata, mixed content, repost data, comments, replies, and media metadata
- optional live smoke test, disabled by default

## Default Integration-Like Test Command

```powershell
& .\.tmp\uow004-build-venv\Scripts\python.exe -m pytest tests\test_post_detail_parsing.py -q -p no:cacheprovider --basetemp .tmp\pytest-uow004-post-detail
```

Expected result:

```text
8 passed
```

## Optional Live Smoke

```powershell
$env:DCINSIDE_LIVE_SMOKE_ENABLED = "true"
& .\.tmp\uow004-build-venv\Scripts\python.exe -m pytest tests\test_post_detail_live_smoke.py -q
```

Live smoke rules:

- not part of mandatory CI gate
- performs one public post detail request
- does not bypass CAPTCHA
- does not persist cookies
- depends on live DCinside markup and availability

## Deferred Integration Tests

| Integration Concern | Target Unit |
|---|---|
| queue, repeated realtime loop, checkpoint handoff | UOW-005 |
| JSONL/media/Garage output persistence | UOW-006 |
| CLI prompt and runtime option parsing | UOW-007 |
| container, PostgreSQL checkpoint, MCP, deployed monitoring | UOW-008 or later adapter unit |
