# NFR Design Patterns - UOW-003 Search And Link Collection

## Scope

This document translates UOW-003 NFR requirements into implementation patterns. It covers traversal guardrails, parser fixtures, row-level parse failures, bounded dedupe, date precision, safe collector logging, property-based testing, and optional live smoke tests.

## Confirmed Design Decisions

| Question | Answer | Design Decision |
|---|---|---|
| Q1 | A | Use one `TraversalGuard` for integrated search page 120, optional `max_pages`, optional `max_segments`, and optional `max_seen_candidates`. |
| Q2 | A | Keep parser fixtures under `tests/fixtures/search/` and feed static files into BeautifulSoup/parser tests. |
| Q3 | A | Parser returns `(candidates, failures)`; failures store row index, stage, safe reason, and `retryable=false` only. |
| Q4 | A | `CandidateDeduper` owns an in-memory seen set and optional `max_seen_candidates`; no persistent dedupe store in UOW-003. |
| Q5 | A | `DateParser` strongly filters only absolute dates/datetimes; ambiguous dates are included with `date_precision="ambiguous"`. |
| Q6 | A | `SafeCollectorEventBuilder` removes URL query, excludes raw HTML/body and `ci_t`, and logs counts/state only. |
| Q7 | A | Put reusable Hypothesis strategies in `tests/strategies/search.py`. |
| Q8 | A | Put optional live smoke tests in `tests/test_search_live_smoke.py`, skipped unless explicitly enabled. |

No follow-up question is required.

## Pattern 1. Traversal Guard

`TraversalGuard` owns link traversal stop checks.

Rules:

- integrated search never traverses past page 120
- optional `max_pages` caps gallery/integrated traversal
- optional `max_segments` caps search-position segments
- optional `max_seen_candidates` caps in-memory dedupe growth
- returns a safe continue/stop/error decision with a reason code

The guard does not fetch pages, parse HTML, or save checkpoints.

## Pattern 2. Static Parser Fixtures

Parser tests use static files under `tests/fixtures/search/`.

Fixture groups:

- `gallery_search.html`
- `gallery_subject_heads.html`
- `integrated_search.html`
- `search_date_success.json`
- `deep_search_gallery_candidates.html`

Fixtures must not contain cookies, raw session identifiers, secrets, or private user data.

## Pattern 3. Row Failure Collection

List parsers return both successful candidates and safe failures.

Failure fields:

- `row_index`
- `stage`
- `reason`
- `retryable=false`

Raw row HTML is excluded. Page-level unknown structure may still raise a typed parser error.

## Pattern 4. Bounded Candidate Deduper

`CandidateDeduper` owns one in-memory seen set per collection job.

Primary key:

- `(gallery_id, post_number)`

Fallback key:

- normalized post URL

If `max_seen_candidates` is set and exceeded, the collector raises a typed runtime/configuration error instead of continuing unbounded.

## Pattern 5. Date Precision

`DateParser` returns parsed value and precision.

Precision values:

- `absolute`
- `date_only`
- `ambiguous`
- `unknown`

Only `absolute` and `date_only` values are used for strong range termination. `ambiguous` candidates stay included with metadata so detail scraping can validate them later.

## Pattern 6. Safe Collector Events

All collector logs pass through `SafeCollectorEventBuilder`.

Rules:

- remove URL query strings
- exclude raw HTML and raw body text
- exclude `ci_t`
- log counts, page numbers, segment states, and safe reason codes
- send safe dictionaries through UOW-001 `LoggerPort`

Events:

- collector start/end
- page fetched
- segment advanced
- candidate summary
- range termination
- row parse failure
- deep-search gallery failure

## Pattern 7. Property-Based Strategy Module

Reusable Hypothesis strategies live in `tests/strategies/search.py`.

Strategy groups:

- URL parts
- encoded keywords
- post candidates
- number/date ranges
- gallery candidates
- realtime seen sets

Properties focus on URL/query invariants, dedupe idempotence, traversal bounds, date precision, and log sanitization.

## Pattern 8. Optional Live Smoke Test

Live smoke tests are not part of default CI.

Rules:

- file: `tests/test_search_live_smoke.py`
- marker: `live`
- env guard: `DCINSIDE_LIVE_SMOKE_ENABLED=true`
- execute at most one gallery or integrated search page request
- assert only basic fetch/parse shape

## Extension Compliance

### Security

| Rule | Status | Design Response |
|---|---|---|
| SECURITY-03 | Compliant | `SafeCollectorEventBuilder` excludes raw HTML/body, URL query, `ci_t`, cookies, and secrets. |
| SECURITY-05 | Compliant | traversal limits and candidate bounds are validated before/during collection. |
| SECURITY-09 | Compliant | row failures expose safe reason codes instead of raw page snippets. |
| SECURITY-11 | Compliant | traversal, parsing, dedupe, date parsing, and logging remain separated. |
| SECURITY-15 | Compliant | unknown or blocked page structures fail closed through typed errors where row-level recovery is unsafe. |

Other Security Baseline rules are N/A for this collector design unit.

### Resiliency

| Rule | Status | Design Response |
|---|---|---|
| RESILIENCY-10 | Compliant | page, segment, and seen-candidate bounds prevent runaway collection. |
| RESILIENCY-14 | Compliant | fixture tests and PBT cover parse and traversal edge cases without live network dependency. |
| RESILIENCY-15 | Compliant | safe structured events support collection failure triage. |

Other Resiliency Baseline rules are N/A for this unit.

### Property-Based Testing

| Rule | Status | Design Response |
|---|---|---|
| PBT-01 | Compliant | traversal, URL, dedupe, range, and sanitization properties are identified. |
| PBT-03 | Compliant | query construction, bound checks, date precision, and dedupe invariants are required. |
| PBT-04 | Compliant | parser and dedupe operations must be deterministic for the same input. |
| PBT-07 | Compliant | reusable strategies are placed under `tests/strategies/search.py`. |
| PBT-08 | Compliant | Hypothesis shrinking and reproducibility remain enabled. |
| PBT-09 | Compliant | Hypothesis remains selected. |
| PBT-10 | Compliant | example fixture tests remain required beside PBT. |

PBT-02, PBT-05, and PBT-06 are N/A for this unit.
