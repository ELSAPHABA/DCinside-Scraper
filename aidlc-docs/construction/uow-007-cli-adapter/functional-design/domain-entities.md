# Domain Entities - UOW-007 CLI Adapter

## Existing Contract Entities

UOW-007 reuses the UOW-001 through UOW-006 contracts below.

| Entity | Source | Role |
|---|---|---|
| `JobConfig` | `models/job.py` | validated Job payload built from CLI arguments |
| `ResumeRequest` | `models/job.py` | resume request built from CLI arguments |
| `DirectPostSource` | `models/job.py` | direct post URL source |
| `GallerySearchSource` | `models/job.py` | gallery search source |
| `IntegratedSearchSource` | `models/job.py` | integrated search source |
| `DeepSearchSource` | `models/job.py` | deep search source |
| `NoKeywordRangeSource` | `models/job.py` | no-keyword range source |
| `RealtimeKeywordSource` | `models/job.py` | realtime keyword source built from environment variables |
| `RealtimeAllSource` | `models/job.py` | realtime all source built from environment variables |
| `ScrapeOptions` | `models/job.py` | comments, media, dccon, delay, retries, comment page limit, and range options |
| `WorkerConfig` | `models/job.py` | post worker count, media download concurrency, and queue max size |
| `StorageConfig` | `models/job.py` | output base path and storage backend selection |
| `HttpRuntimeConfig` | `http/runtime.py` | request delay, timeout, retry, User-Agent, Proxy, and execution directory |
| `UserAgentConfig` | `http/runtime.py` | User-Agent file and rotation settings |
| `ProxyConfig` | `http/runtime.py` | resolved explicit Proxy candidate |
| `HttpClient` | `http/runtime.py` | HTTP runtime client used by collectors, detail service, and media downloads |
| `LinkCollectorService` | `search/collection.py` | source-specific link collection facade |
| `PostDetailService` | `post_detail/detail.py` | post/comment/detail fetch and parse facade |
| `OutputRunLayout` | `outputs/local.py` | local output path layout value object |
| `LocalOutputStore` | `outputs/local.py` | local post/failure/report output store |
| `LocalMediaStore` | `outputs/local.py` | local media file/metadata store |
| `LocalCheckpointStore` | `outputs/local.py` | local `Checkpoint.json` store |
| `JobReport` | `models/report.py` | final report printed by CLI |
| `ErrorMapper` | `core/errors.py` | maps exceptions to safe adapter-facing errors |

## CLI Components

### CliMain

Top-level function `main(argv: list[str] | None = None) -> int`.

Responsibilities:

- build the argument parser
- dispatch subcommands
- call command handlers
- convert exceptions into safe output and exit codes
- return an integer exit code

Non-responsibilities:

- scrape pages
- parse HTML
- write checkpoint ordering directly
- perform work on import

### ArgumentParserFactory

Factory for the stdlib `argparse.ArgumentParser`.

Responsibilities:

- define `run`
- define `resume`
- define `import-user-agents`
- define `configure-proxy`
- define `wizard`
- keep source-specific options grouped and validated through model builders

### JobConfigBuilder

Pure helper that converts parsed CLI arguments and realtime environment into `JobConfig`.

Responsibilities:

- choose the source variant
- build range filters
- build scrape options
- build worker config
- build storage config
- call Pydantic validation

### ResumeRequestBuilder

Pure helper that converts parsed CLI arguments into `ResumeRequest`.

Responsibilities:

- accept explicit `job_id`
- allow omitted `job_id` so local checkpoint lookup can load latest
- call Pydantic validation

### RealtimeEnvReader

Reads only `DCINSIDE_REALTIME_*` variables.

Responsibilities:

- detect realtime enabled state
- build `RealtimeKeywordSource` or `RealtimeAllSource`
- combine realtime environment with CLI gallery scope options when a realtime source requires gallery ID/type
- enforce exactly one termination condition through model validation
- report safe validation errors

### LocalRuntimeFactory

Small composition component for local runs.

Responsibilities:

- build `HttpRuntimeConfig`
- create one `HttpClient`
- create `LinkCollectorService`
- create `PostDetailService`
- create `OutputRunLayout`
- create `LocalOutputStore`
- create `LocalCheckpointStore`

This component wires existing services. It does not introduce another scraping abstraction.

### UserAgentImportCommand

Command handler for `import-user-agents`.

Responsibilities:

- validate source file readability
- copy source file to `user-agents.txt`
- preserve plaintext
- print safe success/failure messages

### ProxyConfigureCommand

Command handler for `configure-proxy`.

Responsibilities:

- warn about plaintext credential storage
- collect host, ID, and password
- write `.env` with documented keys
- avoid printing raw password or raw `.env`

### TerminalReporter

Formats human terminal output.

Responsibilities:

- print start summary
- print final report summary
- print resume command
- print safe error summary
- print traceback according to Q9 while preserving redaction rules

### WizardCommandHandler

Interactive numbered menu handler.

Responsibilities:

- show the main wizard menu
- collect source and option answers for a new scrape
- collect resume `job_id` when needed
- delegate User-Agent import and Proxy configure choices to existing command handlers
- convert answers to the same command entities used by command mode
- return without side effects when the user chooses exit

## Command Entities

### RunCommand

Represents parsed `run` command intent.

Fields:

- source type
- source-specific identifiers and ranges
- output path
- User-Agent file and rotation interval
- Proxy option values
- scrape options
- worker options

Maps to:

- `JobConfig`
- `HttpRuntimeConfig`

### ResumeCommand

Represents parsed `resume` command intent.

Fields:

- optional `job_id`
- output path
- User-Agent and Proxy runtime options where applicable

Maps to:

- `ResumeRequest`
- local runtime dependencies

### ImportUserAgentsCommand

Represents parsed `import-user-agents` command intent.

Fields:

- source file path
- execution directory

Maps to:

- file copy to `user-agents.txt`

### ConfigureProxyCommand

Represents parsed `configure-proxy` command intent.

Fields:

- proxy host
- proxy ID
- proxy password
- execution directory

Maps to:

- plaintext `.env`
- later `ProxyConfig` via UOW-002 loading rules

### WizardCommand

Represents interactive numbered menu intent.

Fields:

- selected menu action
- collected command answers
- execution directory

Maps to:

- `RunCommand`
- `ResumeCommand`
- `ImportUserAgentsCommand`
- `ConfigureProxyCommand`

## Exit Code Entity

### CliExitCode

Logical constants:

| Name | Value | Meaning |
|---|---:|---|
| `SUCCESS` | `0` | Job completed successfully or command completed successfully |
| `RUNTIME_ERROR` | `1` | stopped, CAPTCHA, blocked, storage, network, parse, or unexpected runtime failure |
| `VALIDATION_ERROR` | `2` | CLI argument, environment, or Pydantic validation failure |

## Entity Boundaries

- CLI command entities are adapter input shapes, not domain storage records.
- `JobConfig` remains the canonical scrape request model.
- `HttpRuntimeConfig` remains the canonical HTTP runtime model.
- `OutputRunLayout` remains the canonical local file layout model.
- Terminal output is operational feedback, not JSONL data.
- Proxy credentials are runtime input only and must not become domain data.
