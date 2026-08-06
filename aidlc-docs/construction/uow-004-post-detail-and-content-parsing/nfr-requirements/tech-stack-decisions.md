# Tech Stack Decisions - UOW-004 Post Detail And Content Parsing

## Runtime And Language

| Decision | Selection | Rationale |
|---|---|---|
| Language | Python 3.11+ | Matches existing package and async runtime. |
| HTTP runtime | UOW-002 `HttpClient` | Keeps delay, retry, proxy, User-Agent, cookie lifecycle, and CAPTCHA/block classification centralized. |
| HTML parser | BeautifulSoup | Required by project constraints and avoids browser automation. |
| JSON handling | stdlib `json` | Enough for comment and repost AJAX response parsing. |
| URL/query handling | `urllib.parse` | Standard library is enough for URL extraction and normalization. |

## Dependency Decisions

| Dependency | Selection | Scope |
|---|---|---|
| BeautifulSoup | `beautifulsoup4` | Detail HTML, repost AJAX HTML, DC video iframe HTML, rendered comment fallback parsing. |
| HTTP | reuse `httpx` through UOW-002 | UOW-004 does not create a parallel HTTP stack. |
| Browser automation | Not added | Playwright/Selenium are out of scope. |
| Scraping framework | Not added | Scrapy is unnecessary for this bounded parser/service unit. |
| Queue/storage/database | Not added | Queue, checkpoint, and storage are later units. |
| Media download tooling | Not added | UOW-004 records media metadata only; downloads belong to UOW-006. |

Exact package versions are fixed by the lock file during UOW-004 Code Generation.

## Parser Strategy

| Area | Decision |
|---|---|
| Detail metadata parser | BeautifulSoup selectors from `docs/Function_Specification.md` |
| Content block parser | DOM-order walk of `.writing_view_box .write_div` |
| Repost parser | Direct `/ajax/pum_ajax/get_contents` response parsing |
| DC video parser | Optional iframe HTML metadata resolution |
| Comment parser | `/board/comment/` AJAX JSON primary source |
| Comment fallback | Rendered HTML fixture parser for `li[id^="comment_li_"]` and sibling `ul.reply_list[p-no]` |
| DCCon parser | BeautifulSoup parse of `memo` HTML for `img.written_dccon` and `video.written_dccon` |
| Parser failures | typed core failures for fatal metadata issues; safe `detail_failures` for optional failures |

## Boundary Decisions

| Area | Decision |
|---|---|
| Retry | UOW-002 owns retry; UOW-004 does not add nested retry loops |
| Comment limit | default `max_comment_pages=100` guardrail |
| Raw HTML retention | not stored in production `PostResult` or logs |
| Failure metadata | `stage`, `reason`, `retryable`, `field_path`, `failed_fields` only |
| Memory | one post plus active subresponses only |
| Media files | metadata only; no file download |
| Live smoke | optional env-gated test only |

## Testing Stack

| Decision | Selection | Rationale |
|---|---|---|
| Example tests | pytest | Existing test runner. |
| PBT | Hypothesis | Existing project choice. |
| Fixture format | small files under `tests/fixtures/` | Keeps parser tests deterministic and readable. |
| HTTP fake | UOW-002 fake/MockTransport pattern | No live network in default tests. |
| Live smoke | env-gated optional test | Keeps CI deterministic. |

Required test categories:

- post metadata fixture parsing
- mixed content block fixture parsing
- repost AJAX fixture parsing
- DC video iframe fixture parsing
- comment AJAX fixture parsing
- rendered comment HTML fallback parsing
- missing optional field handling
- partial failure metadata shape
- title/count/date/nickname normalization properties

## Deferred Decisions

These are intentionally left for later units:

- JSONL/Garage output
- media file download and object keys
- checkpoint persistence
- queue insertion and worker lifecycle
- CLI options
- container/MCP live smoke wiring
- metadata parsing failure retry storage and orchestration
