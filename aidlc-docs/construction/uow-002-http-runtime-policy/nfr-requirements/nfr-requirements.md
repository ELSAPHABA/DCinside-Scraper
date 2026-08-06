# NFR Requirements - UOW-002 HTTP Runtime Policy

## Scope

This document defines non-functional requirements for `UOW-002 HTTP Runtime Policy`.

In scope:

- async HTTP request execution
- global request delay
- timeout and retry bounds
- User-Agent loading and rotation
- Proxy resolution from explicit options or `.env`
- response classification before parsing
- safe structured logging
- optional live smoke test policy

Out of scope:

- gallery/search URL construction
- HTML parsing
- comment parsing
- media download persistence
- checkpoint persistence
- terminal prompt UX
- container entrypoint behavior

## Confirmed Questionnaire Decisions

| Question | Answer | Decision |
|---|---|---|
| Q1 | A | Default global request interval is 1 second; unit tests verify limiter invariants, not full Job throughput. |
| Q2 | A | Retry uses max 3 attempts, bounded exponential backoff, limiter before retries, and no retry for CAPTCHA/block/unavailable. |
| Q3 | A | Every external HTTP call has explicit timeout and normal/error/cancel paths close `AsyncClient` and discard cookies. |
| Q4 | A | Raw `.env`, proxy password, credential proxy URL, and raw cookie are forbidden in logs and `ErrorResult.details`. |
| Q5 | A | Safe structured events cover request start/end, retry, classified failure, proxy enabled state, and User-Agent rotation. |
| Q6 | B | Runtime dependencies may include `httpx` and `python-dotenv`; no retry/backoff dependency is added. |
| Q7 | A | PBT targets pure policy logic; real network I/O stays in example/fake transport tests. |
| Q8 | A | Live smoke tests are excluded from unit tests and mandatory CI unless explicitly enabled by environment variable. |

No follow-up question is required. The answers are internally consistent.

## Performance Requirements

### NFR-UOW002-PERF-001. Request Interval Invariant

One `HttpClient` instance must enforce the configured global request interval before each first attempt and retry attempt.

Default:

- `request_interval_seconds = 1.0`

The unit must not set a full Job throughput SLA. End-to-end throughput is measured later after search, parser, and storage units are integrated.

### NFR-UOW002-PERF-002. Bounded Resource Use

The HTTP runtime must use bounded connection, timeout, and retry settings.

Required controls:

- explicit connect/read/write/pool timeouts
- bounded max attempts
- bounded exponential backoff
- one in-memory cookie jar per `HttpClient` lifecycle
- closeable client lifecycle

## Reliability And Resiliency Requirements

### NFR-UOW002-REL-001. Explicit Timeout

Every external HTTP call must use explicit timeout values.

Default timeout values:

| Timeout | Value |
|---|---|
| connect | 10 seconds |
| read | 30 seconds |
| write | 30 seconds |
| pool | 10 seconds |

### NFR-UOW002-REL-002. Retry Bounds

Retryable conditions are limited to:

- network connection failure
- timeout
- HTTP 429
- HTTP 5xx

Non-retryable conditions:

- CAPTCHA
- blocked or abnormal access response
- access denied
- deleted/unavailable content
- unsupported response shape

Default maximum attempts is 3 total attempts.

### NFR-UOW002-REL-003. Resource Cleanup

The runtime must close `httpx.AsyncClient` and discard the in-memory cookie jar on:

- normal close
- request failure path
- cancellation path
- context manager exit

Cookie data must never be persisted to disk.

### NFR-UOW002-REL-004. Fail-Closed Classification

CAPTCHA and block detection must raise typed exceptions and stop the current caller flow. The runtime must not solve, bypass, submit, or automate CAPTCHA.

## Security Requirements

### NFR-UOW002-SEC-001. Secret Redaction

These values must never appear in logs or `ErrorResult.details`:

- raw `.env` content
- proxy password
- proxy URL with credentials
- raw cookie
- raw request/response headers that may contain cookies or credentials

Allowed observability values:

- proxy enabled/disabled state
- proxy source
- redacted proxy host label
- response classification
- retry count
- timeout category

### NFR-UOW002-SEC-002. Controlled Proxy Resolution

Proxy source priority:

1. explicit runtime option
2. execution-location `.env`
3. disabled

`httpx.AsyncClient` must use `trust_env=False` so unrelated process-level proxy variables do not silently alter runtime behavior.

### NFR-UOW002-SEC-003. Import Side-Effect Safety

Importing UOW-002 modules must not:

- create an HTTP client
- read `.env`
- read `user-agents.txt`
- make network requests
- prompt terminal input
- write files

Runtime side effects begin only when runtime objects are explicitly created.

## Observability Requirements

### NFR-UOW002-OBS-001. Safe Structured Events

The runtime must emit safe structured events for:

- request start
- request end
- retry attempt
- classified failure
- proxy enabled state
- User-Agent rotation

URLs in logs must remove or redact query strings. Headers and raw bodies are not logged by default.

## Maintainability Requirements

### NFR-UOW002-MAINT-001. Dependency Boundary

Runtime dependencies allowed for this unit:

- `httpx`
- `python-dotenv`

