# Domain Entities - UOW-003 Search And Link Collection

## Entity Overview

UOW-003 defines search/link collection entities. Names describe contracts for implementation, not necessarily final file names.

## Collector Components

### LinkCollectorService

Responsibilities:

- dispatch by `JobConfig.source.type`
- create mode-specific collectors
- return candidates and summary
- keep queue ownership out of UOW-003

Collaborators:

- `HttpClient`
- `DirectPostCollector`
- `GallerySearchCollector`
- `IntegratedSearchCollector`
- `DeepSearchCollector`
- `NoKeywordRangeCollector`
- `RealtimeCollectionCycle`

### DirectPostCollector

Responsibilities:

- normalize direct post URLs into `PostCandidate`
- parse gallery ID, post number, and gallery type from URL
- dedupe direct URLs

### GallerySearchCollector

Responsibilities:

- build gallery search/list URLs
- traverse pages and `search_pos` segments
- call `GallerySearchParser`
- apply range filter and dedupe
- return `GallerySearchPage` and candidates

### IntegratedSearchCollector

Responsibilities:

- build integrated search URLs
- enforce max page 120
- call `IntegratedSearchParser`
- apply range filter and dedupe
- produce gallery candidates for deep search

### NoKeywordRangeCollector

Responsibilities:

- build no-keyword initial search URL
- call `SearchDateJumpClient` when `date_to` exists
- reuse `GallerySearchCollector` traversal
- apply date and post number termination

### DeepSearchCollector

Responsibilities:

- run integrated search discovery
- dedupe `GalleryCandidate` values
- include integrated result post candidates in final dedupe set
- run sequential gallery keyword searches per candidate gallery
- record partial gallery failures

### RealtimeCollectionCycle

Responsibilities:

- run one latest collection cycle
- support keyword and all modes
- apply provided dedupe set
- return only new candidates

It does not own timers, loops, checkpoints, or queues.

## Parser Components

### GallerySearchParser

Input:

- HTML text
- base URL
- current request URL

Output:

- `GallerySearchPage`

Extracts:

- post rows
- candidates
- subject heads
- page end
- next search URL
- current search position

### IntegratedSearchParser

Input:

- HTML text
- base URL
- current page
- sort mode

Output:

- `IntegratedSearchPage`
- gallery candidates
- page end

### SubjectHeadParser

Responsibilities:

- parse `a[onclick^="listSearchHead"]`
- extract subject head ID and name
- detect active tab
- validate requested subject head

## URL And Request Components

### GallerySearchUrlBuilder

Responsibilities:

- choose major/minor list path
- add `id`, `s_type`, `s_keyword`, `page`
- preserve optional `search_pos`
- preserve optional `search_head`
- normalize relative `search_next` href into absolute URL

### IntegratedSearchUrlBuilder

Responsibilities:

- encode keyword by UTF-8 percent encoding then `%` to `.`
- build latest and accuracy URL forms
- clamp page requests to 120

### SearchDateJumpClient

Responsibilities:

- POST `/ajax/search_ajax/search_date/`
- send `keyword=` for no-keyword range mode
- return `search_pos` when response has `result=success` and nonblank `data`
- return safe no-result/failure state otherwise

Inputs:

- gallery ID
- gallery type
- date
- keyword
- search type
- `ci_t`

## Policy Components

### RangeFilterEvaluator

Responsibilities:

- decide candidate inclusion
- decide skip-and-continue
- decide current traversal termination

Inputs:

- `RangeFilter`
- candidate post number
- candidate created date
- current sort direction

### CandidateDeduper

Responsibilities:

- track seen candidate keys
- return only first occurrence
- expose seen set for realtime cycles

Primary key:

- `(gallery_id, post_number)`

Fallback key:

- normalized detail URL

### GalleryCandidateDeduper

Responsibilities:

- dedupe deep search galleries

Key:

- `(gallery_type, gallery_id)`

## Data Entities

### SearchTraversalState

Fields:

- `mode`
- `gallery_id`
- `gallery_type`
- `page`
- `search_pos`
- `search_next_url`
- `page_end`

Purpose:

- supports collector traversal and later checkpoint handoff

### SubjectHead

Fields:

- `id`
- `name`
- `active`

Purpose:

- validates minor gallery subject head filters
- enriches `PostCandidate.metadata`

### GalleryCandidate

Fields:

- `gallery_id`
- `gallery_type`
- `gallery_name`
- `gallery_url`

Purpose:

- deep search per-gallery expansion

### CollectorSummary

Fields:

- `mode`
- `visited_pages`
- `visited_search_segments`
- `candidate_count`
- `deduped_count`
- `skipped_count`
- `range_stop_reason`
- `gallery_candidate_count`
- `failures`
- `final_state`

Purpose:

- gives UOW-005 enough information for logs and checkpoint state

### CollectorFailure

Fields:

- `stage`
- `gallery_id`
- `gallery_type`
- `url`
- `reason`
- `retryable`

Purpose:

- records partial failures, especially in deep search

## Relationships To Other Units

| Unit | Relationship |
|---|---|
| UOW-001 | consumes source models, `RangeFilter`, `PostCandidate`, typed errors |
| UOW-002 | uses `HttpClient` for all network I/O |
| UOW-004 | receives `PostCandidate` for detail parsing later |
| UOW-005 | owns queue insertion, repeated realtime loop, checkpoint, and cancellation |
| UOW-006 | owns final output dedupe/idempotent storage |
| UOW-007 | builds source config from CLI options |
| UOW-008 | provides container/MCP adapter wiring later |
