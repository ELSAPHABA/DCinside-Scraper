# Business Logic Model - UOW-002 HTTP Runtime Policy

## Purpose

UOW-002 defines the shared HTTP runtime policy used by search collectors, post parsers, comment fetchers, media metadata fetchers, and JobRunner retry handling.

This unit owns request execution policy, not parsing or persistence.

## Design Decisions

| Area | Decision |
|---|---|
| HTTP runtime | `httpx.AsyncClient` |
| Proxy support | use `httpx.AsyncClient(proxy=...)` with `trust_env=False` |
| Request delay | global limiter per `HttpClient` instance |
| Retry target | network error, timeout, 429, 5xx only |
| Retry exclusion | CAPTCHA, block, access denied, unavailable content |
| Timeout default | connect 10s, read 30s, write 30s, pool 10s |
| User-Agent load | runtime creation only |
| User-Agent rotation | every 10 requests by default |
| Proxy priority | explicit runtime option, then `.env`, then disabled |
| Cookie policy | in-memory lifecycle cookies only |
| CAPTCHA handling | classify and stop through typed exceptions, no bypass |

## Runtime Policy Flow

1. Adapter or later service builds runtime options.
2. `RuntimePolicyService` validates and normalizes options.
3. `UserAgentProvider` loads User-Agent candidates at runtime creation.
4. `ProxyProvider` resolves proxy settings from explicit option or `.env`.
5. `HttpClient` creates one `httpx.AsyncClient`.
6. Each request passes through header preparation, User-Agent selection, global rate limit, retry policy, response classification, and typed error mapping.
7. Caller receives response data or a typed exception from UOW-001.
8. Client close releases connection pool and drops in-memory cookies.

## Request Execution Flow

1. Caller sends method, URL, optional params/data, optional headers, and optional `Referer`.
2. `HttpClient` asks `UserAgentProvider` for the active User-Agent.
3. If User-Agent changed since the previous request in the same lifecycle, in-memory cookies are cleared before the request.
4. `HttpClient` merges base headers, active User-Agent, caller headers, and caller `Referer`.
5. Global `RequestRateLimiter` waits until the next allowed request time.
6. Request is sent with configured timeout and proxy.
7. `ResponseClassifier` checks status code, final URL, content type, and body markers.
8. Retryable failures are retried up to the configured limit.
9. Non-retryable classified failures raise typed exceptions immediately.
10. Successful responses return to the caller without parsing.

## HttpClient Lifecycle

An `HttpClient` lifecycle is the period from creating one runtime client to closing it.

It is not the same as one HTTP request. One lifecycle may contain multiple requests.

Recommended lifecycle ownership:

| Caller Flow | Lifecycle |
|---|---|
| Search collector | one collector lifecycle for sequential search page requests |
| Post detail scrape | one post lifecycle for detail HTML, repost AJAX, comment AJAX, and related metadata requests |
| Job-wide runtime | does not share cookies across the whole Job |

Cookie rules inside a lifecycle:

- server-set cookies may stay in memory only while the client is alive
- cookies are never written to disk
- cookies are dropped when the client closes
- cookies are cleared if User-Agent changes
- cookies are not reused across Job restart, resume, Proxy change, or User-Agent change

## User-Agent Flow

1. Explicit User-Agent file path is checked first.
2. If absent, runtime checks `user-agents.txt` in the execution location.
3. Blank lines are ignored.
4. If no valid lines remain, a single default User-Agent is used.
5. Request counter starts at runtime creation.
6. By default, the active User-Agent changes every 10 requests.
7. User-Agent counters are not shared across containers or processes.

## Proxy Flow

1. Explicit runtime proxy option is used first.
2. If no explicit option exists, runtime reads `.env` from the execution location.
3. Valid `.env` proxy variables enable proxy.
4. Missing or invalid proxy variables disable proxy.
5. Proxy password and raw `.env` contents never appear in logs or error details.
6. `trust_env=False` prevents unrelated process environment proxy variables from silently changing runtime behavior.

## Retry Flow

Retryable conditions:

- network connection failure
- timeout
- HTTP 429
- HTTP 5xx

Non-retryable conditions:

- CAPTCHA page or marker
- blocked or abnormal access response
- access denied
- deleted/unavailable content
- unsupported response shape

Default retry policy:

- maximum 3 attempts total unless overridden
- exponential backoff with a small base delay
- request interval still applies before each attempt

## Classification Flow

`ResponseClassifier` classifies raw HTTP responses before any parser sees them.

Classification inputs:

- status code
- final URL after redirects
- response headers
- response body marker text
- content type

Classification outputs:

- success response
- retryable response
- `CaptchaDetectedError`
- `BlockedResponseError`
- `UnavailableContentError`
- `NetworkFailureError`

The classifier does not solve, bypass, or automate CAPTCHA.

## Boundaries

UOW-002 does not:

- construct search URLs
- parse HTML into domain data
- parse comments
- download media to storage
- write checkpoints
- prompt terminal input
- create `.env`
- create or edit `user-agents.txt`

Those behaviors belong to later units or adapters.

