# Logical Components - UOW-004 Post Detail And Content Parsing

## Component Overview

UOW-004 logical components scrape one post detail result without storing JSONL, downloading media files, or managing queues/checkpoints.

| Component | Purpose |
|---|---|
| `PostDetailService` | orchestrates detail HTML fetch, parsers, optional subfetches, comments, and final `PostResult` |
| `PostHtmlFetcher` | fetches detail HTML through UOW-002 `HttpClient` |
| `PostMetadataParser` | extracts core metadata and subject head/repost marker |
| `ContentBlockParser` | parses ordered body blocks and media/link metadata |
| `RepostClient` | fetches repost AJAX payload when `(펌)` is detected |
| `RepostParser` | parses original post card metadata and repost content |
| `DcVideoMetadataResolver` | resolves optional DC video iframe metadata |
| `CommentService` | fetches comment pages and returns comments/replies |
| `CommentPaginationGuard` | bounds comment page traversal |
| `CommentAjaxParser` | parses `/board/comment/` JSON |
| `CommentHtmlFallbackParser` | parses rendered fallback comment/reply HTML fixtures |
| `CommentMemoParser` | splits comment text and DCCon metadata |
| `DetailFailureRecorder` | creates safe `detail_failures` records |
| `SafeDetailEventBuilder` | emits sanitized detail parser events through `LoggerPort` |
| `post_detail.normalization` | holds pure normalization helpers used by parsers and PBT |

## PostDetailService

Responsibilities:

- require caller-provided UOW-002 `HttpClient`
- fetch post detail HTML
- parse metadata and content blocks
- resolve optional repost/DC video/comment data
- collect non-fatal failures through `DetailFailureRecorder`
- return one `PostResult`

It does not write files, save checkpoints, create queues, or download media.

## Fetchers And Optional Subfetches

`PostHtmlFetcher` fetches only the primary detail page.

`RepostClient` fetches `/ajax/pum_ajax/get_contents` only when the parser detects `(펌)`.

`DcVideoMetadataResolver` fetches DC video iframe HTML only when a DC video block needs metadata resolution.

All fetches use UOW-002 `HttpClient`. UOW-004 does not create its own HTTP client or retry loop.

## Parsers

`PostMetadataParser` extracts:

- gallery ID
- post ID and number
- subject head metadata
- title
- author and nickname type
- created date
- views
- recommendations
- comment count
- repost marker

`ContentBlockParser` walks `.writing_view_box .write_div` in DOM order and returns:

- content blocks
- media metadata
- links

`RepostParser` fills `RepostInfo` without original comment count.

`CommentAjaxParser` parses root comments and replies from AJAX JSON.

`CommentHtmlFallbackParser` supports saved rendered HTML fixtures:

- `li[id^="comment_li_"]`
- following sibling `ul.reply_list[p-no]`

## CommentPaginationGuard

Responsibilities:

- read pagination/end signals from parsed comment pages
- stop on empty comment pages
- stop at `max_comment_pages`
- return safe stop reason codes

Default:

- `max_comment_pages=100`

Limit result:

- keep the parsed post
- append safe failure reason `comment_page_limit`

## DetailFailureRecorder

Responsibilities:

- collect optional subfetch/subparse failures
- normalize failure fields
- reject raw body and sensitive fields
- append safe entries to `PostResult.metadata["detail_failures"]`

Allowed fields:

- `stage`
- `reason`
- `retryable`
- `field_path`
- `failed_fields`

## SafeDetailEventBuilder

Responsibilities:

- create safe structured parser/service events
- remove raw body, cookie, proxy, and full query values
- emit only stage, counts, booleans, and safe reasons
- use UOW-001 `LoggerPort`

It mirrors the safe event pattern used by earlier HTTP/search units.

## Normalization Module

`post_detail.normalization` contains pure helpers:

- `strip_repost_marker`
- `parse_count`
- `parse_dcinside_date`
- `classify_nickname_type`
- `validate_block_orders`
- `make_safe_detail_failure`

The module has no I/O and is shared by parser code and property-based tests.

## Test Components

Fixture files live under:

- `tests/fixtures/post_detail/`

Property-based strategies live in:

- `tests/strategies/post_detail.py`

Optional live smoke tests live in:

- `tests/test_post_detail_live_smoke.py`

They run only when `DCINSIDE_LIVE_SMOKE_ENABLED=true`.

## Component Flow

1. Caller creates `PostRequest` from direct input or UOW-003 `PostCandidate`.
2. `PostDetailService` fetches detail HTML through `PostHtmlFetcher`.
3. `PostMetadataParser` creates core metadata.
4. `ContentBlockParser` creates body blocks, media metadata, and links.
5. Optional repost and DC video subfetches run through UOW-002 `HttpClient`.
6. `CommentService` fetches comment pages until `CommentPaginationGuard` stops traversal.
7. Non-fatal optional failures are recorded by `DetailFailureRecorder`.
8. `SafeDetailEventBuilder` emits sanitized events when logging is configured.
9. The service returns one `PostResult`.

## Relationships To Other Units

| Unit | Relationship |
|---|---|
| UOW-001 Core Models And Config | provides models, typed errors, and logger port |
| UOW-002 HTTP Runtime Policy | provides async HTTP client, retry, limiter, proxy, User-Agent, cookie lifecycle, and response classification |
| UOW-003 Search And Link Collection | provides `PostCandidate` values that can become `PostRequest` |
| UOW-005 Job Orchestration | later owns queue lifecycle, retries across posts, checkpoint, and cancellation |
| UOW-006 Output And Media Storage | later owns JSONL/Garage output and media download/storage |
| UOW-007 CLI Adapter | later exposes parser/comment/media options |
| Future metadata retry unit | later consumes safe `detail_failures` records for targeted retry |
