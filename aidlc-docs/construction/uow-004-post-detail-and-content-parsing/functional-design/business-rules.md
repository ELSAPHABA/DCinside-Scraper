# Business Rules - UOW-004 Post Detail And Content Parsing

## Runtime Boundary Rules

### BR-004-001. Import Side Effects

Importing UOW-004 modules must not:

- make network requests
- read `.env`
- read `user-agents.txt`
- prompt terminal input
- write files
- create queues
- download media files

### BR-004-002. HTTP Boundary

All network I/O must go through UOW-002 `HttpClient`.

UOW-004 must not create a separate `httpx.AsyncClient`, use `requests`, or use Playwright.

### BR-004-003. Storage Boundary

UOW-004 must not write JSONL, media files, failure records, checkpoints, or Job reports.

## Service Rules

### BR-004-004. Detail Service Contract

`PostDetailService` returns exactly one `PostResult` for a successful `PostRequest`.

`fetch_post` and `fetch_comments` require caller-provided HTTP client injection.

### BR-004-005. Request Fallback Values

`PostRequest.gallery_id`, `post_id`, and `post_number` are fallback values.

Parsed detail HTML values take precedence when present and valid.

## Metadata Rules

### BR-004-006. Required Metadata

A post fails with a typed parse error when valid `PostResult` construction is impossible because required metadata is missing:

- gallery ID
- post ID
- title
- author

### BR-004-007. Subject Head Metadata

Minor gallery subject head data is stored under `PostResult.metadata["subject_head"]` when present.

Major galleries may leave subject head metadata absent or `null`.

### BR-004-008. Title Repost Marker

Stored JSON title must not include a leading `(펌)` marker.

The marker affects `is_repost` only.

### BR-004-009. Nickname Type

Author nickname type maps to existing `NicknameType` values:

- fixed nickname -> `fixed`
- semi-fixed nickname -> `semi_fixed`
- guest/IP nickname -> `guest`
- unknown/ambiguous -> `unknown`

## Content Block Rules

### BR-004-010. Content Root

Body parsing starts at `.writing_view_box .write_div`.

If the root is missing, the post can still be returned with an empty `content` list only when required metadata is valid.

### BR-004-011. DOM Order

Content blocks must preserve DOM order.

`order` values must be unique and start at `0`.

### BR-004-012. Noise Removal

The parser ignores known non-content nodes:

- `.img_comment`
- `.image_comment`
- `.tip_box2`
- `.num.img`
- `button`
- `script`
- empty whitespace-only nodes

### BR-004-013. Text Blocks

Text nodes and text-bearing elements become `TextBlock` values after whitespace normalization.

Empty text is ignored.

### BR-004-014. Image Blocks

Image content becomes `ImageBlock` and `MediaItem(media_type="image")`.

UOW-004 records URL, source/original URL, alt/title metadata, and order. File path and object key remain `null` unless provided by later storage units.

### BR-004-015. DC Video Blocks

DC video embeds become `DcVideoBlock` and `MediaItem(media_type="dc_video")`.

UOW-004 may resolve iframe HTML to collect:

- video URL
- thumbnail/poster URL
- download URL
- optional description

Missing description is stored as `null`.

### BR-004-016. YouTube Blocks

YouTube iframe or link embeds become `YouTubeBlock`.

The parser extracts normalized URL and `video_id` when possible.

### BR-004-017. Link Blocks

Ordinary external or internal anchors become `LinkBlock` and are also collected in `PostResult.links`.

### BR-004-018. Series Blocks

DCinside series cards become `SeriesBlock`.

Known linked post URLs are parsed into metadata when available.

### BR-004-019. Unknown Embeds

Unsupported embeds become `UnknownEmbedBlock`.

Unknown embeds must not fail the whole post.

## Repost Rules

### BR-004-020. Repost Detection

The parser marks `is_repost=true` when either condition exists:

- `h3.title > b.font_blue009` text is exactly `(펌)`
- `.write_div script` references `/ajax/pum_ajax/get_contents`

### BR-004-021. Repost AJAX

Repost AJAX is requested directly through `HttpClient`.

JavaScript execution is not required.

### BR-004-022. Repost Metadata

`RepostInfo` records original post:

- gallery ID
- gallery name when available
- post number
- author
- nickname type
- views
- recommendations

Original post comment count is not recorded.

### BR-004-023. Repost Partial Failure

If repost AJAX fails, `PostResult` may still be returned with `is_repost=true` and a safe `detail_failures` entry.

## Comment Rules

### BR-004-024. Comment Source

`/board/comment/` AJAX JSON is the primary comment source.

Rendered HTML comment parsing is allowed only as a fixture/fallback parser.

### BR-004-025. Comment Depth

Comment depth maps as:

- `depth == 0`: root comment
- `depth == 1`: reply

Reply comments must preserve `parent_comment_id` or parent comment number when available.

### BR-004-026. Comment Memo

Plain memo content becomes `Comment.memo_text`.

HTML memo content is parsed with BeautifulSoup before text extraction.

### BR-004-027. DCCon Metadata

`img.written_dccon` and `video.written_dccon` become `DcconItem` values.

UOW-004 stores only safe metadata:

- `src`
- `data-src` resolved as source when needed
- `alt`
- `title`
- `conalt`

## Error Rules

### BR-004-028. Partial Failure Metadata

Optional subfetch and subparse failures are stored in `PostResult.metadata["detail_failures"]`.

Safe failure fields are:

- `stage`
- `reason`
- `retryable`
- `field_path`

### BR-004-029. CAPTCHA And Block Propagation

CAPTCHA and block errors from UOW-002 are not swallowed.

They propagate to UOW-005 so the Job can stop and save checkpoint.

### BR-004-030. Safe Logging

Raw HTML, raw cookies, proxy credentials, and sensitive query values must not be logged or placed in failure metadata.

### BR-004-031. Future Retry Boundary

UOW-004 may produce enough safe failure metadata for a future metadata parsing failure retry unit.

UOW-004 does not own that retry unit or its storage.
