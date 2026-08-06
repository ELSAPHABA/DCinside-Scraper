# NFR Requirements - UOW-004 Post Detail And Content Parsing

## Scope

This document defines non-functional requirements for `UOW-004 Post Detail And Content Parsing`.

In scope:

- detail HTML fetch
- BeautifulSoup metadata parsing
- ordered content block parsing
- repost AJAX parsing
- DC video iframe metadata resolution
- comment/reply AJAX parsing
- dccon metadata parsing
- safe partial failure metadata

Out of scope:

- JSONL/Garage storage
- media file download
- checkpoint persistence
- queue lifecycle
- CLI prompt UX
- container/MCP hosting

## Confirmed Questionnaire Decisions

| Question | Answer | Decision |
|---|---|---|
| Q1 | A | Fixture tests must cover normal posts, mixed content, repost AJAX, DC video iframe, comment AJAX JSON, rendered comment HTML fallback, and missing optional fields. |
| Q2 | A | Comment pagination uses AJAX pagination or empty pages, with default `max_comment_pages=100`; limit hits return the post and record `comment_page_limit`. |
| Q3 | A | UOW-004 does not add its own retry loop; UOW-002 owns HTTP retry. Optional subfetch failures become `detail_failures` unless CAPTCHA/block is detected. |
| Q4 | A | Partial failure metadata uses only `stage`, `reason`, `retryable`, `field_path`, and `failed_fields`. |
| Q5 | A | Raw post/comment HTML and AJAX bodies are not stored in production `PostResult` or logs. |
| Q6 | A | PBT targets pure normalization and failure-shape functions; BeautifulSoup DOM parsing uses fixture/example tests. |
| Q7 | A | Parser memory is bounded to one post and its active subresponses; parsed results keep structured metadata only. |
| Q8 | A | Live smoke tests are optional and env-gated, never part of default unit tests or mandatory CI. |

No follow-up question is required. The answers are internally consistent.

## Performance Requirements

### NFR-UOW004-PERF-001. Bounded Comment Pagination

Comment collection must stop when:

- AJAX pagination indicates no next page
- the current page has no comments
- `max_comment_pages` is reached

Default `max_comment_pages` is `100`.

When the limit is reached, the post result is still returned and `detail_failures` records `comment_page_limit`.

### NFR-UOW004-PERF-002. Bounded Per-Post Memory

UOW-004 holds only one post detail HTML and active subfetch responses in memory during parsing.

After parsing, `PostResult` keeps structured values only:

- metadata fields
- content blocks
- media metadata
- comments
- links
- safe failure metadata

Raw HTML and AJAX response bodies are not retained.

## Reliability And Resiliency Requirements

### NFR-UOW004-REL-001. Optional Subfetch Isolation

Failures in optional subfetches must not fail the whole post unless they are CAPTCHA/block errors.

Optional subfetches include:

- repost AJAX
- DC video iframe metadata
- comment AJAX

The service records safe failure metadata and returns the best available `PostResult`.

### NFR-UOW004-REL-002. Core Parse Failure Boundary

The post fails with a typed parse error when valid `PostResult` construction is impossible.

Core failures include missing or invalid:

- gallery ID
- post ID
- title
- author

### NFR-UOW004-REL-003. Malformed DOM Handling

Malformed or unsupported body nodes must not fail the whole post.

Unsupported embeds become `UnknownEmbedBlock` or safe `detail_failures`, depending on whether a content block can be represented.

### NFR-UOW004-REL-004. Future Retry Handoff

Failure metadata must be sufficient for the future metadata parsing failure retry unit to identify failed parser fields without rerunning the whole Job.

Required safe fields:

- `stage`
- `reason`
- `retryable`
- `field_path`
- `failed_fields`

## Security Requirements

### NFR-UOW004-SEC-001. Raw Body Exclusion

Production results and logs must not include:

- raw post HTML
- raw comment AJAX body
- raw repost AJAX body
- raw DC video iframe HTML
- cookies
- proxy credentials
- full sensitive query strings

### NFR-UOW004-SEC-002. Safe Failure Metadata

`PostResult.metadata["detail_failures"]` may contain only safe diagnostic fields:

- `stage`
- `reason`
- `retryable`
- `field_path`
- `failed_fields`

Raw HTML snippets, full URLs, cookies, and proxy values are forbidden.

### NFR-UOW004-SEC-003. CAPTCHA And Block Propagation

CAPTCHA/block classifications from UOW-002 must not be swallowed or converted into partial success.

