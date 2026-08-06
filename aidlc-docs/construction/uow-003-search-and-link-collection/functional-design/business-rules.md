# Business Rules - UOW-003 Search And Link Collection

## Runtime Boundary Rules

### BR-003-001. Import Side Effects

Importing UOW-003 modules must not:

- make network requests
- read `.env`
- read `user-agents.txt`
- prompt terminal input
- write files
- create queues

### BR-003-002. HTTP Boundary

All network I/O must go through UOW-002 `HttpClient`.

UOW-003 must not create a separate `httpx.AsyncClient`, use `requests`, or use Playwright.

### BR-003-003. Queue Boundary

UOW-003 returns candidates through async iterator/list APIs.

`asyncio.Queue` ownership belongs to UOW-005.

## Candidate Rules

### BR-003-004. Candidate Key

Primary candidate dedupe key is:

- `(gallery_id, post_number)`

If `post_number` cannot be parsed, the collector may use a normalized detail URL fallback, but parser code must first attempt query `no`.

### BR-003-005. Direct URL Normalization

Direct post URLs must be normalized into `PostCandidate` values by parsing:

- gallery type from path
- gallery ID from `id`
- post number from `no`

Non-DCinside post URLs are rejected by UOW-001 validation.

### BR-003-006. No Storage

UOW-003 does not write JSONL, media files, failure records, checkpoints, or Job reports.

## Gallery Search Rules

### BR-003-007. Gallery Path

Major gallery list path:

- `/board/lists/`

Minor gallery list path:

- `/mgallery/board/lists/`

### BR-003-008. Gallery Search Parameters

Gallery search requests use:

- `id`
- `s_type`
- `s_keyword`
- `page`
- optional `search_pos`
- optional `search_head`

### BR-003-009. Initial `search_pos`

The first gallery search request omits `search_pos` or sends it blank.

The collector must not calculate `search_pos` from latest post number.

### BR-003-010. Segment Traversal

Within the current `search_pos` segment:

1. start at `page=1`
2. continue until page end
3. then follow `a.search_next[href]`
4. restart page traversal from `page=1` for the next segment

### BR-003-011. Page End Detection

Page end is determined by:

1. `a.page_end[href]`
2. largest page number in paging links
3. current page if neither exists

### BR-003-012. Row Inclusion

The parser includes only rows matching:

- `.gall_listwrap.list tbody tr.ub-content.us-post`

Rows are ignored when:

- `us-post` class is absent
- `.gall_num` text is `-`
- post number cannot be parsed

### BR-003-013. List Repost Marker

A row is marked `is_repost=true` only when:

- `.gall_tit > b.font_blue009` text is exactly `(펌)`

`.gall_tit span.mark` alone must not mark repost.

### BR-003-014. Subject Head Filter

Subject head filter uses `search_head`.

`sort_type` must not be used as subject head ID.

Major galleries fail validation if a subject head filter is requested.

## Subject Head Rules

### BR-003-015. Subject Head Tab Parsing

Minor gallery subject head tabs are parsed from:

- `a[onclick^="listSearchHead"]`

The numeric argument in `listSearchHead(<ID>)` is the subject head ID.

### BR-003-016. Subject Head Validation

Requested subject head is invalid when:

- parsed tab IDs do not include it
- response URL drops `search_head`
- active tab for the requested ID is missing

HTTP 200 alone is not a successful validation signal.

### BR-003-017. Subject Head Fallback

Fallback probing by `search_head=N` increments of 10 is allowed only when DOM tab parsing is unavailable.

Fallback success still requires active tab or matching subject evidence.

## Integrated Search Rules

### BR-003-018. Keyword Encoding

Integrated search keyword encoding is:

1. UTF-8 percent encoding
2. replace `%` with `.`

Example:

- `싱글벙글` -> `.EC.8B.B1.EA.B8.80.EB.B2.99.EA.B8.80`

### BR-003-019. Integrated URL Forms

Latest:

- page 1: `/post/q/<keyword>`
- page 2+: `/post/p/<page>/q/<keyword>`

Accuracy:

- page 1: `/post/sort/accuracy/q/<keyword>`
- page 2+: `/post/p/<page>/sort/accuracy/q/<keyword>`

### BR-003-020. Integrated Page Limit

Integrated search traversal must not request page greater than 120.

### BR-003-021. Integrated Result Parsing

Integrated result parser extracts:

- detail URL
- title
- preview
- gallery name
- gallery URL
- created date
- gallery ID
- post number
- gallery type

## Range Rules

### BR-003-022. Range Inclusion

A candidate is included only when it satisfies all configured bounds:

- `date_from <= created_at <= date_to`
- `min_post_number <= post_number <= max_post_number`

Missing candidate date is not enough to reject by date unless the mode requires date-based termination.

### BR-003-023. Range Termination

For descending list/search results, traversal may stop when:

- candidate date is older than `date_from`
- candidate post number is lower than `min_post_number`

The collector skips candidates newer than `date_to` or greater than `max_post_number` and continues.

## No-Keyword Rules

### BR-003-024. No-Keyword Initial Search

No-keyword range collection starts with:

- `s_type=search_subject_memo`
- `s_keyword=%20`

### BR-003-025. Date Jump AJAX

If `date_to` exists, date jump uses:

- `POST https://gall.dcinside.com/ajax/search_ajax/search_date/`

Form data:

- `ci_t`
- `date`
- `id`
- `keyword=`
- `s_type=search_subject_memo`
- `_GALLTYPE_`

Successful `data` becomes `search_pos`.

## Deep Search Rules

### BR-003-026. Deep Search Required Range

Deep search requires at least one date or post-number range.

UOW-001 validates this. UOW-003 must not silently run unbounded deep search.

### BR-003-027. Deep Search Gallery Discovery

Deep search gallery candidates are discovered through integrated search, up to page 120.

Gallery dedupe key:

- `(gallery_type, gallery_id)`

### BR-003-028. Deep Search Partial Failure

Failure in one candidate gallery does not fail the whole deep search.

The collector records:

- gallery ID
- gallery type
- safe reason

## Realtime Rules

### BR-003-029. Realtime Cycle Only

UOW-003 implements a single collection cycle for realtime modes.

UOW-005 owns loop, sleep, termination, checkpoint, and queue insertion.

### BR-003-030. Realtime Dedupe

Realtime cycle must not return candidates already present in the provided dedupe set.

## Error Rules

### BR-003-031. Safe Errors

Parser and collector failures must use UOW-001 typed exceptions or safe failure records.

Raw HTML, raw cookies, proxy credentials, and full URLs with sensitive query values must not be logged.

### BR-003-032. CAPTCHA And Block Propagation

CAPTCHA/block errors from UOW-002 are not swallowed by UOW-003.

They propagate to UOW-005 so the Job can stop and save checkpoint.
