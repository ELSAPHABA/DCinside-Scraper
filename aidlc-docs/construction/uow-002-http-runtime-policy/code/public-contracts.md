# Public Contracts - UOW-002 HTTP Runtime Policy

## Package Exports

UOW-002 adds the import-safe package:

- `dcinside_scraper.http`

Top-level convenience exports added to `dcinside_scraper`:

- `HttpClient`
- `HttpRuntimeConfig`
- `ProxyConfig`
- `RuntimePolicyService`
- `UserAgentConfig`

Importing these modules must not read `.env`, read `user-agents.txt`, prompt terminal input, write files, or make network requests.

## Runtime Config

### `HttpRuntimeConfig`

Fields:

- `request_interval_seconds`
- `timeout`
- `retry_policy`
- `user_agent`
- `proxy`
- `proxy_env_path`
- `execution_dir`
- `default_headers`

Defaults:

- request interval: 1 second
- timeout: connect 10s, read 30s, write 30s, pool 10s
- retry: max 3 attempts
- User-Agent rotation: every 10 requests
- proxy: explicit option, `.env`, then disabled

### `TimeoutConfig`

Converts to `httpx.Timeout`.

### `RetryPolicy`

Defines:

- `max_attempts`
- `backoff_base_seconds`
- `backoff_max_seconds`
- retry status codes
- timeout/network retry flags

## Proxy Contract

### `ProxyConfig`

Represents resolved proxy settings.

Rules:

- disabled proxy returns `None` for `httpx`
- safe label never includes username or password
- credential proxy URL is only built for `httpx`, not logs

### `DotenvProxyLoader`

Reads only these keys with `dotenv_values(path)`:

- `DCINSIDE_PROXY_HOST`
- `DCINSIDE_PROXY_ID`
- `DCINSIDE_PROXY_PW`

It does not call `load_dotenv()` and does not mutate `os.environ`.

### `ProxyProvider`

Resolution priority:

1. explicit runtime proxy option
2. `.env`
3. disabled

## User-Agent Contract

### `UserAgentProvider`

Resolution priority:

1. explicit file path
2. execution-location `user-agents.txt`
3. built-in default User-Agent

Rules:

- one User-Agent per nonblank line
- rotation interval is request-count based
- `next_for_request()` returns `(user_agent, changed)`
- `HttpClient` clears cookies when `changed=True`

## HTTP Client Contract

### `HttpClient`

Public async methods:

- `get(url, *, headers=None, params=None, referer=None)`
- `post(url, *, data=None, headers=None, referer=None)`
- `download(url, *, headers=None)`
- `request(method, url, *, params=None, data=None, headers=None, referer=None)`
- `close()`

Return value for request methods:

- `HttpResponse`

`download()` returns `bytes`.

### `HttpResponse`

Fields:

- `status_code`
- `url`
- `headers`
- `text`
- `content`
- `elapsed_seconds`

## Classification Contract

### `ResponseClassifier`

Inputs:

- status code
- final URL
- headers
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
| retry exhausted/network | `NetworkFailureError` |

CAPTCHA/block/unavailable classifications are not retried.

## Logging Contract

### `SafeHttpEventBuilder`

Safe event fields may include:

- event name
- URL without query string
- proxy enabled state
- proxy source
- redacted proxy label
- method
- attempt
- status code
- classification
- delay seconds

Forbidden values:

- raw `.env`
- proxy password
- credential proxy URL
- raw cookies
- raw headers
- raw body/content

## Testing Contract

Default tests use:

- `httpx.MockTransport`
- fake clock
- fake async sleeper
- Hypothesis strategies

Live DCinside smoke testing is not part of default tests or mandatory CI.
