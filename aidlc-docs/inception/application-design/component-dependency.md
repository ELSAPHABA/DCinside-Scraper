# Component Dependencies

## Dependency Matrix

| Component | Depends On | Communication |
|---|---|---|
| `CliAdapter` | `JobConfigValidator`, `ScraperFacade` | Direct async call through `asyncio.run()` |
| `ContainerAdapter` | `JobConfigValidator`, `ScraperFacade` | Direct async call |
| `McpAdapter` | `JobConfigValidator`, `ScraperFacade` | Direct async call from MCP tool |
| `ScraperFacade` | `JobRunner`, parsers for single-shot APIs | Direct async call |
| `JobRunner` | `LinkCollector`, `PostWorkerPool`, storage ports | Direct async call |
| `LinkCollector` | `HttpClient`, `GallerySearchParser`, `IntegratedSearchParser` | HTTP + parser calls |
| `PostWorkerPool` | `PostScrapeService`, `OutputStorePort`, `CheckpointStorePort` | Queue + direct async call |
| `PostScrapeService` | `HttpClient`, `PostParser`, `RepostService`, `CommentService`, `MediaService` | HTTP + parser calls |
| `RepostService` | `HttpClient`, `RepostParser` | AJAX POST + parser call |
| `CommentService` | `HttpClient`, `CommentParser` | Comment API POST + parser call |
| `MediaService` | `HttpClient`, `MediaParser`, `MediaStorePort` | Download + store call |
| `HttpClient` | `UserAgentProvider`, `ProxyProvider`, `ClockPort`, `LoggerPort` | Direct calls |
| `OutputStorePort` | Local or S3-compatible implementation | Port implementation |
| `MediaStorePort` | Local or S3-compatible implementation | Port implementation |
| `CheckpointStorePort` | Local or PostgreSQL implementation | Port implementation |

## Runtime Flow

```
--------------+      +----------------+      +-------------+
| CLI/MCP/CTR | ---> | ScraperFacade  | ---> | JobRunner   |
+--------------+      +----------------+      +-------------+
                                                 |
                         +-----------------------+-----------------------+
                         |                                               |
                         v                                               v
                +----------------+                              +----------------+
                | LinkCollector  |                              | PostWorkerPool |
                +----------------+                              +----------------+
                         |                                               |
                         v                                               v
                  +------------+                                 +---------------+
                  | HttpClient | <------------------------------ | PostScrapeSvc |
                  +------------+                                 +---------------+
                         |                                               |
                         v                                               v
                  +------------+                              +--------------------+
                  | DCinside   |                              | Output/Checkpoint |
                  +------------+                              +--------------------+
```

## Storage Flow

```
PostResult
    |
    v
+-----------------+       local mode        +------------------+
| OutputStorePort | ----------------------> | local JSONL file |
+-----------------+                         +------------------+
    |
    | container mode
    v
+-----------------------------+
| Garage S3-compatible object |
+-----------------------------+

Checkpoint
    |
    +--> local mode: Checkpoint.json
    |
    +--> container mode: PostgreSQL
```

## Communication Patterns

1. **Adapter to core**: CLI, container, MCP only translate input/output. They do not parse DCinside HTML.
2. **Collector to worker**: `LinkCollector` writes `PostCandidate` values to an `asyncio.Queue`.
3. **Worker to output**: `PostWorkerPool` stores `PostResult` through `OutputStorePort`.
4. **Output to checkpoint**: checkpoint completed position is updated only after post result storage succeeds.
5. **HTTP policy**: all DCinside requests go through `HttpClient`; parsers never call network directly.
6. **Storage policy**: concrete storage implementations stay behind ports. Garage is the default S3-compatible object store; SeaweedFS can replace it later through the same S3-compatible port if requirements justify it.

## Data Ownership

| Data | Owner Component | Storage |
|---|---|---|
| Job config | `JobConfigValidator` | In memory, checkpoint snapshot |
| Post result JSONL | `OutputStorePort` | Local file or S3-compatible object store |
| Media files | `MediaStorePort` | Local directory or S3-compatible object store |
| Failed post/media records | `OutputStorePort` | Failure JSONL/report |
| Checkpoint/status | `CheckpointStorePort` | `Checkpoint.json` or PostgreSQL |
| Structured logs | `LoggerPort` implementation | stdout/stderr or local logs |

