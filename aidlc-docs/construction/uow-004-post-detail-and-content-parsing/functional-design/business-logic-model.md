# Business Logic Model - UOW-004 Post Detail And Content Parsing

## Purpose

UOW-004 turns a DCinside post URL or `PostCandidate` into a `PostResult`.

This unit owns detail page fetch, metadata parsing, ordered body block parsing, repost metadata parsing, DC video metadata resolution, and comment/reply parsing. It does not own JSONL storage, media file download, checkpoint persistence, queue lifecycle, CLI prompts, or container/MCP hosting.

## Confirmed Decisions

| Area | Decision |
|---|---|
| Detail service contract | `PostDetailService` receives `PostRequest` plus injected UOW-002 `HttpClient` and returns `PostResult`; public `fetch_post`/`fetch_comments` require HTTP client injection |
| Metadata parser | BeautifulSoup parser extracts title, subject head, author, nickname type, date, views, recommendations, comment count, gallery ID, post number, and repost marker |
| Ordered content | `.writing_view_box .write_div` DOM order becomes `TextBlock`, `ImageBlock`, `DcVideoBlock`, `YouTubeBlock`, `LinkBlock`, `SeriesBlock`, or `UnknownEmbedBlock` |
| Media boundary | UOW-004 records URL/metadata only; file download and storage belong to UOW-006 |
| DC video | UOW-004 may fetch DC video iframe HTML to resolve video URL, poster URL, download URL, and optional description |
| Repost `(펌)` | Detect marker, strip `(펌)` from stored title, fetch `/ajax/pum_ajax/get_contents`, parse original post metadata and repost content blocks; original comment count is not stored |
| Comments | `/board/comment/` AJAX JSON is primary; rendered HTML comment/reply structure is a fixture/fallback parser |
| Comment memo/dccon | `memo` is split into `memo_text` and `DcconItem` metadata |
| Partial failure | Core detail HTML/core metadata failure fails the post; optional subfetch failures are recorded in `PostResult.metadata["detail_failures"]` |

## Post Detail Flow

1. Caller builds `PostRequest` from direct URL or UOW-003 `PostCandidate`.
2. Caller provides a UOW-002 `HttpClient`; UOW-004 does not create its own client.
3. `PostDetailService` fetches the detail HTML.
4. `PostMetadataParser` parses core post metadata.
5. `ContentBlockParser` parses ordered body blocks and media metadata.
6. If repost marker exists, `RepostClient` fetches repost AJAX content and `RepostParser` fills `RepostInfo`.
7. If DC video blocks require iframe resolution, `DcVideoMetadataResolver` fetches only the metadata HTML.
8. If `ScrapeOptions.include_comments` is true, `CommentService` fetches and parses comments/replies.
9. `PostDetailService` returns one `PostResult`.

## Metadata Flow

`PostMetadataParser` extracts:

- `gallery_id`
- `post_id`
- `post_number`
- `subject_head` into `metadata["subject_head"]`
- title with leading `(펌)` removed
- author name, user ID/IP, and `NicknameType`
- created date
- view count
- recommendation upvote/downvote counts
- comment count
- `is_repost`

The parser prefers explicit DOM fields from the detail page. If `PostRequest` already contains gallery ID or post number, those values are fallback inputs only.

## Ordered Content Flow

`ContentBlockParser` walks `.writing_view_box .write_div` in DOM order.

The parser removes known noise before creating blocks:

- `.img_comment`
- `.image_comment`
- `.tip_box2`
- `.num.img`
- buttons
- scripts
- empty layout nodes

Block rules:

- text nodes become `TextBlock`
- image tags and image links become `ImageBlock`
- DC video embeds become `DcVideoBlock`
- YouTube iframe/link embeds become `YouTubeBlock`
- normal anchors become `LinkBlock`
- DCinside series cards become `SeriesBlock`
- unsupported embeds become `UnknownEmbedBlock`

The `order` field is dense and unique within one post.

## Repost Flow

Repost detection uses either:

- `h3.title > b.font_blue009` with text `(펌)`
- a `.write_div script` call to `/ajax/pum_ajax/get_contents`

When repost is detected:

1. Stored `PostResult.title` removes the leading `(펌)`.
2. The AJAX endpoint is requested directly through `HttpClient`.
3. Original post gallery, post number, author, nickname type, views, and recommendations are parsed into `RepostInfo`.
4. Original post comment count is ignored.
5. Repost body media/content is parsed with the same content block parser rules.

## Comment Flow

`CommentService` uses `/board/comment/` AJAX JSON as the primary source.

Parsing rules:

- `depth == 0` becomes a root `Comment`
- `depth == 1` becomes a reply with `parent_comment_id`
- IDs and numbers are preserved when present
- author data is normalized into `AuthorInfo`
- `memo` is parsed into text and dccon metadata

The rendered HTML fallback parser supports:

- root comments under `li[id^="comment_li_"]`
- replies under the following `ul.reply_list[p-no]`

## Partial Failure Flow

Fatal failures:

- detail HTML fetch failure
- missing core metadata needed to build valid `PostResult`
- CAPTCHA/block exceptions from UOW-002

Non-fatal failures:

- comment AJAX parse/fetch failure
- repost AJAX parse/fetch failure
- DC video iframe metadata failure
- unsupported content embed

Non-fatal failures are appended to `PostResult.metadata["detail_failures"]` with safe fields only:

- `stage`
- `reason`
- `retryable`
- `field_path`

This is enough for the future metadata-failure retry unit without making UOW-004 own retry storage.

## Testable Properties

- `fetch_post` requires an injected `HttpClient`.
- Leading `(펌)` is removed from stored titles.
- Content block order is deterministic and unique.
- Media parsing does not download files.
- DC video description is `null` when absent.
- Repost metadata excludes original comment count.
- Comment replies preserve parent relationship.
- CAPTCHA/block exceptions propagate.
- Optional subfetch failure returns a `PostResult` with `detail_failures`.
