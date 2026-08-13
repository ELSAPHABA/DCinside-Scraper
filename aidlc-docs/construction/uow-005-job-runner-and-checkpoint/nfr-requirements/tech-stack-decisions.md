# Tech Stack Decisions - UOW-005 Job Runner And Checkpoint

## Runtime And Language

| Decision | Selection | Rationale |
|---|---|---|
| Language | Python 3.11+ | Matches existing package baseline. |
| Async lifecycle | `anyio` task group/cancellation scope | Confirmed by questionnaire Q1. |
| Candidate queue | `asyncio.Queue[PostCandidate]` | Preserves the Functional Design and Q2 queue contract. |
| Model contracts | existing Pydantic models | Reuse UOW-001 validated models. |
| Storage boundary | existing UOW-006 ports | Keeps checkpoint/output implementation outside JobRunner. |

## Dependency Decisions

| Dependency | Selection | Scope |
|---|---|---|
| `anyio` | Add direct runtime dependency | Used directly by UOW-005 orchestration. |
| `asyncio` | Standard library | Queue and low-level async primitives where needed. |
| Celery/RQ/Redis queue | Not added | Distributed worker orchestration is out of scope. |
| Scheduler library | Not added | Realtime timer/end-at checks are small enough for the runner. |
| Pydantic | existing core dependency | Existing model validation and serialization. |

## Concurrency Strategy

| Area | Decision |
|---|---|
| Collector | one sequential producer task per Job |
| Queue item | `PostCandidate` |
| Worker pool | `WorkerConfig.post_worker_count` consumers |
| Media download limit | `WorkerConfig.media_worker_count` semaphore |
| Queue max size | `WorkerConfig.queue_max_size` when set |
| Cancellation | `anyio` task lifecycle; graceful current-candidate finish path |
| Realtime loop | JobRunner-owned polling loop |

## Checkpoint Strategy

| Area | Decision |
|---|---|
| Advancement | after output/failure storage success only |
| Normal interval | every 10 completed outcomes |
| Terminal save | required on all terminal paths |
| Queue snapshot | optional, best effort only |
| Resume primary keys | `search_position` plus `completed_keys` |
| Resumed output | new UOW-006 output run |

## Security Strategy

| Area | Decision |
|---|---|
| Observability | safe structured events |
| CAPTCHA/block | fail-closed Job stop |
| Raw HTML/body | forbidden in JobRunner logs/reports |
| Proxy credentials | forbidden in JobRunner logs/reports |
| Cookies/headers | forbidden in JobRunner logs/reports |

## Testing Stack

| Decision | Selection | Rationale |
|---|---|---|
| Example tests | pytest | Existing test runner. |
| Async tests | pytest plus anyio-compatible execution | Required because UOW-005 uses anyio. |
| PBT | Hypothesis | Existing project choice. |
| Test doubles | hand-written fakes | JobRunner contracts are small. |
| Live tests | excluded from default gate | Keeps tests deterministic. |

Required default test categories:

- fake Job completion
- bounded worker consumption
- completed-key skip
- checkpoint advancement ordering
- checkpoint save interval
- manual stop
- CAPTCHA/block stop
- recoverable per-post failure
- resume dedupe
- realtime termination
- pure state PBT

## Deferred Decisions

These are intentionally left for later units:

- CLI stop signal mapping
- container worker process supervision
- PostgreSQL checkpoint adapter
- distributed queue runtime
- MCP job control surface
- live DCinside smoke tests
