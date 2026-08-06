# Deployment Architecture - UOW-003 Search And Link Collection

## Architecture Classification

UOW-003 has no standalone deployed runtime architecture.

It is a search/link collection package layer consumed by later scraper units and adapters.

```text
Developer or CI
    |
    v
UOW-003 Python search/link collection package
    |
    +-- URL builders
    +-- gallery search collector
    +-- integrated search collector
    +-- no-keyword range collector
    +-- deep-search collector
    +-- realtime one-cycle collector
    +-- BeautifulSoup parsers
    +-- traversal guard
    +-- candidate deduper
    +-- safe collector event builder
    |
    v
Unit tests, fixture tests, property-based tests

Optional manual path:
DCINSIDE_LIVE_SMOKE_ENABLED=true
    |
    v
single gallery or integrated search smoke

Later units import UOW-003:
UOW-004 post/comment/media scraping
UOW-005 JobRunner and checkpoint orchestration
UOW-006 output persistence
UOW-007 CLI
UOW-008 container and MCP
```

## Environment Topology

| Environment | UOW-003 Role | Infrastructure |
|---|---|---|
| Local development | run parser, URL, traversal, dedupe, range, and PBT tests | developer Python environment |
| CI | run unit tests and PBT without live network by default | CI runner |
| Runtime scraper | imported by later JobRunner/CLI/container units | no UOW-003-owned runtime resources |
| Optional live smoke | verify one external search/list request when explicitly enabled | local or CI runner with outbound internet |

## Runtime Boundaries

UOW-003 import must not:

- make network requests
- read `.env`
- read `user-agents.txt`
- read environment variables
- prompt terminal input
- write files
- create queues
- create `httpx.AsyncClient`

At explicit runtime call, UOW-003 may:

- receive a UOW-002 `HttpClient`
- build search/list URLs
- issue requests through the injected client
- parse response HTML/JSON
- emit safe collector events
- return post candidates and collector summaries

## External Services

| Service Type | Status | Reason |
|---|---|---|
| DCinside HTTP | Runtime dependency through UOW-002 | UOW-003 builds URLs and parses responses but does not own HTTP policy |
| Proxy service | Deferred to UOW-002/caller | UOW-003 does not configure proxy |
| Garage object storage | Deferred | output storage belongs to UOW-006 and UOW-008 |
| PostgreSQL checkpoint store | Deferred | checkpoint persistence belongs to UOW-005 and UOW-008 |
| Queue/scheduler | Deferred | worker orchestration belongs to UOW-005 and UOW-008 |
| Monitoring backend | Deferred | UOW-003 only emits safe events through `LoggerPort`; deployed monitoring is later work |

## Dependency Flow

```text
Validated source config
    |
    v
LinkCollectorService
    |
    +-- selected collector
    |       |
    |       +-- URL builder
    |       +-- UOW-002 HttpClient
    |       +-- BeautifulSoup parser
    |       +-- TraversalGuard
    |       +-- CandidateDeduper
    |
    v
PostCandidate values for later units
```

UOW-003 does not own storage or checkpoint output. It returns candidates and summary state to the caller.

## Test Architecture

Default test path:

```text
pytest / Hypothesis
    |
    +-- static search fixtures
    +-- fake UOW-002 HttpClient responses
    +-- pure URL/range/dedupe strategies
    |
    v
deterministic collector and parser tests
```

Live smoke path:

```text
DCINSIDE_LIVE_SMOKE_ENABLED=true
    |
    v
marked live smoke test
    |
    v
single gallery or integrated search request
```

Live smoke is not a default CI gate.

## Security Boundary

The deployment boundary for UOW-003 is the caller process.

Required security behavior:

- no raw HTML/body logging
- no full query URL logging
- no `ci_t` logging
- no raw cookie logging
- no proxy credential access
- no CAPTCHA bypass automation
- typed CAPTCHA/block errors from UOW-002 propagate to the caller

## Infrastructure Handoff

UOW-003 hands off search/link collection capability to later units:

- `LinkCollectorService`
- gallery/integrated/no-keyword/deep/realtime collectors
- search/list parsers
- traversal guard
- candidate deduper
- collector summaries
- safe collector events

Later units decide:

- worker process topology
- concurrency model
- checkpoint persistence
- JSONL/media output storage
- Garage bucket layout
- container env injection
- CLI terminal prompts
- MCP server hosting
- monitoring backend
