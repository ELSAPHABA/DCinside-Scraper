# Logical Components - UOW-002 HTTP Runtime Policy

## Component Overview

UOW-002 logical components implement shared HTTP runtime policy for later search, post, comment, media, CLI, container, and MCP units.

| Component | Purpose |
|---|---|
| `RuntimePolicyService` | builds validated runtime dependencies from UOW-001 config and runtime options |
| `HttpClient` | owns `httpx.AsyncClient`, request execution, retry loop, limiter, cookies, and close lifecycle |
| `RequestRateLimiter` | enforces per-client request start interval |
| `RetryPolicy` | stores retry limits and backoff configuration |
| `BackoffCalculator` | computes bounded exponential backoff delays |
| `UserAgentProvider` | loads and rotates User-Agent values |
| `ProxyProvider` | resolves proxy settings from explicit option or `.env` |
| `DotenvProxyLoader` | reads `DCINSIDE_PROXY_*` with `dotenv_values()` |
| `HeaderBuilder` | merges safe defaults, User-Agent, caller headers, and `Referer` |
| `ResponseClassifier` | classifies transport responses before parser use |
| `SafeHttpEventBuilder` | creates redacted structured log events |
| `HttpTestHarness` | fake transport/time helpers for unit and PBT tests |

## RuntimePolicyService

Responsibilities:

- accept validated runtime config from UOW-001 models
- create `UserAgentProvider`
- create `ProxyProvider`
- create `RequestRateLimiter`
- create `ResponseClassifier`
- create `HttpClient`

It does not:

- read files at package import
- prompt terminal input
- construct scraper URLs
- parse HTML
- persist checkpoints or output data

## HttpClient

Responsibilities:

- own one `httpx.AsyncClient`
- set explicit timeout
- set proxy from `ProxyProvider`
- set `trust_env=False`
- execute async requests
- run the local retry loop
- call limiter before first attempts and retries
- clear in-memory cookies when User-Agent changes
- classify responses before returning them
- close client resources

Lifecycle:

- starts when `HttpClient` is created
- may include multiple HTTP requests
- ends when `close()` or async context exit runs
- drops cookie state at lifecycle end

## RequestRateLimiter

Responsibilities:

- serialize request scheduling through `asyncio.Lock`
- enforce configured interval between request starts
- use monotonic time
- use injected sleeper in tests

State:

- `request_interval_seconds`
- `last_request_started_at`
- `lock`

The limiter does not manage worker count or Job-level concurrency.

## RetryPolicy

Fields:

- `max_attempts`
- `backoff_base_seconds`
- `backoff_max_seconds`
- `retry_status_codes`
- `retry_on_timeout`
- `retry_on_network_error`

Defaults:

- max attempts: 3
- retry status codes: 429 and 5xx
- timeout retry: enabled
- network retry: enabled

## BackoffCalculator

Responsibilities:

- compute bounded exponential backoff
- avoid unbounded sleep
- support deterministic tests with injected values

It does not decide whether a response is retryable. That is owned by `ResponseClassifier` and `RetryPolicy`.

## UserAgentProvider

Responsibilities:

- load explicit User-Agent file path when provided
- otherwise load execution-location `user-agents.txt`
- ignore blank lines
- fall back to a built-in default when no valid lines exist
- rotate every configured request count
- return `(user_agent, changed)` for each request

State:

- `agents`
- `rotation_interval_requests`
- `request_count`
- `current_index`

## ProxyProvider

Responsibilities:

- apply proxy source priority
- validate host presence
- build `httpx` proxy config
- return a redacted safe label
- disable proxy when no valid config exists

Source priority:

1. explicit runtime option
2. `.env`
3. disabled

## DotenvProxyLoader

Responsibilities:

- call `dotenv_values(path)` at runtime creation
- read only `DCINSIDE_PROXY_HOST`, `DCINSIDE_PROXY_ID`, `DCINSIDE_PROXY_PW`
- return a plain internal proxy candidate
- avoid mutating `os.environ`

It must not:

- call `load_dotenv()`
- log raw `.env`
- expose raw password in errors

## HeaderBuilder

Merge order:

1. safe default headers
2. active User-Agent
3. caller-provided headers
4. caller-provided `Referer`

Rules:

- raw cookies are not logged
- caller `Referer` is transported but not invented by UOW-002
- parser units decide exact AJAX referer values

## ResponseClassifier

Inputs:

- status code
- final URL
- response headers
- content type
- bounded body sample

Outputs:

- `success`
- `retryable`
- `captcha`
- `blocked`
- `unavailable`
- `network_error`

Typed exception mapping:

| Classification | Exception |
|---|---|
| captcha | `CaptchaDetectedError` |
| blocked | `BlockedResponseError` |
| unavailable | `UnavailableContentError` |
| network_error | `NetworkFailureError` |

The classifier does not use BeautifulSoup and does not bypass CAPTCHA.

## SafeHttpEventBuilder

Responsibilities:

- build safe event dictionaries
- redact URL query strings
- include safe proxy label only
- exclude raw headers and raw bodies
- exclude raw cookie and `.env` values
- include retry/classification/elapsed metadata

Events:

- request start
- request end
- retry attempt
- classified failure
- proxy enabled state
- User-Agent rotation

## HttpTestHarness

Test-only helpers:

- fake transport or `httpx.MockTransport`
- fake monotonic clock
- fake async sleeper
- Hypothesis strategies for proxy values, headers, User-Agent lists, retry classifications, and secret-like strings

Live smoke tests are separate and env-gated by `DCINSIDE_LIVE_SMOKE_ENABLED=true`.

## Interaction Flow

1. Caller asks `RuntimePolicyService` to create an `HttpClient`.
2. `RuntimePolicyService` builds providers and policy components.
3. `HttpClient.request()` gets the active User-Agent.
4. If User-Agent changed, `HttpClient` clears cookies.
5. `HeaderBuilder` builds request headers.
6. `RequestRateLimiter` waits for the next allowed start time.
7. `httpx.AsyncClient` sends the request with timeout and proxy config.
8. `ResponseClassifier` classifies the response.
9. `HttpClient` retries, returns success, or raises a typed exception.
10. `SafeHttpEventBuilder` emits redacted structured events through `LoggerPort`.
11. `HttpClient.close()` releases the underlying client and drops cookies.

## Relationships To Other Units

| Unit | Relationship |
|---|---|
| UOW-001 | consumes config models, ports, typed exceptions, logger, and redactor contracts |
| UOW-003 | uses `HttpClient` for gallery/search traversal |
| UOW-004 | uses `HttpClient` for post/comment/media fetches |
| UOW-005 | interprets retryable/non-retryable runtime errors in Job lifecycle |
| UOW-007 | passes CLI options into runtime config |
| UOW-008 | passes container `.env` and runtime env into runtime config |
