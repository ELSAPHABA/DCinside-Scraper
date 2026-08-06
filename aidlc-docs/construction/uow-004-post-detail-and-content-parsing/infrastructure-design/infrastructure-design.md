# Infrastructure Design - UOW-004 Post Detail And Content Parsing

## Scope

UOW-004 is not a deployable scraper worker. It defines an importable Python post detail and comment parsing layer used by later units.

In scope:

- detail HTML fetch through injected UOW-002 `HttpClient`
- BeautifulSoup metadata parsing
- ordered content block parsing
- repost AJAX parsing
- DC video iframe metadata parsing
- comment/reply AJAX parsing
- rendered comment HTML fallback fixture parsing
- safe detail failure metadata
- fixture/PBT tests
- optional live smoke test boundary
- safe structured detail events

Out of scope:

- JSONL, Garage, PostgreSQL, or object storage adapters
- media file download/storage
- queue lifecycle
- checkpoint persistence
- CLI prompt UX
- container entrypoint
- MCP hosting

## Confirmed Decisions

| Area | Decision |
|---|---|
| Deployment environment | N/A for standalone UOW-004 service/container deployment |
| Compute and parallelism | one `PostRequest` at a time; no worker pool or persistent compute owned by UOW-004 |
| HTTP/network boundary | UOW-004 receives UOW-002 `HttpClient`; it does not configure proxy, User-Agent, limiter, cookies, or retry |
| Runtime configuration | consumes validated `PostRequest`, `CommentRequest`, `ScrapeOptions`, and in-memory options only |
| Fixture/test data | static sanitized HTML/JSON fixtures under `tests/fixtures/post_detail/` |
| Live smoke | excluded by default; env-gated one post plus one comment page smoke only |
| Output/media infrastructure | no JSONL, Garage, or media storage mapping in UOW-004 |
| Monitoring/shared infrastructure | no external monitoring, Garage, PostgreSQL, or queue; safe events through UOW-001 `LoggerPort` only |

## Deployment Environment

UOW-004 is an importable library layer, not a standalone runtime.

Required environment:

- Python package build/import environment
- local unit/PBT execution environment
- CI unit/PBT execution environment
- optional live smoke execution environment when explicitly enabled

Not required:

- Docker image owned by UOW-004
- scheduler
- queue consumer
- hosted service
- MCP server process
- cloud account resources
- object storage bucket
- database migration

## Compute Infrastructure

No persistent compute infrastructure is provisioned for UOW-004.

Execution targets:

- local developer machine for parser, normalization, failure-shape, and fixture tests
- CI runner for unit tests and property-based tests
- optional manual smoke run against DCinside when enabled by environment variable

UOW-004 parses one requested post at a time from the caller perspective. Multi-worker execution, queue insertion, worker count, checkpoint save, and realtime loop execution are deferred to later JobRunner/worker units.

## HTTP And Network Boundary

UOW-004 uses a caller-provided UOW-002 `HttpClient`.

UOW-004 may request through the injected client:

- post detail HTML
- repost AJAX payload
- DC video iframe HTML
- comment AJAX pages

UOW-004 must not:

- create its own `httpx.AsyncClient`
- configure proxy settings
- rotate User-Agent values
- configure request rate limits
- read or persist cookies
- implement a separate retry loop
- bypass CAPTCHA

CAPTCHA/block typed errors from UOW-002 propagate to the caller.

## Runtime Configuration Boundary

UOW-004 consumes already-validated request/config models and runtime objects from its caller.

Inputs:

- `PostRequest`
- `CommentRequest`
- `ScrapeOptions`
- injected `HttpClient`
- optional in-memory parser/service options

UOW-004 import must not:

- make network requests
- read `.env`
- read `user-agents.txt`
- read environment variables
- prompt terminal input
- write files
- create queues

Live smoke environment parsing belongs to the test file, not the production parser package.

## Fixture And Test Data Infrastructure

Parser tests use static sanitized fixtures under `tests/fixtures/post_detail/`.

Fixture groups:

- normal post detail HTML
- mixed content detail HTML
- repost AJAX response
- DC video iframe response
- comment AJAX JSON
- rendered comment HTML fallback
- optional field missing cases

Tests must not download or refresh fixtures during default execution.

## Monitoring Infrastructure

No external monitoring stack is defined for UOW-004.

UOW-004 emits safe structured detail events through UOW-001 `LoggerPort`:

- detail parse start/end
- metadata parse failure
- content block summary
- comment page summary
- optional subfetch failure
- repost parse result
- DC video metadata result

Future worker/container deployment may add Prometheus/OpenTelemetry around these events, but that integration is not part of UOW-004.

## Live Smoke Test Infrastructure

Live smoke tests are optional and disabled by default.

Activation:

- `DCINSIDE_LIVE_SMOKE_ENABLED=true`

Rules:

- not part of mandatory unit tests
- not part of mandatory CI gate
- use a dedicated test marker
- perform at most one post detail page request
- perform at most one comment page request
- no media download
- no CAPTCHA bypass or automation
- no persisted cookies
- assert only basic fetch/parse shape

## Shared Infrastructure

No shared infrastructure is created by UOW-004.

Deferred shared infrastructure:

| Infrastructure | Target Unit |
|---|---|
| queue or worker scheduler | UOW-005 and UOW-008 |
| checkpoint persistence | UOW-005 and UOW-008 |
| JSONL output storage | UOW-006 |
| media download/storage | UOW-006 |
| Garage S3-compatible JSONL/media storage | UOW-006 and UOW-008 |
| PostgreSQL checkpoint store | UOW-008 |
| container entrypoint and env injection | UOW-008 |
| MCP server hosting | UOW-008 or later adapter unit |
| Prometheus/OpenTelemetry monitoring | later deployed runtime |
| metadata parsing failure retry store/orchestrator | future retry unit |

## Implementation Impact

Code generation for UOW-004 should not create Docker, Terraform, cloud resource definitions, database migrations, object storage buckets, queues, scheduler config, monitoring configuration, JSONL writers, or media download stores.

Code generation may create:

- post detail service modules
- BeautifulSoup metadata/content/comment parsers
- repost AJAX parser/client logic using injected `HttpClient`
- DC video iframe metadata resolver using injected `HttpClient`
- comment pagination guard
- detail failure recorder
- safe detail event builder
- normalization helpers
- static parser fixtures
- PBT strategies and tests
- optional live smoke test marker

## Deferred Items

| Deferred Item | Target Unit |
|---|---|
| worker queue and checkpoint orchestration | UOW-005 |
| JSONL/media/Garage storage | UOW-006 |
| CLI runtime prompts and file creation | UOW-007 |
| container entrypoint, PostgreSQL checkpoint, MCP, deployed monitoring | UOW-008 or later adapter unit |
| metadata parsing failure retry storage and orchestration | future retry unit |
