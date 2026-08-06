# Tech Stack Decisions - UOW-002 HTTP Runtime Policy

## Runtime And Language

| Decision | Selection | Rationale |
|---|---|---|
| Language | Python 3.11+ | Matches UOW-001 and supports async runtime typing. |
| Async runtime | `asyncio` | Standard library async foundation for multi-worker scraping. |
| HTTP client | `httpx.AsyncClient` | Supports async requests, timeout config, connection pooling, cookies, and proxy config. |
| Proxy environment trust | `trust_env=False` | Keeps proxy behavior controlled by app config and `.env`, not process-level env variables. |

## Runtime Dependencies

| Dependency | Selection | Scope |
|---|---|---|
| HTTP runtime | `httpx` | Required for async HTTP transport. |
| `.env` parsing | `python-dotenv` | User-confirmed Q6 choice for local `.env` proxy profile loading. |
| Retry/backoff library | Not added | Retry policy is small and local to UOW-002. |
| Browser automation | Not added | UOW-002 is BeautifulSoup/httpx compatible and does not require Playwright. |
| Scraping framework | Not added | Not needed for the shared runtime policy. |

Exact package versions are fixed by the lock file during UOW-002 Code Generation.

## HTTP Configuration

| Area | Decision |
|---|---|
| Timeout default | connect 10s, read 30s, write 30s, pool 10s |
| Retry default | max 3 total attempts |
| Retry statuses | HTTP 429 and 5xx |
| Retry exclusions | CAPTCHA, block, access denied, unavailable content, unsupported response shape |
| Request interval default | 1 second |
| User-Agent rotation default | every 10 requests |
| Cookie storage | in-memory only, per `HttpClient` lifecycle |

## Proxy And `.env`

Proxy variables:

- `DCINSIDE_PROXY_HOST`
- `DCINSIDE_PROXY_ID`
- `DCINSIDE_PROXY_PW`

Resolution priority:

1. explicit runtime proxy option
2. execution-location `.env`
3. disabled

`python-dotenv` is used only at runtime creation time. Package import must not read `.env`.

## Logging And Error Stack

| Decision | Selection |
|---|---|
| Structured logging port | UOW-001 `LoggerPort` |
| Error contract | UOW-001 typed exceptions and `ErrorResult` |
| Secret redaction | UOW-001 `SecretRedactor` plus UOW-002 boundary tests |
| URL logging | query removed or redacted |
| Raw headers/body logging | forbidden by default |

No `structlog` or external logging dependency is added in UOW-002.

## Testing Stack

| Decision | Selection | Rationale |
|---|---|---|
| Example tests | pytest | Existing project test runner. |
| PBT | Hypothesis | Already selected by project extensions. |
| HTTP fake | `httpx.MockTransport` or minimal local fake transport | Avoids live network flakiness in unit tests. |
| Live smoke | env-gated optional test | Keeps CI deterministic. |

Required test categories:

- limiter invariants
- retry bounds
- timeout conversion
- response classification
- resource cleanup
- proxy resolution
- User-Agent rotation
- header merge
- secret redaction
- import side-effect safety

## Deferred Decisions

These are intentionally left for later units:

- final search URL traversal and `search_pos` behavior
- post/comment/media parser selectors
- checkpoint persistence
- Garage/S3 output client
- CLI prompts and terminal UX
- container entrypoint `.env` generation
- full Job throughput targets
