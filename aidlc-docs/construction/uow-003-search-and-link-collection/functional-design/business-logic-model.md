# Business Logic Model - UOW-003 Search And Link Collection

## Purpose

UOW-003 turns configured DCinside entrypoints into deduplicated `PostCandidate` values.

This unit owns search/list traversal and candidate extraction. It does not own post detail parsing, storage, checkpoint writes, or queue lifecycle.

## Confirmed Decisions

| Area | Decision |
|---|---|
| Collector output | async iterator/list of `PostCandidate`; Queue insertion belongs to UOW-005 |
| Gallery search traversal | collect page 1 to page end within a `search_pos` segment, then follow `a.search_next[href]` as-is |
| `search_pos` initial value | omitted or blank; never calculated from latest post number |
| Gallery parser scope | rows, subject head, repost marker, dates/counts, `search_next`, `page_end` |
| Integrated search | URL builder with `%` to `.` keyword encoding, parser, max 120 pages |
| Range filter | applied during link collection; storage/idempotency units still dedupe later |
| No-keyword range | initial `%20` URL plus `/ajax/search_ajax/search_date/` when `date_to` exists |
| Deep search | integrated search gallery discovery, then sequential per-gallery keyword search |
| Realtime | UOW-003 provides one latest collection cycle; loop/timer/checkpoint belongs to UOW-005 |

## Collector Flow

1. Caller provides a UOW-001 source config and UOW-002 `HttpClient`.
2. `LinkCollectorService` dispatches to the matching collector.
3. Collector builds URLs or AJAX request data.
4. Collector fetches HTML/API payloads through `HttpClient`.
5. BeautifulSoup parsers extract `PostCandidate` values and traversal metadata.
6. `RangeFilterEvaluator` decides whether each candidate is included, skipped, or should end the current traversal.
7. `CandidateDeduper` removes duplicates by `(gallery_id, post_number)`.
8. Collector returns candidates and a `CollectorSummary`.

## Supported Modes

| Mode | Source Model | Collector |
|---|---|---|
| direct URL | `DirectPostSource` | `DirectPostCollector` |
| gallery search | `GallerySearchSource` | `GallerySearchCollector` |
| integrated search | `IntegratedSearchSource` | `IntegratedSearchCollector` |
| deep search | `DeepSearchSource` | `DeepSearchCollector` |
| no-keyword range | `NoKeywordRangeSource` | `NoKeywordRangeCollector` |
| realtime keyword | `RealtimeKeywordSource` | `RealtimeCollectionCycle` |
| realtime all | `RealtimeAllSource` | `RealtimeCollectionCycle` |

## Gallery Search Flow

URL builder:

- major gallery: `https://gall.dcinside.com/board/lists/`
- minor gallery: `https://gall.dcinside.com/mgallery/board/lists/`
- query: `id`, `s_type`, `s_keyword`, `page`, optional `search_pos`, optional `search_head`

Traversal:

1. Start with `page=1` and omitted/blank `search_pos`.
2. Fetch current page.
3. Parse rows and page metadata.
4. Continue `page += 1` until current segment page end.
5. If `a.search_next[href]` exists, use that URL as the next segment start.
6. Stop when `search_next` is absent, no valid rows exist, or range termination is reached.

`search_pos` is copied from DCinside links. It is not calculated by post number.

## Gallery Parser Flow

`GallerySearchParser` extracts:

- rows from `.gall_listwrap.list tbody tr.ub-content.us-post`
- post number from `.gall_num`
- subject head from `.gall_subject`
- title and detail URL from `.gall_tit a`
- list-level repost marker from `.gall_tit > b.font_blue009`
- writer cell metadata from `.gall_writer`
- created date from `.gall_date[title]` or text
- views from `.gall_count`
- recommendations from `.gall_recommend`
- page end from `a.page_end[href]` or paging links
- next segment URL from `a.search_next[href]`
- subject head tabs from `a[onclick^="listSearchHead"]`

Rows without `us-post` or with `.gall_num` equal to `-` are ignored.

## Subject Head Flow

Subject head support applies only to minor galleries.

Validation:

1. Parse visible tabs with `a[onclick^="listSearchHead"]`.
2. Extract `listSearchHead(<ID>)`.
3. Match requested `search_head` against parsed IDs.
4. Treat missing active tab or dropped `search_head` in the response as invalid.

Fallback probing by increments of 10 is only used when the DOM tab list is absent.

`sort_type` is not used as a subject head filter.

## Integrated Search Flow

Keyword encoding:

1. UTF-8 percent-encode the keyword.
2. Replace `%` with `.`.
3. Preserve spaces as `.20`.

URL forms:

- latest first page: `/post/q/<keyword>`
- latest later pages: `/post/p/<page>/q/<keyword>`
- accuracy first page: `/post/sort/accuracy/q/<keyword>`
- accuracy later pages: `/post/p/<page>/sort/accuracy/q/<keyword>`

Traversal:

1. Start at configured `page_start`.
2. Parse current page.
3. Determine page end from `a.page_end[href]` or largest paging link.
4. Stop at configured `page_end`, parsed page end, or page 120, whichever comes first.

## Integrated Parser Flow

`IntegratedSearchParser` extracts:

- result items from `.integrate_cont.sch_result.result_all ul.sch_result_list > li`
- title and detail URL from `a.tit_txt`
- preview text from `p.link_dsc_txt` excluding `.dsc_sub`
- gallery name and URL from `p.dsc_sub > a.sub_txt`
- created date from `p.dsc_sub > span.date_time`
- `gallery_id` and `post_number` from detail URL query
- gallery type from detail URL path

Each result may also produce a `GalleryCandidate` for deep search.

## No-Keyword Range Flow

Initial URL:

- `s_type=search_subject_memo`
- `s_keyword=%20`

If `date_to` exists:

1. Fetch the initial list page with the same `HttpClient` lifecycle.
2. Use the in-memory cookie state from UOW-002.
3. POST to `/ajax/search_ajax/search_date/`.
4. Send `keyword=` as an empty string.
5. Use successful response `data` as `search_pos`.
6. Reuse gallery search traversal.

If date jump fails, the collector treats it as no result for that date and returns an empty candidate set plus a safe failure reason.

## Deep Search Flow

1. Run integrated search for the keyword, up to 120 pages.
2. Add integrated-search post candidates to the final dedupe set.
3. Extract gallery candidates from integrated results.
4. Dedupe galleries by `(gallery_type, gallery_id)`.
5. For each candidate gallery, run gallery search with the same keyword and configured `s_type`.
6. Apply range filter and candidate dedupe.
7. Record per-gallery failures without failing the whole Job.

Deep search requires at least one date or post-number range. UOW-001 validates this; UOW-003 assumes validated input.

## Realtime Cycle Flow

UOW-003 implements one reusable collection cycle.

Realtime keyword:

- if `gallery_id` is present, run one latest gallery keyword search cycle
- otherwise run one latest integrated search cycle

Realtime all:

- run one latest gallery list cycle without keyword search parameters

The cycle applies the provided dedupe set and returns only new candidates.

UOW-005 owns:

- repeated loop
- timer/end-at termination
- checkpoint save
- queue insertion

## Testable Properties

- Gallery search URL parsing and formatting preserves `id`, `page`, `s_type`, `s_keyword`, `search_pos`, and `search_head`.
- Integrated search keyword encoding is deterministic.
- Integrated search page traversal never exceeds page 120.
- Candidate dedupe is idempotent.
- Range filter inclusion is monotonic for descending post numbers.
- Realtime cycle returns no candidate already present in the dedupe set.
- Deep search gallery dedupe uses `(gallery_type, gallery_id)`.
