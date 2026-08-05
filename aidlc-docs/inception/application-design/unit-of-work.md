# Unit Of Work

## Decomposition Decision

확정 답변에 따라 기능 흐름 기준으로 8개 Unit of Work를 둡니다. 단일 Python 패키지 `dcinside_scraper` 안에서 구현하며, CLI, container, MCP는 같은 core API를 호출합니다.

## Units

| Unit | Name | Responsibility | Primary Owner Boundary |
|---|---|---|---|
| UOW-001 | Core Models And Config | Pydantic 모델, Job 설정, validation, public API request/result schema, port protocol | models/config |
| UOW-002 | HTTP Runtime Policy | `httpx` client, request delay, retry, timeout, User-Agent rotation, Proxy, block/CAPTCHA response classification | runtime |
| UOW-003 | Search And Link Collection | gallery search, integrated search, deep search, no-keyword range, realtime link discovery, dedupe, range filter | search |
| UOW-004 | Post Detail And Content Parsing | post metadata/body, comments/replies, dccon, media, dc_video description, YouTube/link/series, `(펌)` AJAX card parsing | detail |
| UOW-005 | Job Runner And Checkpoint | `JobRunner`, `asyncio.Queue`, worker pool, lifecycle state, stop/resume, checkpoint update ordering | runtime/detail integration |
| UOW-006 | Output And Storage | local JSONL/media, failure records, S3-compatible output port, Garage default object storage, local checkpoint port | storage |
| UOW-007 | CLI Adapter | terminal options, Job creation, resume command, image/dccon options, Proxy/User-Agent import flow | adapters |
| UOW-008 | Container, MCP, And Test Harness | one-shot container contract, PostgreSQL checkpoint adapter, MCP tools, fixture tests, PBT, smoke test wiring | adapters/tests |

## Code Organization Strategy

Greenfield code should use this package layout:

```text
src/
  dcinside_scraper/
    __init__.py
    core/
      api.py
      config.py
      errors.py
      ports.py
    models/
      job.py
      post.py
      comment.py
      media.py
      checkpoint.py
    http/
      client.py
      user_agent.py
      proxy.py
      rate_limit.py
    parsers/
      gallery_search.py
      integrated_search.py
      post.py
      repost.py
      comments.py
      media.py
    jobs/
      runner.py
      collectors.py
      workers.py
      checkpointing.py
    outputs/
      jsonl.py
      media_store.py
      checkpoint_store.py
      s3_store.py
      postgres_checkpoint.py
    adapters/
      cli.py
      container.py
      mcp.py
tests/
  fixtures/
  test_*.py
```

## Implementation Order

1. UOW-001 Core Models And Config
2. UOW-002 HTTP Runtime Policy
3. UOW-003 Search And Link Collection
4. UOW-004 Post Detail And Content Parsing
5. UOW-006 Output And Storage
6. UOW-005 Job Runner And Checkpoint
7. UOW-007 CLI Adapter
8. UOW-008 Container, MCP, And Test Harness

Storage is implemented before `JobRunner` integration so result writes and checkpoint commits have concrete ports available.

## Unit Details

### UOW-001. Core Models And Config

- Defines Pydantic models for Job config, requests, post results, comments, media, repost info, checkpoint, reports, and failure records.
- Defines common enums: Job type, gallery type, media mode, dccon mode, checkpoint status, stop reason.
- Defines strict input validation shared by CLI, library, container, and MCP.
- Defines port protocols for HTTP, output, media, checkpoint, clock, and logger.

### UOW-002. HTTP Runtime Policy

- Wraps `httpx.AsyncClient`.
- Applies global request delay, retry, timeout, User-Agent, and Proxy consistently.
- Loads `user-agents.txt`, defaults to rotation every 10 requests, and falls back to one default User-Agent.
- Applies Proxy priority: explicit option first, then `.env`, then disabled.
- Classifies CAPTCHA/block/unavailable responses without bypassing CAPTCHA.

### UOW-003. Search And Link Collection

- Parses gallery search pages and integrated search pages.
- Implements direct URL normalization, gallery search, integrated search, deep search, no-keyword range search, realtime keyword search, and realtime all search.
- Keeps one sequential link collector per Job.
- Applies `(gallery_id, post_number)` dedupe and configured date/post number filters.
- Pushes `PostCandidate` values into the worker queue.

### UOW-004. Post Detail And Content Parsing

- Parses post metadata, title, author, nickname type, dates, counts, body text, and body links.
- Parses ordered content blocks for text, images, DC video, YouTube, external links, and series.
- Parses DC video description when present and stores `null` when absent.
- Detects and parses `(펌)` posts, including AJAX card metadata and media.
- Fetches and parses comments/replies and dccon metadata.

### UOW-005. Job Runner And Checkpoint

- Owns `JobRunner`, queue orchestration, worker pool lifecycle, cancellation, and resume flow.
- Saves checkpoint every 10 completed posts and immediately on manual stop, error, CAPTCHA, timeout, and normal completion.
- Updates checkpoint only after post result storage succeeds.
- Restores Job config, search position, page, completed keys, and possible remaining queue snapshot.
- Realtime termination and checkpoint behavior are validated here with UOW-003.

### UOW-006. Output And Storage

- Writes one JSON object per post to one Job JSONL file.
- Creates a new JSONL file on resume instead of appending to an old Job output.
- Stores failure records and Job reports.
- Supports local media paths and S3-compatible media/object output.
- Uses Garage as the default S3-compatible object store.
- Keeps SeaweedFS as a future replacement through the same S3-compatible port.

### UOW-007. CLI Adapter

- Provides terminal UI and command options.
- Builds `JobConfig` through shared validation.
- Supports direct URL, gallery search, integrated search, deep search, no-keyword range, resume, image mode, dccon mode, request interval, worker count, User-Agent import, and Proxy option.
- Calls core async API through `asyncio.run()`.

### UOW-008. Container, MCP, And Test Harness

- Provides one-shot worker container entrypoint.
- Reads `RESUME`, `JOB_ID`, `DATABASE_URL`, realtime env, and S3-compatible storage env.
- Adds PostgreSQL checkpoint adapter for container mode.
- Provides MCP tools for search, fetch, Job run, and resume.
- Adds parser fixture tests, Hypothesis PBT, import side-effect tests, adapter validation tests, and optional live smoke test hooks.

## Boundary Rules

- Parser components do not perform network or storage I/O.
- All network I/O goes through `HttpClient`.
- All result, media, and checkpoint writes go through storage ports.
- Adapters do not contain scraping logic.
- Core import must not start a scrape, prompt the terminal, or create files.

