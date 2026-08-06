# Business Rules - UOW-002 HTTP Runtime Policy

## Runtime Rules

### BR-002-001. Import Side Effects

Importing HTTP runtime modules must not:

- create an HTTP client
- read `.env`
- read `user-agents.txt`
- make network requests
- prompt terminal input
- write files

Runtime side effects start only when a runtime object is explicitly created.

### BR-002-002. Async HTTP Client

All concrete HTTP requests in this unit use `httpx.AsyncClient`.

The implementation must not add a parallel `requests` runtime.

### BR-002-003. Trust Environment Proxy

`HttpClient` must use `trust_env=False`.

Reason: proxy behavior is controlled by the explicit option or project `.env` flow, not unrelated process-level `HTTP_PROXY` or `HTTPS_PROXY` variables.

## Request Delay Rules

### BR-002-004. Global Request Interval

One `HttpClient` instance has one global request limiter.

All requests and retries through that instance share the limiter.

Default request interval is 1 second unless config overrides it.

### BR-002-005. Retry Attempts Also Wait

Retry attempts must pass through the same request limiter as first attempts.

This prevents retry storms after temporary DCinside failures.

## Timeout Rules

### BR-002-006. Default Timeout

Default timeout values are:

| Timeout | Value |
|---|---|
| connect | 10 seconds |
| read | 30 seconds |
| write | 30 seconds |
| pool | 10 seconds |

Adapters may override these values through validated runtime config.

## Retry Rules

### BR-002-007. Retryable Conditions

Only these conditions are retryable by default:

- network connection failure
- timeout
- HTTP 429
- HTTP 5xx

### BR-002-008. Non-Retryable Conditions

These conditions are not retried:

- CAPTCHA
- blocked or abnormal access response
- access denied
- deleted/unavailable content
- unsupported response content

These must raise typed exceptions immediately.

### BR-002-009. Retry Limit

Default retry policy is maximum 3 attempts total.

The retry policy may be overridden by validated runtime config.

## User-Agent Rules

### BR-002-010. Runtime-Only User-Agent Loading

`user-agents.txt` is loaded only when runtime is explicitly created.

Package import must not read the file.

### BR-002-011. User-Agent Source Priority

User-Agent source priority is:

1. explicit file path
2. execution-location `user-agents.txt`
3. built-in default User-Agent

### BR-002-012. User-Agent File Parsing

Rules:

- one User-Agent per line
- trim surrounding whitespace
- ignore blank lines
- preserve user-provided nonblank strings
- if no valid lines remain, use one default User-Agent

### BR-002-013. User-Agent Rotation

Default rotation interval is every 10 requests.

The interval may be overridden by runtime config.

The counter is local to one runtime process and is not shared across containers.

### BR-002-014. Cookie Reset On User-Agent Change

When User-Agent changes inside a client lifecycle, in-memory cookies must be cleared before the next request.

## Proxy Rules

### BR-002-015. Proxy Source Priority

Proxy source priority is:

1. explicit runtime option
2. execution-location `.env`
3. disabled

### BR-002-016. Proxy Env Variables

The `.env` proxy profile may contain:

- `DCINSIDE_PROXY_HOST`
- `DCINSIDE_PROXY_ID`
- `DCINSIDE_PROXY_PW`

If host is missing or invalid, proxy is disabled.

### BR-002-017. Proxy Secret Handling

Logs and error details must not include:

- proxy password
- raw `.env` content
- full proxy URL with credentials
- raw credential file content

Only safe labels such as proxy enabled state and redacted host may be logged.

### BR-002-018. Proxy Change Resets Client State

Proxy changes require a new `HttpClient` lifecycle.

Cookies from another proxy must not be reused.

## Header, Referer, And Cookie Rules

### BR-002-019. Header Merge Order

Header merge order is:

1. safe default headers
2. active User-Agent
3. caller-provided headers
4. caller-provided `Referer`

Caller-provided headers may override safe defaults except forbidden internal fields defined later by implementation.

### BR-002-020. Referer For AJAX

AJAX calls should pass explicit `Referer` from the caller when required.

UOW-002 only transports the header. UOW-003 and UOW-004 decide exact referer values.

### BR-002-021. Cookie Storage

Cookies are never persisted to disk.

Only server-set in-memory cookies within the current `HttpClient` lifecycle are allowed.

### BR-002-022. Cookie Reuse Prohibited Across Boundaries

Cookies must not be reused across:

- program restart
- Job resume
- Proxy change
- User-Agent change
- new `HttpClient` lifecycle

## Response Classification Rules

### BR-002-023. Classify Before Parsing

`HttpClient` must classify CAPTCHA, block, unavailable, retryable, and success responses before parser components see the body.

### BR-002-024. CAPTCHA Fail-Closed

CAPTCHA detection raises `CaptchaDetectedError`.

The runtime must not bypass, solve, submit, or automate CAPTCHA.

### BR-002-025. Block Detection

Block or abnormal access markers raise `BlockedResponseError`.

### BR-002-026. Unavailable Content

Deleted, access denied, adult/login required, or unsupported unavailable pages raise `UnavailableContentError` unless a later parser explicitly owns a more precise classification.

## Error Rules

### BR-002-027. Typed Exceptions

UOW-002 raises UOW-001 typed exceptions:

- `CaptchaDetectedError`
- `BlockedResponseError`
- `UnavailableContentError`
- `NetworkFailureError`
- `ValidationFailure`

### BR-002-028. No Raw Secrets In Error Details

Error details must remain compatible with UOW-001 `ErrorMapper` and `SecretRedactor`.

## Data Flow Rules

### BR-002-029. No Parser Work

UOW-002 returns response bytes/text and metadata only.

It does not extract post title, comments, media URLs, search candidates, or repost data.

### BR-002-030. No Persistence Work

UOW-002 does not save JSONL, media, checkpoint, `.env`, cookies, or User-Agent files.