No `requests` runtime, retry/backoff dependency, scraping framework, or browser automation dependency is added in UOW-002.

### NFR-UOW002-MAINT-002. Policy Components

Implementation may keep policy pieces separate where they have clear runtime responsibilities:

- `HttpClient`
- `RequestRateLimiter`
- `UserAgentProvider`
- `ProxyProvider`
- `HeaderBuilder`
- `ResponseClassifier`

Do not add adapter-specific scraper logic to UOW-002.

## Testing Requirements

### NFR-UOW002-TEST-001. Example Tests

UOW-002 must include example tests for:

- timeout config conversion to `httpx`
- retryable vs non-retryable classification
- limiter applied before first attempts and retries
- `AsyncClient` close on normal/error/cancel paths
- cookie jar cleared on User-Agent rotation
- proxy priority: explicit option, `.env`, disabled
- secret redaction in logs and `ErrorResult.details`
- import side-effect safety

### NFR-UOW002-TEST-002. Property-Based Tests

UOW-002 must include Hypothesis property-based tests for:

- User-Agent rotation invariant
- proxy resolution priority
- safe header merge
- retry classification idempotence
- redaction safety

PBT must use pure policy logic or fake transports. It must not perform real DCinside network requests.

### NFR-UOW002-TEST-003. Optional Live Smoke

Live smoke tests are not part of default unit tests or mandatory CI.

They may run only when explicitly enabled, for example:

- `DCINSIDE_LIVE_SMOKE_ENABLED=true`

Allowed live smoke scope:

- one lightweight HEAD/GET request
- no CAPTCHA handling automation
- no persisted cookie reuse

## Extension Compliance Summary

### Security Baseline

| Rule | Status | Rationale |
|---|---|---|
| SECURITY-01 | N/A | UOW-002 does not define persistent storage resources. |
| SECURITY-02 | N/A | No network intermediary is deployed in this unit. |
| SECURITY-03 | Compliant | Logs and error details must redact `.env`, proxy, cookie, and query-sensitive values. |
| SECURITY-04 | N/A | No HTML-serving endpoint. |
| SECURITY-05 | Compliant | Runtime config and proxy values require validation before use. |
| SECURITY-06 | N/A | No IAM policy in this unit. |
| SECURITY-07 | N/A | No deployment network boundary in this unit. |
| SECURITY-08 | N/A | No authenticated public resource endpoint. |
| SECURITY-09 | Compliant | Typed exceptions and safe details prevent raw transport leakage. |
| SECURITY-10 | Compliant | Dependencies must be pinned by the lock file during code generation. |
| SECURITY-11 | Compliant | HTTP policy, classification, and error mapping remain separated. |
| SECURITY-12 | N/A | No user authentication. |
| SECURITY-13 | Compliant | Runtime inputs are validated before constructing `httpx` options. |
| SECURITY-14 | N/A | Alerting belongs to later operations/infrastructure work. |
| SECURITY-15 | Compliant | CAPTCHA/block/unavailable cases produce safe typed errors. |

### Resiliency Baseline

| Rule | Status | Rationale |
|---|---|---|
| RESILIENCY-01 | N/A | UOW-002 is a library/runtime unit, not a deployable service by itself. |
| RESILIENCY-02 | N/A | Recovery targets are Job/storage concerns. |
| RESILIENCY-03 | N/A | Change process is handled globally. |
| RESILIENCY-04 | N/A | Deployment is handled in later infrastructure units. |
| RESILIENCY-05 | N/A | Runtime monitoring is surfaced through safe logs only in this unit. |
| RESILIENCY-06 | N/A | No service health endpoint. |
| RESILIENCY-07 | N/A | No deployed capacity plan in this unit. |
| RESILIENCY-08 | N/A | No topology in this unit. |
| RESILIENCY-09 | N/A | No compute scaling in this unit. |
| RESILIENCY-10 | Compliant | Timeout, retry bounds, and fail-closed classifications are required. |
| RESILIENCY-11 | N/A | No standalone DR strategy. |
| RESILIENCY-12 | N/A | No backup resource in this unit. |
| RESILIENCY-13 | N/A | Failover runbooks are later infrastructure work. |
| RESILIENCY-14 | Compliant | Unit-level failure behavior is covered through fake transport tests. |
| RESILIENCY-15 | Compliant | Structured events and safe classifications support incident triage. |

### Property-Based Testing

| Rule | Status | Rationale |
|---|---|---|
| PBT-01 | Compliant | UOW-002 policy properties are identified. |
| PBT-02 | N/A | No persistence round trip is owned by this unit. |
| PBT-03 | Compliant | Retry, proxy, User-Agent, header, and redaction invariants are required. |
| PBT-04 | Compliant | Classification idempotence is required. |
| PBT-05 | N/A | No alternate oracle implementation in this unit. |
| PBT-06 | N/A | No mutable state machine model is required beyond bounded provider counters. |
| PBT-07 | Compliant | Domain-specific strategies are required for headers, proxy values, and UA lists. |
| PBT-08 | Compliant | Hypothesis shrinking and reproducibility are required. |
| PBT-09 | Compliant | Hypothesis remains the selected PBT library. |
| PBT-10 | Compliant | Example tests remain required beside PBT. |
