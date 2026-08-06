# Infrastructure Design - UOW-003 Search And Link Collection

## Scope

UOW-003 is not a deployable scraper worker. It defines an importable Python search/link collection layer used by later units.

In scope:

- gallery/list URL construction
- integrated search URL construction
- BeautifulSoup search/list parsers
- `search_pos` traversal
- no-keyword date jump request handling through the injected HTTP client
- deep-search gallery discovery
- candidate dedupe and range filtering
- fixture/PBT tests
- optional live smoke test boundary
- safe structured collector events

Out of scope:

- post detail scraping
- comment/media parsing
- queue lifecycle
- checkpoint persistence
- JSONL, Garage, PostgreSQL, or object storage adapters
- CLI prompt UX
- container entrypoint
- MCP hosting

## Confirmed Decisions

| Area | Decision |
|---|---|
| Deployment environment | N/A for standalone UOW-003 service/container deployment |
| Compute and parallelism | local development and CI test runner only; no worker pool or persistent compute |
| HTTP/network boundary | UOW-003 receives UOW-002 `HttpClient`; it does not configure proxy, User-Agent, limiter, or cookies |
| Runtime configuration | UOW-003 consumes validated in-memory config only; no env/file/prompt reads |
| Fixture/test data | static sanitized HTML/JSON fixtures under `tests/fixtures/search/` |
| Live smoke | excluded by default; env-gated single gallery or integrated search smoke only |
| Monitoring | no external monitoring stack; safe events through UOW-001 `LoggerPort` only |
| Shared infrastructure | no Garage, PostgreSQL, queue, checkpoint, or shared infrastructure artifact for UOW-003 |

## Deployment Environment

UOW-003 is an importable library layer, not a standalone runtime.

Required environment:

- Python package build/import environment
- local unit/PBT execution environment
- CI unit/PBT execution environment
- optional live smoke execution environment when explicitly enabled

Not required:

- Docker image owned by UOW-003
- scheduler
- queue consumer
- hosted service
- MCP server process
- cloud account resources

## Compute Infrastructure

No persistent compute infrastructure is provisioned for UOW-003.

Execution targets:

- local developer machine for parser, URL, traversal, range, and dedupe tests
- CI runner for unit tests and property-based tests
- optional manual smoke run against DCinside when enabled by environment variable

Deep search uses sequential per-gallery traversal in this unit. Parallel collection, queue insertion, worker count, checkpoint save, and realtime loop execution are deferred to later JobRunner/worker units.

## HTTP And Network Boundary

UOW-003 uses a caller-provided UOW-002 `HttpClient`.

UOW-003 may:

- build request URLs
- pass request method, URL, form data, and referer hints to the injected client
- reuse the same client lifecycle for no-keyword `search_date` AJAX after the initial list fetch
- consume UOW-002 response classification and typed errors

UOW-003 must not:

- create its own `httpx.AsyncClient`
- configure proxy settings
- rotate User-Agent values
- configure request rate limits
- read or persist cookies
- bypass CAPTCHA

## Runtime Configuration Boundary

UOW-003 consumes already-validated source config from UOW-001 and runtime objects from its caller.

UOW-003 import must not:

- make network requests
- read `.env`
- read `user-agents.txt`
- read environment variables
- prompt terminal input
- write files
- create queues

Realtime loop termination env parsing belongs to the JobRunner/container/CLI unit that repeatedly calls UOW-003.

## Fixture And Test Data Infrastructure

Parser tests use static sanitized fixtures under `tests/fixtures/search/`.

Fixture groups:

- gallery search rows and pagination
- minor gallery subject head tabs
- integrated search result list and page end
- no-keyword `search_date` success JSON
- deep-search gallery candidate extraction

Tests must not download or refresh fixtures during default execution.

## Monitoring Infrastructure

No external monitoring stack is defined for UOW-003.

UOW-003 emits safe structured collector events through UOW-001 `LoggerPort`:

- collector start
- collector end
- page fetched
- segment advanced
- candidate count summary
- range termination
- row parse failure
- deep-search per-gallery failure

Future worker/container deployment may add Prometheus/OpenTelemetry around these events, but that integration is not part of UOW-003.

## Live Smoke Test Infrastructure

Live smoke tests are optional and disabled by default.

Activation:

- `DCINSIDE_LIVE_SMOKE_ENABLED=true`

Rules:

- not part of mandatory unit tests
- not part of mandatory CI gate
- use a dedicated test marker
- perform at most one gallery or integrated search page request
- no CAPTCHA bypass or automation
- no persisted cookies
- assert only basic fetch/parse shape

## Shared Infrastructure

No shared infrastructure is created by UOW-003.

Deferred shared infrastructure:

| Infrastructure | Target Unit |
|---|---|
| queue or worker scheduler | UOW-005 and UOW-008 |
| checkpoint persistence | UOW-005 and UOW-008 |
| JSONL output storage | UOW-006 |
| Garage S3-compatible JSONL/media storage | UOW-006 and UOW-008 |
| PostgreSQL checkpoint store | UOW-008 |
| container entrypoint and env injection | UOW-008 |
| MCP server hosting | UOW-008 or later adapter unit |
| Prometheus/OpenTelemetry monitoring | later deployed runtime |
| SeaweedFS extension path | later storage evolution |

## Implementation Impact

Code generation for UOW-003 should not create Docker, Terraform, cloud resource definitions, database migrations, object storage buckets, queues, scheduler config, or monitoring configuration.

Code generation may create:

- search collector modules
- URL builders
- BeautifulSoup parsers
- traversal guard
- candidate deduper
- date parser
- range evaluator
- safe collector event builder
- static parser fixtures
- PBT strategies and tests
- optional live smoke test marker

## Deferred Items

| Deferred Item | Target Unit |
|---|---|
| post/comment/media parsers | UOW-004 |
| worker queue and checkpoint orchestration | UOW-005 |
| JSONL/media/Garage storage | UOW-006 |
| CLI runtime prompts and file creation | UOW-007 |
| container entrypoint, PostgreSQL checkpoint, MCP, deployed monitoring | UOW-008 or later adapter unit |
