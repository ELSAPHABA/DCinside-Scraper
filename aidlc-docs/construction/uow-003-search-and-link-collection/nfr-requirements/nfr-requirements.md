# NFR Requirements - UOW-003 Search And Link Collection

## Scope

This document defines non-functional requirements for `UOW-003 Search And Link Collection`.

In scope:

- gallery/list URL generation
- integrated search URL generation
- BeautifulSoup parser correctness for search/list pages
- traversal bounds
- candidate dedupe
- range filtering
- no-keyword date jump response handling
- deep search gallery discovery
- realtime one-cycle collection
- safe structured collector logging

Out of scope:

- post detail parsing
- result storage
- checkpoint persistence
- queue lifecycle
- CLI prompt UX
- container/MCP hosting

## Confirmed Questionnaire Decisions

| Question | Answer | Decision |
|---|---|---|
| Q1 | A | Integrated search has hard max page 120; gallery search uses range/`search_next` termination plus optional `max_pages`/`max_segments` guardrails. |
| Q2 | A | Code generation must include fixtures for gallery search, subject head, integrated search, no-keyword `search_date` JSON, and deep-search gallery candidates. |
| Q3 | A | Individual row parse failures become safe `CollectorFailure` records; page-level unknown structure and CAPTCHA/block propagate. |
| Q4 | A | Candidate dedupe uses in-memory set with optional `max_seen_candidates`; persistent dedupe is deferred to UOW-006. |
| Q5 | A | Post-number ranges apply strongly; date ranges apply strongly only when list dates are absolute and parseable. Ambiguous dates are included with metadata. |
| Q6 | A | Safe structured events cover collector lifecycle, page/segment progress, counts, range termination, and deep-search per-gallery failures. |
| Q7 | A | PBT targets pure URL/policy logic; BeautifulSoup DOM parsing uses fixture/example tests. |
| Q8 | A | Live smoke tests are excluded from default tests and mandatory CI unless explicitly enabled. |

No follow-up question is required. The answers are internally consistent.

## Performance Requirements

### NFR-UOW003-PERF-001. Bounded Traversal

Integrated search must never request page greater than 120.

Gallery search terminates on:

- absent `search_next`
- empty valid result rows
- range termination
- optional `max_pages`
- optional `max_segments`

### NFR-UOW003-PERF-002. Bounded Dedupe Memory

Candidate dedupe may use an in-memory set.

If `max_seen_candidates` is configured and exceeded, the collector must stop with a safe bounded-resource error rather than growing unbounded memory.

Persistent or large-scale dedupe is deferred to UOW-006 output/idempotency work.

## Reliability And Resiliency Requirements

### NFR-UOW003-REL-001. Parser Failure Isolation

Individual row parser failures must not fail the whole page.

Required behavior:

- record a safe `CollectorFailure`
- skip the failed row
- continue parsing remaining rows

Exceptions:

- CAPTCHA/block/unavailable errors from UOW-002 propagate
- page-level unrecognized search result structure may fail the page

### NFR-UOW003-REL-002. Partial Deep Search Failure

Failure in one candidate gallery must not fail the whole deep search.

The collector records:

- gallery ID
- gallery type
- safe reason
- retryable flag when available

### NFR-UOW003-REL-003. Deterministic Traversal State

Collector summaries must expose enough state for UOW-005 checkpoint handoff:

- mode
- page
- `search_pos`
- next segment URL
- visited page count
- visited segment count
- accepted/deduped/skipped counts
- range stop reason

UOW-003 does not persist checkpoints.

## Security Requirements

### NFR-UOW003-SEC-001. Safe Logging

Logs must not include:

- raw HTML
- raw response body
- raw cookie
- proxy credential
- full URL query
- raw search AJAX form with `ci_t`

Allowed values:

- redacted URL/path
- gallery ID
- gallery type
- page number
- safe `search_pos` label/count when needed
- accepted/skipped/deduped counts
- safe reason

### NFR-UOW003-SEC-002. CAPTCHA And Block Propagation

CAPTCHA/block classifications from UOW-002 must not be swallowed or converted into successful empty results.

They propagate to UOW-005 so the Job can stop and save checkpoint.

### NFR-UOW003-SEC-003. Import Side-Effect Safety

