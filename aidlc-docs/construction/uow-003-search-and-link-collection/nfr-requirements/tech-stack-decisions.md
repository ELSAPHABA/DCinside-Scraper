# Tech Stack Decisions - UOW-003 Search And Link Collection

## Runtime And Language

| Decision | Selection | Rationale |
|---|---|---|
| Language | Python 3.11+ | Matches existing package and async runtime. |
| HTTP runtime | UOW-002 `HttpClient` | Keeps request delay, retry, proxy, User-Agent, and classification centralized. |
| HTML parser | BeautifulSoup | Required by project constraints and avoids browser automation. |
| URL/query handling | `urllib.parse` | Standard library is enough for URL building and query extraction. |
| JSON handling | stdlib `json` | Enough for no-keyword `search_date` response parsing. |

## Dependency Decisions

| Dependency | Selection | Scope |
|---|---|---|
| BeautifulSoup | `beautifulsoup4` | Search/list fixture parsing. |
| HTTP | reuse `httpx` through UOW-002 | UOW-003 does not create a parallel HTTP stack. |
| Browser automation | Not added | Playwright/Selenium are out of scope. |
| Scraping framework | Not added | Scrapy is unnecessary for this bounded parser/collector unit. |
| Queue/storage/database | Not added | Queue, checkpoint, and storage are later units. |

Exact package versions are fixed by the lock file during UOW-003 Code Generation.

## Parser Strategy

| Area | Decision |
|---|---|
| Gallery search parser | BeautifulSoup selectors from `docs/Function_Specification.md` |
| Integrated search parser | BeautifulSoup selectors from `docs/Function_Specification.md` |
| Subject head parser | parse `a[onclick^="listSearchHead"]` |
| No-keyword date jump | parse JSON response with stdlib `json` |
| Parser failures | row-level failure records where possible |

## Traversal Decisions

| Area | Decision |
|---|---|
| Gallery `search_pos` | copy `a.search_next[href]` as-is; do not calculate from latest post number |
| Gallery page end | `a.page_end[href]`, then largest paging link, then current page |
| Integrated max page | hard max 120 |
| Deep search | integrated discovery then sequential per-gallery keyword search |
| Realtime | one collection cycle only; UOW-005 owns loop and checkpoint |

## Testing Stack

| Decision | Selection | Rationale |
|---|---|---|
| Example tests | pytest | Existing test runner. |
| PBT | Hypothesis | Existing project choice. |
| Fixture format | inline strings or small files under `tests/fixtures/` | Keeps parser tests deterministic. |
| HTTP fake | UOW-002 fake/MockTransport pattern | No live network in default tests. |
| Live smoke | env-gated optional test | Keeps CI deterministic. |

Required test categories:

- gallery URL building
- integrated keyword encoding
- parser fixture extraction
- subject head validation
- no-keyword date jump JSON parsing
- deep-search gallery dedupe
- range filter
- realtime dedupe
- safe logging fields

## Deferred Decisions

These are intentionally left for later units:

- post detail parser selectors
- comment/media/repost card parsing
- queue insertion and worker lifecycle
- checkpoint persistence
- JSONL/Garage output
- CLI options
- container/MCP live smoke wiring
