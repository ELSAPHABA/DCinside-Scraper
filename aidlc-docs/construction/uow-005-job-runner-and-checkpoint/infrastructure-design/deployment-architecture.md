# Deployment Architecture - UOW-005 Job Runner And Checkpoint

## Architecture Classification

UOW-005 has no standalone deployed runtime architecture.

It is a runner package layer consumed by later runtime adapters.

```text
CLI, container worker, MCP adapter, tests, or library caller
    |
    v
UOW-005 runner package
    |
    +-- JobRunner
    +-- JobRunContext
    +-- CheckpointCoordinator
    +-- StopController
    +-- RealtimeLoopController
    +-- RunnerEventBuilder
    |
    +--> UOW-003 collector port
    +--> UOW-004 post detail port
    +--> UOW-006 output/checkpoint ports
    +--> LoggerPort / ClockPort
```

## Environment Topology

| Environment | UOW-005 Role | Infrastructure |
|---|---|---|
| Local development | imported runner package with fake or local ports | Python process |
| CI | async orchestration and PBT tests | Python process, fake services |
| Runtime scraper | called by later CLI/container/MCP adapter | caller process plus injected ports |
| Distributed platform | not owned by UOW-005 | later worker/container/queue units |

## Runtime Boundaries

UOW-005 import must not:

- read `.env`
- read process environment variables
- open network connections
- create output directories
- create `Checkpoint.json`
- start a Job automatically
- connect to Garage/S3
- connect to PostgreSQL
- create external queues

At explicit runtime calls, UOW-005 may:

- open an `anyio` task group
- create an in-process `asyncio.Queue[PostCandidate]`
- call injected collector/detail/output/checkpoint ports
- emit safe logger events
- return a `JobReport`

## In-Process Execution Shape

One Job run:

```text
JobRunner.run(JobConfig)
    |
    +-- create JobRunContext
    +-- restore completed keys when resume applies
    +-- start anyio task group
    |     |
    |     +-- CollectorTask
    |     |     |
    |     |     v
    |     |   asyncio.Queue[PostCandidate]
    |     |
    |     +-- PostWorker 1..N
    |
    +-- CheckpointCoordinator
    +-- OutputStorePort / CheckpointStorePort
    +-- JobReport
```

Concurrency is local to one Python process.

UOW-005 does not scale workers across processes or machines.

## Dependency Flow

```text
JobConfig
    |
    +-- WorkerConfig.post_worker_count -> worker task count
    +-- WorkerConfig.queue_max_size -> optional queue max size
    |
    v
JobRunner
    |
    +-- collector dependency -> PostCandidate values
    +-- detail dependency -> PostResult or per-post failure
    +-- output dependency -> posts/failures/report storage
    +-- checkpoint dependency -> save/load runner state
```

Checkpoint commit ordering is owned by UOW-005.

Storage durability and layout are owned by UOW-006 or later storage adapters.

## External Services

| Service Type | Status | Reason |
|---|---|---|
| DCinside HTTP | Indirect only | accessed through UOW-002/UOW-004 dependencies |
| Local filesystem | Indirect only | accessed through UOW-006 storage ports |
| S3/Garage | Indirect/deferred | storage adapter responsibility |
| PostgreSQL | Deferred | checkpoint adapter belongs to later work |
| Redis/Celery/RQ | Not used | distributed queue is out of UOW-005 scope |
| MCP server | Deferred | adapter responsibility |
| Monitoring backend | Deferred | UOW-005 emits safe events only |

## Test Architecture

Default test path:

```text
pytest / Hypothesis
    |
    +-- fake collector
    +-- fake detail service
    +-- fake output store
    +-- fake checkpoint store
    +-- fake logger/clock
    |
    v
JobRunner orchestration tests
```

Default test gate validates:

- normal completion
- bounded worker behavior
- completed-key skip
- checkpoint save interval
- checkpoint-after-storage ordering
- manual stop
- CAPTCHA/block stop
- recoverable per-post failure
- resume dedupe
- realtime termination

No live services are required.

## Security Boundary

The deployment boundary for UOW-005 is the caller process plus injected dependencies.

Required behavior:

- depend on validated config
- use injected ports
- emit only safe structured events
- stop new work on CAPTCHA/block
- avoid raw proxy/cookie/header/body logging

Security behavior outside UOW-005:

- proxy secret loading
- `.env` parsing
- credential injection
- deployed log storage
- container secret management

## Infrastructure Handoff

UOW-005 hands off runner capability to later units:

- importable `JobRunner`
- reusable `run_job`/`resume_job` delegation target
- in-process worker orchestration
- checkpoint timing
- safe stop behavior
- fake-friendly ports for adapter testing

Later units decide:

- terminal UI and signal handling
- Docker image and entrypoint
- Garage environment variables and buckets
- PostgreSQL checkpoint schema
- distributed retry/DLQ processing
- MCP job control commands
- deployed monitoring
