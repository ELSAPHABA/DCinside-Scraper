# Domain Entities - UOW-004 Post Detail And Content Parsing

## Entity Overview

UOW-004 uses the existing core models where possible. Names below describe implementation contracts, not final file names.

## Service Components

### PostDetailService

Responsibilities:

- accept `PostRequest`
- use injected `HttpClient`
- fetch detail HTML
- call metadata, content, repost, video, and comment parsers
- return `PostResult`

Collaborators:

- `PostHtmlFetcher`
- `PostMetadataParser`
- `ContentBlockParser`
- `RepostClient`
- `RepostParser`
- `DcVideoMetadataResolver`
- `CommentService`

### PostHtmlFetcher

Responsibilities:

- fetch the post detail URL
- pass through CAPTCHA/block/network exceptions from UOW-002
- return HTML text only

### CommentService

Responsibilities:

- accept `CommentRequest`
- fetch `/board/comment/` AJAX JSON through `HttpClient`
- parse root comments and replies
- return `list[Comment]`

## Parser Components

### PostMetadataParser

Input:

- detail HTML
- `PostRequest`
- final response URL when available

Output:

- parsed values for `PostResult`

Extracts:

- gallery ID
- post ID and post number
- subject head metadata
- title
- repost marker
- author and nickname type
- created date
- views
- recommendations
- comment count

### ContentBlockParser

Input:

- `.writing_view_box .write_div` BeautifulSoup node
- base URL

Output:

- ordered `ContentBlock` list
- `MediaItem` list
- `ContentLink` list

Supported block types:

- `TextBlock`
- `ImageBlock`
- `DcVideoBlock`
- `YouTubeBlock`
- `LinkBlock`
- `SeriesBlock`
- `UnknownEmbedBlock`

### RepostClient

Responsibilities:

- detect AJAX parameters from repost script
- request `/ajax/pum_ajax/get_contents`
- return AJAX HTML or JSON payload for parser use

### RepostParser

Responsibilities:

- parse original post card metadata into `RepostInfo`
- parse repost body content with `ContentBlockParser`
- exclude original comment count

### DcVideoMetadataResolver

Responsibilities:

- fetch DC video iframe HTML when block metadata is incomplete
- parse video URL, thumbnail/poster URL, download URL, and description
- return partial metadata when optional fields are absent

### CommentAjaxParser

Input:

- `/board/comment/` AJAX response

Output:

- `list[Comment]`

Responsibilities:

- parse comment IDs and numbers
- map depth and parent IDs
- parse author information
- delegate `memo` parsing to `CommentMemoParser`

### CommentHtmlFallbackParser

Input:

- rendered comment HTML fixture

Output:

- `list[Comment]`

Responsibilities:

- parse `li[id^="comment_li_"]`
- parse replies from following `ul.reply_list[p-no]`
- preserve root/reply relationship

### CommentMemoParser

Responsibilities:

- convert plain memo to `memo_text`
- parse HTML memo with BeautifulSoup
- extract `DcconItem` metadata
- avoid media downloads

### DetailFailureRecorder

Responsibilities:

- collect non-fatal subfetch/subparse failures
- store safe records in `PostResult.metadata["detail_failures"]`
- avoid raw HTML, cookies, credentials, and sensitive query values

## Data Entities

### PostRequest

Existing UOW-001 request model used as input.

Fields used by UOW-004:

- `url`
- `gallery_type`
- `gallery_id`
- `post_id`
- `post_number`
- `scrape_options`

### CommentRequest

Existing request model for comment-only fetching.

Fields used by UOW-004:

- `gallery_id`
- `post_id`
- `post_number`
- `gallery_type`

### PostResult

Primary output entity.

UOW-004 fills:

- `gallery_id`
- `post_id`
- `post_number`
- `is_repost`
- `repost`
- `title`
- `author`
- `nickname_type`
- `date`
- `views`
- `recommendations`
- `comment_count`
- `content`
- `images`
- `comments`
- `links`
- `metadata`

### RepostInfo

Original post metadata for `(펌)` posts.

Fields:

- `gallery_id`
- `gallery_name`
- `post_id`
- `post_number`
- `author`
- `nickname_type`
- `views`
- `recommendations`

### ContentBlock

Discriminated union used for ordered body content.

Variants:

- `TextBlock`
- `ImageBlock`
- `DcVideoBlock`
- `YouTubeBlock`
- `LinkBlock`
- `SeriesBlock`
- `UnknownEmbedBlock`

### MediaItem

Post-level media metadata.

Used for:

- images
- DC videos
- later media download handoff

### Comment

Comment or reply entity.

Root comments use `depth=0`.

Replies use `depth=1` and preserve parent fields.

### DcconItem

DCCon metadata entity attached to `Comment.dccons`.

UOW-004 stores metadata only.

### DetailFailure

Stored as a dict inside `PostResult.metadata["detail_failures"]`.

Fields:

- `stage`
- `reason`
- `retryable`
- `field_path`

Purpose:

- preserve safe partial failure context
- support future metadata parsing failure retry without adding storage ownership to UOW-004

## Relationships To Other Units

| Unit | Relationship |
|---|---|
| UOW-001 | consumes `PostRequest`, `CommentRequest`, `PostResult`, `Comment`, content/media models, typed errors |
| UOW-002 | uses injected `HttpClient` for all network I/O and propagates CAPTCHA/block errors |
| UOW-003 | receives `PostCandidate` values that can be converted to `PostRequest` |
| UOW-005 | owns queue lifecycle, realtime loops, checkpoint handling, and retry orchestration |
| UOW-006 | owns JSONL/Garage storage and media file download/storage |
| UOW-007 | exposes CLI options for detail/comment/media behavior later |
| Future retry unit | consumes safe metadata parse failure records for targeted post retry |
