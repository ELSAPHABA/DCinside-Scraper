# Public Contracts - UOW-004 Post Detail And Content Parsing

## Package Exports

Public import path:

- `dcinside_scraper.post_detail`

Primary exports:

- `PostDetailService`
- `CommentService`
- `PostMetadataParser`
- `ContentBlockParser`
- `RepostClient`
- `RepostParser`
- `DcVideoMetadataResolver`
- `CommentAjaxParser`
- `CommentHtmlFallbackParser`
- `CommentMemoParser`
- `CommentPaginationGuard`
- `DetailFailureRecorder`
- `SafeDetailEventBuilder`
- `strip_repost_marker`
- `parse_count`
- `parse_dcinside_date`
- `classify_nickname_type`
- `validate_block_orders`
- `make_safe_detail_failure`

Top-level convenience exports were added for:

- `PostDetailService`
- `CommentService`
- `PostMetadataParser`
- `ContentBlockParser`

## Public Async API

`dcinside_scraper.core.api.fetch_post(request, http_client)`:

- input: `PostRequest`
- required dependency: caller-injected UOW-002-compatible `HttpPort`
- output: `PostResult`
- raises `ValidationFailure` when `http_client` is omitted

`dcinside_scraper.core.api.fetch_comments(request, http_client)`:

- input: `CommentRequest`
- required dependency: caller-injected UOW-002-compatible `HttpPort`
- output: `list[Comment]`
- raises `ValidationFailure` when `http_client` is omitted

UOW-004 does not create a default HTTP client in these APIs.

## Service Contracts

`PostDetailService.fetch_post(request)`:

- fetches post detail HTML through injected client
- parses core metadata into `PostResult`
- parses ordered content blocks
- resolves DC video iframe metadata when present
- fetches repost AJAX when `(펌)` is detected
- fetches comments when `request.scrape_options.include_comments` is true
- records optional subfetch failures in `PostResult.metadata["detail_failures"]`

`CommentService.fetch_comments(request)`:

- posts to `/board/comment/` through injected client
- parses root comments and replies
- returns flat `Comment` values with `depth` and parent fields

## Parser Contracts

`PostMetadataParser` extracts:

- gallery ID
- post ID and post number
- title with leading `(펌)` removed
- author and nickname type
- created date
- views
- recommendations
- comment count
- subject head metadata
- comment AJAX hidden params when present

`ContentBlockParser` extracts:

- `TextBlock`
- `ImageBlock`
- `DcVideoBlock`
- `YouTubeBlock`
- `LinkBlock`
- `SeriesBlock`
- `UnknownEmbedBlock`

`RepostParser` extracts:

- original gallery ID/name
- original post ID/number
- original author and nickname type
- views
- recommendations
- repost body content blocks

Original post comment count is not stored in `RepostInfo`.

`CommentAjaxParser` extracts:

- comment number
- parent comment number for replies
- depth
- author data
- memo text
- dccon metadata
- created date
- deletion metadata

`CommentHtmlFallbackParser` supports saved rendered HTML fixtures:

- `li[id^="comment_li_"]`
- following sibling `ul.reply_list[p-no]`

## Guardrails

`ScrapeOptions.max_comment_pages`:

- default: `100`
- minimum: `1`
- used by `CommentPaginationGuard`

`CommentPaginationGuard` stops on:

- empty page
- pagination end
- configured max page limit

When the max page limit is reached inside post detail collection, a safe `detail_failures` entry records `comment_page_limit`.

## Security And Side Effects

Importing UOW-004 must not:

- make network requests
- read `.env`
- read `user-agents.txt`
- read environment variables
- prompt terminal input
- write files
- create queues
- create `httpx.AsyncClient`
- download media files

Safe detail failures include only:

- `stage`
- `reason`
- `retryable`
- `field_path`
- `failed_fields`

Safe detail events:

- redact URL query strings
- drop raw HTML/body/content/cookie/header/proxy fields

CAPTCHA/block/network handling remains owned by UOW-002 and propagates through typed exceptions where appropriate.