They propagate to UOW-005 so the Job can stop and save checkpoint.

### NFR-UOW004-SEC-004. Import Side-Effect Safety

Importing UOW-004 modules must not:

- make network requests
- read `.env`
- read `user-agents.txt`
- prompt terminal input
- write files
- create queues
- download media files

## Observability Requirements

### NFR-UOW004-OBS-001. Safe Parser Events

UOW-004 may emit safe structured events for:

- detail parse start/end
- metadata parse failure
- content block count
- comment page count
- optional subfetch failure
- repost parse result
- DC video metadata resolution result

Raw HTML, raw AJAX bodies, cookies, proxy values, and full query URLs are excluded.

## Maintainability Requirements

### NFR-UOW004-MAINT-001. Dependency Boundary

Runtime dependency additions allowed for UOW-004:

- BeautifulSoup, already selected for parser work

UOW-004 must not add Playwright, Selenium, Scrapy, database, queue, storage, or media download dependencies.

### NFR-UOW004-MAINT-002. Retry Boundary

HTTP retry, delay, proxy, User-Agent rotation, and CAPTCHA/block classification remain centralized in UOW-002.

UOW-004 does not implement a parallel retry policy.

### NFR-UOW004-MAINT-003. Parser Boundary

UOW-004 owns parsing and result assembly only.

Storage, checkpoint, media download, queue lifecycle, CLI, container, and MCP concerns remain in later units.

## Testing Requirements

### NFR-UOW004-TEST-001. Fixture Tests

UOW-004 must include fixtures for:

- normal post detail HTML
- mixed content detail HTML
- repost AJAX response
- DC video iframe response
- comment AJAX JSON
- rendered comment HTML fallback
- optional field missing cases

### NFR-UOW004-TEST-002. Property-Based Tests

UOW-004 must include Hypothesis tests for pure functions:

- title repost marker normalization
- count normalization
- date normalization
- nickname type classification
- content block order validation
- safe failure record shape

BeautifulSoup DOM parser correctness remains fixture-based.

### NFR-UOW004-TEST-003. Optional Live Smoke

Live smoke tests are not part of default unit tests or mandatory CI.

They may run only when explicitly enabled, for example:

- `DCINSIDE_LIVE_SMOKE_ENABLED=true`

Allowed live smoke scope:

- one post detail page
- one comment page
- no media download
- no CAPTCHA handling automation
- no persisted cookies

## Extension Compliance Summary

### Security Baseline

| Rule | Status | Rationale |
|---|---|---|
| SECURITY-03 | Compliant | Parser events and failure metadata exclude raw HTML, cookies, proxy credentials, and full sensitive URLs. |
| SECURITY-09 | Compliant | Parser failures expose safe reasons and field paths only. |
| SECURITY-10 | Compliant | Dependency pinning remains required at code generation. |
| SECURITY-11 | Compliant | Parser, HTTP runtime, storage, checkpoint, and queue responsibilities remain separated. |
| SECURITY-13 | Compliant | HTML and JSON parsing use structured parsers, not ad hoc shell/string execution. |
| SECURITY-15 | Compliant | CAPTCHA/block propagation supports fail-closed Job behavior. |

Other Security Baseline rules are N/A for this parser unit.

### Resiliency Baseline

| Rule | Status | Rationale |
|---|---|---|
| RESILIENCY-10 | Compliant | Optional subfetch isolation, bounded comment pagination, and CAPTCHA propagation are required. |
| RESILIENCY-14 | Compliant | Fixture/fake HTTP tests verify failure behavior without live network dependency. |
| RESILIENCY-15 | Compliant | Safe parser events and failure metadata support incident triage. |

Other Resiliency Baseline rules are N/A for this non-deployable unit.

### Property-Based Testing

| Rule | Status | Rationale |
|---|---|---|
| PBT-01 | Compliant | Testable parser normalization properties are identified. |
| PBT-03 | Compliant | Count/date/title/nickname/order/failure-shape invariants are required. |
| PBT-04 | Compliant | Normalization idempotence and safe failure shape are required. |
| PBT-07 | Compliant | Domain-specific strategies are required for parser normalization values. |
| PBT-08 | Compliant | Hypothesis shrinking and reproducibility remain enabled. |
| PBT-09 | Compliant | Hypothesis remains selected. |
| PBT-10 | Compliant | Fixture/example tests remain required beside PBT. |

PBT-02, PBT-05, and PBT-06 are N/A for this unit.
