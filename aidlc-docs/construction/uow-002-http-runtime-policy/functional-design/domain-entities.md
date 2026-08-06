# Domain Entities - UOW-002 HTTP Runtime Policy

## Entity Overview

UOW-002 defines runtime entities for HTTP execution policy. Names describe contracts for the upcoming implementation, not final file names.

## Configuration Entities

### HttpRuntimeConfig

Represents resolved HTTP runtime settings.

Fields:

- `request_interval_seconds`
- `timeout`
- `retry_policy`
- `user_agent`
- `proxy`
- `default_headers`
- `metadata`

Relationships:

- owns one `TimeoutConfig`
- owns one `RetryPolicy`
- owns one `UserAgentConfig`
- owns one `ProxyConfig`

### TimeoutConfig

Fields:

- `connect_seconds`
- `read_seconds`
- `write_seconds`
- `pool_seconds`

Defaults:

- connect 10
- read 30
- write 30
- pool 10

### RetryPolicy

Fields:

- `max_attempts`
- `backoff_base_seconds`
- `retry_status_codes`
- `retry_on_network_error`
- `retry_on_timeout`

Defaults:

- max attempts 3
- retry status codes: 429 and 5xx
- network error retry enabled
- timeout retry enabled

### UserAgentConfig

Fields:

- `explicit_file_path`
- `fallback_file_name`
- `default_user_agent`
- `rotation_interval_requests`

Defaults:

- fallback file name: `user-agents.txt`
- rotation interval: 10 requests

### ProxyConfig

Fields:

- `enabled`
- `source`
- `host`
- `username`
- `password`
- `safe_label`

Rules:

- `source` is one of explicit, env_file, disabled
- password is never logged
- full proxy URL with credentials is never logged

## Runtime Components

### RuntimePolicyService

Responsibilities:

- build `HttpRuntimeConfig`
- create providers and policy components
- ensure import side-effect safety

Collaborators:

- `UserAgentProvider`
- `ProxyProvider`
- `RequestRateLimiter`
- `ResponseClassifier`
- `HttpClient`

### HttpClient

Responsibilities:

- own one `httpx.AsyncClient`
- implement UOW-001 `HttpPort`
- apply timeout, proxy, headers, request limiter, retry policy, and response classification
- close connection pool and drop in-memory cookies

Lifecycle:

- starts when the client object is created
- ends when the client is closed
- may contain many HTTP requests
- does not persist cookies

### HttpClientLifecycle

Represents caller-owned client scope.

Recommended lifecycle scopes:

- search collector lifecycle
- one post detail scrape lifecycle

Not recommended:

- one cookie-sharing lifecycle for an entire Job
- cookie reuse across resume

### UserAgentProvider

Responsibilities:

- load User-Agent list at runtime creation
- ignore blank lines
- provide default User-Agent fallback
- rotate active User-Agent by request count
- expose whether the active User-Agent changed

State:

- `agents`
- `rotation_interval_requests`
- `request_count`
- `current_index`

### ProxyProvider

Responsibilities:

- resolve proxy from explicit option
- load `.env` only at runtime creation when needed
- validate host presence
- return disabled proxy when invalid or absent
- provide redacted safe label

Inputs:

- explicit proxy option
- execution location
- `.env` file

### RequestRateLimiter

Responsibilities:

- enforce global request interval for one `HttpClient`
- serialize request start times through a single limiter
- apply to first attempts and retries

State:

- `request_interval_seconds`
- `last_request_at`
- internal lock for concurrent workers using the same client

### ResponseClassifier

Responsibilities:

- classify response before parser usage
- detect CAPTCHA markers
- detect block/abnormal access markers
- detect unavailable content markers
- classify retryable HTTP status codes

Inputs:

- status code
- final URL
- headers
- body text or bytes sample

Outputs:

- success
- retryable
- captcha
- blocked
- unavailable

### HeaderBuilder

Responsibilities:

- merge default headers
- apply active User-Agent
- merge caller headers
- apply caller `Referer`

It does not decide parser-specific referer values.

## Request Entities

### HttpRequest

Fields:

- `method`
- `url`
- `params`
- `data`
- `headers`
- `referer`
- `metadata`

### RequestAttempt

Fields:

- `request`
- `attempt_number`
- `started_at`
- `user_agent`
- `proxy_safe_label`

Purpose:

- supports retry decisions and safe logs without exposing secrets

### HttpResponse

Fields:

- `status_code`
- `url`
- `headers`
- `text`
- `content`
- `elapsed_seconds`

UOW-002 returns transport response data only. Domain parsing belongs to later units.

### ResponseClassification

Fields:

- `kind`
- `retryable`
- `error_code`
- `safe_reason`

Kinds:

- `success`
- `retryable`
- `captcha`
- `blocked`
- `unavailable`
- `network_error`

## Error Entities

UOW-002 uses UOW-001 typed exceptions.

| Condition | Exception |
|---|---|
| invalid runtime config | `ValidationFailure` |
| network failure after retries | `NetworkFailureError` |
| CAPTCHA detected | `CaptchaDetectedError` |
| blocked response | `BlockedResponseError` |
| unavailable content | `UnavailableContentError` |

## External Dependencies

### httpx.AsyncClient

Used for:

- async GET
- async POST
- async download
- connection pooling within lifecycle
- in-memory cookie jar within lifecycle
- proxy support through `proxy=...`
- timeout support

Configuration:

- `trust_env=False`
- proxy set from `ProxyProvider`
- timeout set from `TimeoutConfig`

## Relationships To Other Units

| Unit | Relationship |
|---|---|
| UOW-001 | consumes ports, typed exceptions, validation/error contracts |
| UOW-003 | provides HTTP transport for search collection |
| UOW-004 | provides HTTP transport for post/comment/media fetches |
| UOW-005 | surfaces retryable/non-retryable errors for Job lifecycle decisions |
| UOW-007 | receives CLI runtime options but does not duplicate HTTP policy |
| UOW-008 | receives container env but does not duplicate HTTP policy |

