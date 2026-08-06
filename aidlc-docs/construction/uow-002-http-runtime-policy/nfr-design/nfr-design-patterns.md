# NFR Design Patterns - UOW-002 HTTP Runtime Policy

## Scope

This document translates UOW-002 NFR requirements into implementation patterns. It covers async HTTP lifecycle, request limiting, retry/backoff, timeout, proxy `.env` loading, User-Agent rotation, response classification, safe logging, and test design.

## Confirmed Design Decisions

| Question | Answer | Design Decision |
|---|---|---|
| Q1 | A | One `RequestRateLimiter` per `HttpClient`, using `asyncio.Lock` and monotonic time. |
| Q2 | A | Retry is a small loop inside `HttpClient.request()` with `RetryPolicy` values. |
| Q3 | A | Production uses `time.monotonic` and `asyncio.sleep`; tests may inject clock/sleeper callables. |
| Q4 | A | Use `dotenv_values(path)` at runtime creation and extract only `DCINSIDE_PROXY_*`. |
| Q5 | A | `UserAgentProvider.next_for_request()` returns `(user_agent, changed)`; `HttpClient` clears cookies when changed. |
| Q6 | A | `ResponseClassifier` uses status, final URL, content-type, and a limited body sample. |
| Q7 | A | `SafeHttpEventBuilder` sanitizes events before passing safe dicts to `LoggerPort`. |
| Q8 | A | Unit/PBT tests use fake transport and fake time; live smoke is explicit env-gated only. |

No follow-up question is required.

## Pattern 1. Per-Client Rate Limiter

Each `HttpClient` owns exactly one `RequestRateLimiter`.

Design:

- use `asyncio.Lock` to serialize request start scheduling
- use monotonic time for elapsed calculations
- wait before first attempts and retry attempts
- keep limiter state inside one client lifecycle

The limiter only controls request start spacing. It does not own Job-level concurrency, URL collection, parser scheduling, or worker pools.

## Pattern 2. Local Retry Loop

`HttpClient.request()` contains the retry loop.

Flow:

1. Build safe request headers.
2. Ask limiter to wait.
3. Send request with explicit timeout.
4. Classify response.
5. Return success, retry retryable failures, or raise typed exception.
6. Apply bounded backoff before the next retry attempt.

`RetryPolicy` supplies:

- `max_attempts`
- retryable status codes
- retry-on-timeout flag
- retry-on-network-error flag
- backoff base and cap

No external retry/backoff library is added.

## Pattern 3. Injectable Time For Tests

Production defaults:

- `time.monotonic`
- `asyncio.sleep`

Tests may inject:

- fake monotonic clock
- fake async sleeper that records requested waits without delaying the test

This keeps limiter/backoff tests deterministic and fast without adding a production clock framework.

## Pattern 4. Runtime-Only `.env` Loading

Use `python-dotenv` through `dotenv_values(path)` only when creating runtime proxy settings.

Rules:

- do not call `load_dotenv()`
- do not mutate `os.environ`
- read only the execution-location `.env` or explicit path selected by runtime config
- extract only `DCINSIDE_PROXY_HOST`, `DCINSIDE_PROXY_ID`, `DCINSIDE_PROXY_PW`
- discard all other `.env` keys for UOW-002
- never log raw `.env` content

Proxy resolution remains:

1. explicit runtime option
2. `.env`
3. disabled

## Pattern 5. User-Agent Rotation With Client-Owned Cookie Reset

`UserAgentProvider` owns rotation state only.

API shape:

- input: current request count
- output: `(user_agent, changed)`

`HttpClient` owns cookie state. When `changed=True`, `HttpClient` clears the in-memory cookie jar before sending the next request.

This avoids coupling User-Agent selection to `httpx.AsyncClient` internals.

## Pattern 6. Lightweight Response Classification

`ResponseClassifier` runs before any parser.

Inputs:

- status code
- final URL after redirect
- response headers
- content type
- bounded body text sample

Outputs:

- success
- retryable
- captcha
- blocked
- unavailable
- network_error

The classifier does not use BeautifulSoup and does not parse full page structure. Parser units own detailed HTML extraction.

## Pattern 7. Safe HTTP Event Builder

All HTTP runtime logs pass through `SafeHttpEventBuilder`.

Responsibilities:

- remove or redact URL query strings
- include proxy enabled state and redacted proxy label only
- include User-Agent rotation event without logging the full list
- include retry attempt, status code, classification, and elapsed time
- exclude raw headers, raw cookies, raw body, proxy password, and raw `.env`

The builder sends only safe dictionaries to UOW-001 `LoggerPort`.

## Pattern 8. Deterministic Test Harness

Default tests use:

- `httpx.MockTransport` or a small fake transport
- fake clock
- fake sleeper
- reusable Hypothesis strategies under `tests/strategies/`

Live smoke tests:

- skipped by default
- excluded from mandatory CI
- run only when `DCINSIDE_LIVE_SMOKE_ENABLED=true`
- use a dedicated marker
- perform at most one lightweight HEAD/GET request

## Extension Compliance

### Security

| Rule | Status | Design Response |
|---|---|---|
| SECURITY-03 | Compliant | `SafeHttpEventBuilder` and redaction tests prevent secret logging. |
| SECURITY-05 | Compliant | proxy, timeout, retry, and runtime config are validated before use. |
| SECURITY-09 | Compliant | typed errors avoid leaking raw transport details. |
| SECURITY-10 | Compliant | dependency pinning remains required at code generation. |
| SECURITY-11 | Compliant | runtime policy, classification, logging, and error mapping stay separated. |
| SECURITY-13 | Compliant | `.env` and request options are parsed through safe APIs, not dynamic loading. |
| SECURITY-15 | Compliant | CAPTCHA/block/unavailable responses fail closed through typed exceptions. |

Other Security Baseline rules are N/A for this library/runtime unit.

### Resiliency

| Rule | Status | Design Response |
|---|---|---|
| RESILIENCY-10 | Compliant | timeout, retry bounds, limiter, and fail-closed classification are explicit. |
| RESILIENCY-14 | Compliant | failure behavior is tested with fake transport and fake time. |
| RESILIENCY-15 | Compliant | structured safe events support incident triage. |

Other Resiliency Baseline rules are N/A for this non-deployable unit.

### Property-Based Testing

| Rule | Status | Design Response |
|---|---|---|
| PBT-01 | Compliant | testable HTTP policy properties are identified. |
| PBT-03 | Compliant | proxy, User-Agent, retry, header, and redaction invariants are required. |
| PBT-04 | Compliant | response classification idempotence is required. |
| PBT-07 | Compliant | reusable strategies are placed under `tests/strategies/`. |
| PBT-08 | Compliant | Hypothesis shrinking and reproducibility remain enabled. |
| PBT-09 | Compliant | Hypothesis remains selected. |
| PBT-10 | Compliant | example tests remain required beside PBT. |

PBT-02, PBT-05, and PBT-06 are N/A for this unit.
