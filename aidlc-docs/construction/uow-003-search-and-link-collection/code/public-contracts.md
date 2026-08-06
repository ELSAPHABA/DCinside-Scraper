# Public Contracts - UOW-003 Search And Link Collection

## Package Exports

Public import path:

- `dcinside_scraper.search`

Primary exports:

- `GallerySearchCollector`
- `IntegratedSearchCollector`
- `NoKeywordRangeCollector`
- `RealtimeCollectionCycle`
- `LinkCollectorService`
- `GallerySearchUrlBuilder`
- `IntegratedSearchUrlBuilder`
- `GallerySearchParser`
- `IntegratedSearchParser`
- `SubjectHeadParser`
- `SearchDateJumpClient`
- `CandidateDeduper`
- `RangeFilterEvaluator`
- `TraversalGuard`
- `SafeCollectorEventBuilder`
- `parse_post_url`

Top-level convenience exports were added for:

- `LinkCollectorService`
- `GallerySearchCollector`
- `IntegratedSearchCollector`
- `GallerySearchUrlBuilder`
- `IntegratedSearchUrlBuilder`
- `CandidateDeduper`

## Public Async API

`dcinside_scraper.core.api.search_gallery(request, http_client)`:

- input: `GallerySearchRequest`
- required dependency: caller-injected UOW-002-compatible `HttpPort`
- output: `GallerySearchPage`
- raises `ValidationFailure` when `http_client` is omitted

`dcinside_scraper.core.api.search_integrated(request, http_client)`:

- input: `IntegratedSearchRequest`
- required dependency: caller-injected UOW-002-compatible `HttpPort`
- output: `IntegratedSearchPage`
- raises `ValidationFailure` when `http_client` is omitted

UOW-003 does not create a default HTTP client in these APIs.

## URL Builders

`GallerySearchUrlBuilder.build(...)`:

- major gallery path: `/board/lists/`
- minor gallery path: `/mgallery/board/lists/`
- mini gallery path: `/mini/board/lists/`
- query keys: `id`, `page`, optional `s_type`, optional `s_keyword`, optional `search_pos`, optional `search_head`
- space is encoded as `%20`

`IntegratedSearchUrlBuilder.build(...)`:

- UTF-8 percent-encodes keyword then replaces `%` with `.`
- clamps page to max 120
- `IntegratedSearchSort.LATEST` maps to `/post/q/<keyword>` and `/post/p/<page>/q/<keyword>`
- `IntegratedSearchSort.RELEVANCE` maps to `/post/sort/accuracy/q/<keyword>` and `/post/p/<page>/sort/accuracy/q/<keyword>`

## Parser Contracts

`GallerySearchParser.parse(...)` extracts:

- post candidates from `tr.ub-content.us-post`
- post number from `.gall_num`
- title/link from `.gall_tit a`
- repost marker from `.gall_tit > b.font_blue009`
- subject head text from `.gall_subject`
- date from `.gall_date[title]` or text
- views and recommendations
- subject head tabs from `a[onclick^="listSearchHead"]`
- page end and next search URL

`IntegratedSearchParser.parse(...)` extracts:

- result rows from `.integrate_cont.sch_result.result_all ul.sch_result_list > li`
- title/detail URL from `a.tit_txt`
- preview text from `p.link_dsc_txt`
- gallery name/link from `p.dsc_sub > a.sub_txt`
- date from `p.dsc_sub > span.date_time`
- gallery ID, gallery type, and post number from the detail URL

Row-level parser failures become `CollectorFailure` records and exclude raw HTML.

## Collector Contracts

`GallerySearchCollector`:

- fetches through injected client only
- traverses page and `search_pos`
- copies `search_next` URLs from parsed HTML
- does not calculate `search_pos`
- validates minor-gallery subject head tabs when present

`IntegratedSearchCollector`:

- fetches through injected client only
- never traverses beyond page 120
- produces both post candidates and gallery candidates

`NoKeywordRangeCollector`:

- starts with blank keyword gallery search
- uses `/ajax/search_ajax/search_date/` only through the same injected client
- treats unsuccessful date jump as empty result with safe stop reason

`DeepSearchCollector`:

- discovers galleries through integrated search
- dedupes galleries by `(gallery_type, gallery_id)`
- sequentially runs gallery keyword search per candidate gallery
- records per-gallery failures without failing the whole result

`RealtimeCollectionCycle`:

- performs one collection cycle only
- excludes candidates already present in the provided seen set
- does not own timer, sleep loop, checkpoint, or queue insertion

## Security And Side Effects

Importing UOW-003 must not:

- make network requests
- read `.env`
- read `user-agents.txt`
- read environment variables
- prompt terminal input
- write files
- create queues
- create `httpx.AsyncClient`

Safe collector events:

- redact URL query strings
- drop `ci_t`
- drop raw HTML/body/content/cookie/header fields

CAPTCHA/block/network handling remains owned by UOW-002 and propagates through typed exceptions.
