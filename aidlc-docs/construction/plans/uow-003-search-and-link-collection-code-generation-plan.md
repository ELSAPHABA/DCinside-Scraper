# Code Generation Plan - UOW-003 Search And Link Collection

이 문서는 `UOW-003 Search And Link Collection` 코드 생성을 위한 단일 기준 계획입니다. 이번 요청에서 계획 생성과 코드 생성을 함께 완료했습니다.

## Unit Context

- **Unit**: UOW-003 Search And Link Collection
- **Project Type**: Greenfield Python package
- **Workspace Root**: `D:\HongDev\ELSAPHABA\DCinside-Scraper`
- **Code Location**: workspace root의 `src/`, `tests/`, `pyproject.toml`
- **Documentation Location**: `aidlc-docs/construction/uow-003-search-and-link-collection/code/`
- **Primary Stories**: US-004, US-005, US-006B, US-007A, US-007B
- **Supporting Role**: UOW-004 to UOW-008이 사용할 검색/목록 기반 `PostCandidate` 수집 기능 제공

## Dependencies

| Dependency | Status |
|---|---|
| Prior unit dependency | UOW-001 and UOW-002 approved and implemented |
| Functional Design | Approved |
| NFR Requirements | Approved |
| NFR Design | Approved |
| Infrastructure Design | Approved by current user instruction |

## Scope

UOW-003 implements:

- gallery/list URL builder
- integrated search URL builder and keyword encoding
- BeautifulSoup gallery search parser
- BeautifulSoup integrated search parser
- subject head parser and validation
- no-keyword date jump JSON parsing and request helper
- direct post candidate normalization
- gallery search traversal with `page` and `search_pos`
- integrated search traversal with page 120 hard cap
- deep-search gallery discovery and sequential gallery expansion
- one-cycle realtime keyword/all collection
- range filtering
- in-memory candidate dedupe with optional bound
- safe collector event builder
- fixture tests, property-based tests, and optional live smoke test

UOW-003 does not implement:

- post detail parsing
- comment/media/repost AJAX parsing
- JSONL/media/checkpoint storage
- queue insertion or worker pool
- CLI prompt UX
- container entrypoint
- Docker, Terraform, database migrations, Garage, PostgreSQL, or monitoring configuration

## Expected Interfaces And Contracts

| Contract | Target Path |
|---|---|
| Runtime dependency | `pyproject.toml` |
| Public search package exports | `src/dcinside_scraper/search/__init__.py` |
| Search/link collection implementation | `src/dcinside_scraper/search/collection.py` |
| Public async search API wiring | `src/dcinside_scraper/core/api.py` |
| Top-level convenience exports | `src/dcinside_scraper/__init__.py` |
| Search fixture tests | `tests/test_search_collection.py` |
| Search PBT tests | `tests/test_search_properties.py` |
| Search PBT strategies | `tests/strategies/search.py` |
| Static fixtures | `tests/fixtures/search/` |
| Optional live smoke | `tests/test_search_live_smoke.py` |
| Public contract documentation | `aidlc-docs/construction/uow-003-search-and-link-collection/code/public-contracts.md` |
| Code generation summary | `aidlc-docs/construction/uow-003-search-and-link-collection/code/code-generation-summary.md` |

## Database Entities

No database entities or migration scripts are owned by UOW-003.

## Step Sequence

### Step 1. Dependency Update

- [x] Add `beautifulsoup4>=4.12,<5`.
- [x] Reuse UOW-002 `HttpClient`.
- [x] Do not add Playwright, Selenium, Scrapy, requests, database, queue, or storage dependency.

### Step 2. Search Package

- [x] Create `src/dcinside_scraper/search/`.
- [x] Create import-safe public exports.
- [x] Avoid env/file/prompt/network side effects at import.

### Step 3. URL, Parser, And Policy Components

- [x] Implement `GallerySearchUrlBuilder`.
- [x] Implement `IntegratedSearchUrlBuilder`.
- [x] Implement `GallerySearchParser`.
- [x] Implement `IntegratedSearchParser`.
- [x] Implement `SubjectHeadParser`.
- [x] Implement `SearchDateJumpClient`.
- [x] Implement `DateParser`.
- [x] Implement `RangeFilterEvaluator`.
- [x] Implement `CandidateDeduper`.
- [x] Implement `TraversalGuard`.
- [x] Implement `SafeCollectorEventBuilder`.

### Step 4. Collectors

- [x] Implement `DirectPostCollector`.
- [x] Implement `GallerySearchCollector`.
- [x] Implement `IntegratedSearchCollector`.
- [x] Implement `NoKeywordRangeCollector`.
- [x] Implement `DeepSearchCollector`.
- [x] Implement `RealtimeCollectionCycle`.
- [x] Implement `LinkCollectorService`.

### Step 5. Public API Wiring

- [x] Wire `search_gallery(request, http_client)` to `GallerySearchCollector`.
- [x] Wire `search_integrated(request, http_client)` to `IntegratedSearchCollector`.
- [x] Require caller-injected HTTP client.

### Step 6. Testing

- [x] Add static gallery/integrated/search-date fixtures.
- [x] Add example tests for URL builders, parsers, subject head validation, public API wiring, no-keyword date jump, range filtering, realtime dedupe, safe event redaction, and dedupe bounds.
- [x] Add PBT tests for integrated page clamp, dedupe idempotence, range decision stability, and safe collector event redaction.
- [x] Add optional env-gated live smoke test.

### Step 7. Documentation

- [x] Generate public contract documentation.
- [x] Generate code generation summary.
- [x] Record no deployment artifacts for this unit.

## Story Traceability

| Story | Coverage In This Unit |
|---|---|
| US-004 | gallery search URL building, `search_pos`, subject head validation, row parsing |
| US-005 | integrated search URL building, keyword encoding, max page 120, result parsing |
| US-006B | deep-search gallery discovery and sequential gallery expansion |
| US-007A | no-keyword range date jump helper |
| US-007B | one-cycle realtime keyword/all collection and seen-set dedupe |

## Completion Criteria

- [x] UOW-003 source files exist under `src/dcinside_scraper/search/`.
- [x] Tests for UOW-003 behavior exist under `tests/`.
- [x] Documentation summary exists under `aidlc-docs/construction/uow-003-search-and-link-collection/code/`.
- [x] No runtime infrastructure artifact is created for UOW-003.
- [x] `py -3.12 -m pytest -q` passes.
