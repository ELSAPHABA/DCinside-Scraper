# NFR Design Patterns - UOW-004 Post Detail And Content Parsing

## Scope

This document translates UOW-004 NFR requirements into implementation patterns. It covers parser fixture layout, bounded comment pagination, optional subfetch isolation, safe failure metadata, raw HTML exclusion, normalization helpers, safe detail events, property-based testing, and optional live smoke tests.

## Confirmed Design Decisions

| Question | Answer | Design Decision |
|---|---|---|
| Q1 | A | Keep parser fixtures under `tests/fixtures/post_detail/` as small HTML/JSON files. |
| Q2 | A | Use `CommentPaginationGuard` for pagination end, empty page end, and default `max_comment_pages=100`. |
| Q3 | A | Use `DetailFailureRecorder` for optional subfetch/subparse failures; CAPTCHA/block propagate. |
| Q4 | A | Public outputs return `PostResult`; raw body fields are forbidden in failures and events. |
| Q5 | A | Put pure title/count/date/nickname normalization helpers in a small `post_detail.normalization` module. |
| Q6 | A | Use `SafeDetailEventBuilder` for sanitized parser/detail events through `LoggerPort`. |
| Q7 | A | Put reusable Hypothesis strategies in `tests/strategies/post_detail.py`. |
| Q8 | A | Put optional live smoke tests in `tests/test_post_detail_live_smoke.py`, skipped unless explicitly enabled. |

No follow-up question is required.

## Pattern 1. Static Post Detail Fixtures

Parser tests use static files under `tests/fixtures/post_detail/`.

Fixture groups:

- `normal_post.html`
- `mixed_content_post.html`
- `repost_ajax.html`
- `dc_video_iframe.html`
- `comments_page.json`
- `comments_rendered_fallback.html`
- `missing_optional_fields.html`

Fixtures must not contain cookies, raw session identifiers, secrets, proxy data, or private user data.

## Pattern 2. Comment Pagination Guard

`CommentPaginationGuard` owns comment pagination stop checks.

Rules:

- stop when AJAX pagination indicates no next page
- stop when a page returns no comments
- stop at default `max_comment_pages=100`
- return safe reason `comment_page_limit` when the configured limit is reached

The guard does not fetch comments or write checkpoints.

## Pattern 3. Detail Failure Recorder

`DetailFailureRecorder` collects non-fatal detail failures.

Allowed fields:

- `stage`
- `reason`
- `retryable`
- `field_path`
- `failed_fields`

Forbidden fields:

- raw HTML
- raw AJAX body
- cookies
- proxy credentials
- full sensitive query URLs

CAPTCHA/block errors are not recorded here. They propagate as UOW-002 typed errors.

## Pattern 4. Raw Body Exclusion

UOW-004 public service APIs return structured models only:

- `PostResult`
- `list[Comment]`

Raw HTML and AJAX payloads are allowed only in:

- local test fixtures
- temporary in-memory parser inputs

They are not copied into `PostResult.metadata`, logs, failures, or generated JSONL.

## Pattern 5. Normalization Helpers

Pure parser normalization lives in `post_detail.normalization`.

Helper groups:

- title repost marker removal
- integer count parsing
- DCinside date parsing
- nickname type classification
- content block order validation
- safe failure record normalization

These helpers contain no network I/O, BeautifulSoup traversal, file I/O, or logging.

## Pattern 6. Safe Detail Events

All detail parser logs pass through `SafeDetailEventBuilder`.

Rules:

- exclude raw HTML and body text
- exclude cookies and proxy data
- strip or omit full query URLs
- log counts, stage names, safe reason codes, and booleans
- send safe dictionaries through UOW-001 `LoggerPort`

Events:

- detail parse start/end
- metadata parse failure
- content block summary
- comment page summary
- optional subfetch failure
- repost parse result
- DC video metadata result

## Pattern 7. Property-Based Strategy Module

Reusable Hypothesis strategies live in `tests/strategies/post_detail.py`.

Strategy groups:

- repost and normal title strings
- numeric count strings
- DCinside date strings
- nickname metadata inputs
- content block order sequences
- safe failure records

PBT targets pure normalization and failure-shape invariants. BeautifulSoup DOM parser correctness remains fixture-based.

## Pattern 8. Optional Live Smoke Test

Live smoke tests are not part of default CI.

Rules:

- file: `tests/test_post_detail_live_smoke.py`
- marker: `live`
- env guard: `DCINSIDE_LIVE_SMOKE_ENABLED=true`
- fetch at most one post detail page
- fetch at most one comment page
- no media download
- no CAPTCHA handling automation
- no persisted cookies

## Extension Compliance

### Security

| Rule | Status | Design Response |
|---|---|---|
| SECURITY-03 | Compliant | `DetailFailureRecorder` and `SafeDetailEventBuilder` exclude raw bodies, cookies, proxy credentials, and sensitive URLs. |
| SECURITY-09 | Compliant | parser failures expose safe fields only. |
| SECURITY-11 | Compliant | parsing, pagination guard, failure recording, logging, HTTP runtime, and storage remain separated. |
| SECURITY-13 | Compliant | HTML/JSON data is parsed through BeautifulSoup and stdlib JSON boundaries. |
| SECURITY-15 | Compliant | CAPTCHA/block errors propagate instead of being converted to partial success. |

Other Security Baseline rules are N/A for this parser design unit.

### Resiliency

| Rule | Status | Design Response |
|---|---|---|
| RESILIENCY-10 | Compliant | comment page bounds and optional subfetch isolation prevent runaway or brittle parsing. |
| RESILIENCY-14 | Compliant | fixture tests and fake HTTP cover parser failures without live network dependency. |
| RESILIENCY-15 | Compliant | safe events and failure metadata support detail parser triage. |

Other Resiliency Baseline rules are N/A for this unit.

### Property-Based Testing

| Rule | Status | Design Response |
|---|---|---|
| PBT-01 | Compliant | title, count, date, nickname, order, and failure-shape properties are identified. |
| PBT-03 | Compliant | parser normalization invariants are required. |
| PBT-04 | Compliant | normalization helpers must be deterministic for the same input. |
| PBT-07 | Compliant | reusable strategies are placed under `tests/strategies/post_detail.py`. |
| PBT-08 | Compliant | Hypothesis shrinking and reproducibility remain enabled. |
| PBT-09 | Compliant | Hypothesis remains selected. |
| PBT-10 | Compliant | fixture/example tests remain required beside PBT. |

PBT-02, PBT-05, and PBT-06 are N/A for this unit.
