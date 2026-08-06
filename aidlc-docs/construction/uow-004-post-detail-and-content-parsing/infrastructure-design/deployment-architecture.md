# Deployment Architecture - UOW-004 Post Detail And Content Parsing

## Architecture Classification

UOW-004 has no standalone deployed runtime architecture.

It is a post detail and comment parsing package layer consumed by later scraper units and adapters.

```text
Developer or CI
    |
    v
UOW-004 Python post detail parsing package
    |
    +-- PostDetailService
    +-- post metadata parser
    +-- ordered content block parser
    +-- repost AJAX parser/client
    +-- DC video metadata resolver
    +-- comment service/parser
    +-- comment pagination guard
    +-- detail failure recorder
    +-- safe detail event builder
    |
    v
Unit tests, fixture tests, property-based tests

Optional manual path:
DCINSIDE_LIVE_SMOKE_ENABLED=true
    |
    v
single post detail and one comment page smoke

Later units import UOW-004:
UOW-005 JobRunner and checkpoint orchestration
UOW-006 output/media persistence
UOW-007 CLI
UOW-008 container and MCP
```

## Environment Topology

| Environment | UOW-004 Role | Infrastructure |
|---|---|---|
| Local development | run parser, normalization, fixture, and PBT tests | developer Python environment |
| CI | run unit tests and PBT without live network by default | CI runner |
| Runtime scraper | imported by later JobRunner/CLI/container units | no UOW-004-owned runtime resources |
| Optional live smoke | verify one external post/comment request when explicitly enabled | local or CI runner with outbound internet |

## Runtime Boundaries

UOW-004 import must not:

- make network requests
- read `.env`
- read `user-agents.txt`
- read environment variables
- prompt terminal input
- write files
- create queues
- create `httpx.AsyncClient`
- download media files

At explicit runtime call, UOW-004 may:

- receive a UOW-002 `HttpClient`
- fetch detail/comment/repost/video metadata through the injected client
- parse response HTML/JSON
- emit safe detail events
- return `PostResult` or `list[Comment]`

## External Services

| Service Type | Status | Reason |
|---|---|---|
| DCinside HTTP | Runtime dependency through UOW-002 | UOW-004 fetches detail/subresources but does not own HTTP policy |
| Proxy service | Deferred to UOW-002/caller | UOW-004 does not configure proxy |
| Garage object storage | Deferred | output storage belongs to UOW-006 and UOW-008 |
| Media storage | Deferred | media download/storage belongs to UOW-006 |
| PostgreSQL checkpoint store | Deferred | checkpoint persistence belongs to UOW-005 and UOW-008 |
| Queue/scheduler | Deferred | worker orchestration belongs to UOW-005 and UOW-008 |
| Monitoring backend | Deferred | UOW-004 only emits safe events through `LoggerPort`; deployed monitoring is later work |

## Dependency Flow

```text
PostRequest or CommentRequest
    |
    v
PostDetailService / CommentService
    |
    +-- UOW-002 HttpClient
    +-- BeautifulSoup parsers
    +-- normalization helpers
    +-- CommentPaginationGuard
    +-- DetailFailureRecorder
    +-- SafeDetailEventBuilder
    |
    v
PostResult or list[Comment] for later storage/orchestration units
```

UOW-004 does not own storage or checkpoint output. It returns parsed data and safe failure metadata to the caller.

## Test Architecture

Default test path:

```text
pytest / Hypothesis
    |
    +-- static post_detail fixtures
    +-- fake UOW-002 HttpClient responses
    +-- pure normalization/failure-shape strategies
    |
    v
deterministic parser and service tests
```

Live smoke path:

```text
DCINSIDE_LIVE_SMOKE_ENABLED=true
    |
    v
marked live smoke test
    |
    v
single post detail and one comment page request
```

Live smoke is not a default CI gate.

## Security Boundary

The deployment boundary for UOW-004 is the caller process.

Required security behavior:

- no raw HTML/body logging
- no raw AJAX body logging
- no full query URL logging
- no raw cookie logging
- no proxy credential access
- no CAPTCHA bypass automation
- no media file download in this unit
- typed CAPTCHA/block errors from UOW-002 propagate to the caller

## Infrastructure Handoff

UOW-004 hands off post detail parsing capability to later units:

- `PostDetailService`
- `CommentService`
- post/comment/content/media parser outputs
- `PostResult`
- safe `detail_failures`
- safe detail events
- optional live smoke path

Later units decide:

- worker process topology
- post-level concurrency
- checkpoint persistence
- JSONL/media output storage
- Garage bucket layout
- container env injection
- CLI terminal prompts
- MCP server hosting
- monitoring backend
- metadata-failure retry orchestration
