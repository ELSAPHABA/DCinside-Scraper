# Logical Components - UOW-003 Search And Link Collection

## Component Overview

UOW-003 logical components collect post links from gallery search, integrated search, no-keyword ranges, realtime modes, and deep search without scraping post detail content.

| Component | Purpose |
|---|---|
| `LinkCollectorService` | orchestrates selected collection mode and returns post candidates |
| `GallerySearchCollector` | traverses gallery list/search pages, including `search_pos` segments |
| `IntegratedSearchCollector` | traverses integrated search results with the page 120 cap |
| `NoKeywordRangeCollector` | collects by gallery, date range, and post-number range without a keyword |
| `DeepSearchCollector` | discovers galleries from integrated search, then runs gallery keyword collection per gallery |
| `RealtimeCollectionCycle` | repeats configured realtime collection until timer or end time |
| `TraversalGuard` | enforces page, segment, and seen-candidate bounds |
| `GalleryListParser` | parses gallery list rows into post candidates and row failures |
| `IntegratedSearchParser` | parses integrated search rows into post candidates and gallery hints |
| `SearchDateNavigator` | resolves date quick-move inputs/responses for no-keyword date traversal |
| `CandidateDeduper` | removes duplicate candidates within one job |
| `DateParser` | parses list dates with explicit precision metadata |
| `SafeCollectorEventBuilder` | emits redacted collector events through `LoggerPort` |

## LinkCollectorService

Responsibilities:

- select collection mode from validated config
- create collector dependencies
- run exactly one configured collection job
- return ordered, deduped post candidates
- surface typed validation/runtime errors

It does not parse post detail pages, scrape comments, download media, or write output files.

## Collectors

`GallerySearchCollector` handles gallery keyword and subject-head collection. It uses `search_pos` from discovered next-search links instead of inventing segment values.

`IntegratedSearchCollector` handles integrated search URLs and stops at page 120 even when a higher page is requested.

`NoKeywordRangeCollector` uses the blank keyword query and date quick-move response path, then applies date and post-number range checks.

`DeepSearchCollector` first discovers candidate galleries from integrated results, then runs gallery keyword collection for each discovered gallery within the required date or post-number range.

`RealtimeCollectionCycle` repeats gallery/integrated collection until exactly one configured termination condition is met: runtime seconds or end time.

## TraversalGuard

Responsibilities:

- enforce integrated page cap
- enforce optional `max_pages`
- enforce optional `max_segments`
- enforce optional `max_seen_candidates`
- return safe decision reason codes

The guard is shared by all collectors that can loop.

## Parsers

Parsers accept HTML text and return `ParserResult`.

`ParserResult` fields:

- `candidates`
- `failures`
- optional `next_page_url`
- optional `next_search_pos`
- optional `gallery_hints`

`CollectorFailure` excludes raw HTML and stores only row index, parser stage, safe reason, and `retryable=false`.

## CandidateDeduper

Responsibilities:

- dedupe by `(gallery_id, post_number)`
- fall back to normalized URL only when the structured key is unavailable
- keep state per job
- raise typed error when the configured seen bound is exceeded

No SQLite or persistent dedupe store is included in UOW-003.

## DateParser

Responsibilities:

- parse absolute date and datetime text
- mark date-only values separately
- mark relative or ambiguous values as `ambiguous`
- mark parse failures as `unknown`

Only absolute and date-only values drive strong range termination.

## SafeCollectorEventBuilder

Responsibilities:

- redact URL query strings
- exclude raw HTML/body and `ci_t`
- emit counts, page numbers, segment numbers, mode, and safe reason codes
- use UOW-001 `LoggerPort`

It mirrors UOW-002 safe HTTP event handling for collector-level events.

## Test Components

Fixture files live under `tests/fixtures/search/`.

Property-based strategies live in `tests/strategies/search.py`.

Optional live smoke tests live in `tests/test_search_live_smoke.py` and run only when `DCINSIDE_LIVE_SMOKE_ENABLED=true`.

## Component Flow

1. `LinkCollectorService` receives validated mode config.
2. The selected collector requests pages through UOW-002 `HttpClient`.
3. The collector passes HTML or date response content to a parser/navigator.
4. Parsed candidates flow through `DateParser`, range checks, `TraversalGuard`, and `CandidateDeduper`.
5. Safe collector events are emitted through `SafeCollectorEventBuilder`.
6. The service returns final candidates for later post-detail scraping units.

## Relationships To Other Units

| Unit | Relationship |
|---|---|
| UOW-001 Core Models And Config | provides validated config, typed errors, and logger port |
| UOW-002 HTTP Runtime Policy | provides async HTTP client, retry, limiter, proxy, User-Agent, and response classification |
| Later post scraping units | consume UOW-003 post candidates and scrape detail/comment/media content |
| Later output units | persist candidates, checkpoints, JSONL, media, and object storage artifacts |