Importing UOW-003 modules must not:

- make network requests
- read `.env`
- read `user-agents.txt`
- prompt terminal input
- write files
- create queues

## Observability Requirements

### NFR-UOW003-OBS-001. Safe Collector Events

UOW-003 must emit safe structured events for:

- collector start
- collector end
- page fetched
- segment advanced
- candidate count summary
- range termination
- row parse failure
- deep-search per-gallery failure

Raw HTML and full query URLs are excluded from event payloads.

## Maintainability Requirements

### NFR-UOW003-MAINT-001. Dependency Boundary

Runtime dependency additions allowed for UOW-003:

- BeautifulSoup parser dependency if not already present

No Playwright, Selenium, Scrapy, database, queue, or storage dependency is added in UOW-003.

### NFR-UOW003-MAINT-002. Parser Boundary

Search/list parsers may extract candidate metadata needed for filtering and dedupe.

Detailed post body, comments, media, repost AJAX card parsing, and output schema finalization remain in later units.

## Testing Requirements

### NFR-UOW003-TEST-001. Example And Fixture Tests

UOW-003 must include fixtures for:

- gallery search rows and pagination
- minor gallery subject head tabs
- integrated search result list and page end
- no-keyword `search_date` success JSON
- deep-search gallery candidate extraction

### NFR-UOW003-TEST-002. Property-Based Tests

UOW-003 must include Hypothesis tests for:

- gallery URL round trip
- integrated keyword encoding determinism
- integrated max page clamp
- candidate dedupe idempotence
- range filter monotonicity
- realtime dedupe exclusion
- deep-search gallery dedupe

PBT must target pure policy/URL logic. BeautifulSoup DOM parser correctness remains fixture-based.

### NFR-UOW003-TEST-003. Optional Live Smoke

Live smoke tests are not part of default unit tests or mandatory CI.

They may run only when explicitly enabled, for example:

- `DCINSIDE_LIVE_SMOKE_ENABLED=true`

Allowed live smoke scope:

- one gallery search page
- or one integrated search page
- no CAPTCHA handling automation
- no persisted cookies

## Extension Compliance Summary

### Security Baseline

| Rule | Status | Rationale |
|---|---|---|
| SECURITY-03 | Compliant | Safe collector events exclude raw HTML, cookies, proxy credentials, and full query URLs. |
| SECURITY-05 | Compliant | Source config validation comes from UOW-001; traversal guardrails validate bounds. |
| SECURITY-09 | Compliant | Parser failures expose safe reasons only. |
| SECURITY-10 | Compliant | dependency pinning remains required at code generation. |
| SECURITY-11 | Compliant | collector, parser, HTTP runtime, storage, and checkpoint responsibilities remain separated. |
| SECURITY-13 | Compliant | URL/query parsing uses structured parsing and safe JSON handling. |
| SECURITY-15 | Compliant | CAPTCHA/block propagation supports fail-closed Job behavior. |

Other Security Baseline rules are N/A for this library/search unit.

### Resiliency Baseline

| Rule | Status | Rationale |
|---|---|---|
| RESILIENCY-10 | Compliant | bounded traversal, parser failure isolation, and CAPTCHA propagation are required. |
| RESILIENCY-14 | Compliant | fixture/fake HTTP tests verify failure behavior without live network dependency. |
| RESILIENCY-15 | Compliant | collector summaries and safe events support incident triage. |

Other Resiliency Baseline rules are N/A for this non-deployable unit.

### Property-Based Testing

| Rule | Status | Rationale |
|---|---|---|
| PBT-01 | Compliant | testable search/link properties are identified. |
| PBT-03 | Compliant | URL, bounds, dedupe, range, and realtime invariants are required. |
| PBT-04 | Compliant | dedupe idempotence and deterministic encoding are required. |
| PBT-07 | Compliant | domain-specific strategies are required for URLs, candidates, ranges, and galleries. |
| PBT-08 | Compliant | Hypothesis shrinking and reproducibility remain enabled. |
| PBT-09 | Compliant | Hypothesis remains selected. |
| PBT-10 | Compliant | fixture/example tests remain required beside PBT. |

PBT-02, PBT-05, and PBT-06 are N/A for this unit.
