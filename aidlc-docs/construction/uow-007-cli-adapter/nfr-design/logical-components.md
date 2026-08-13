# Logical Components - UOW-007 CLI Adapter

This document defines logical components for the UOW-007 CLI adapter implementation.

## Component Overview

| Component | Responsibility |
|---|---|
| `CliMain` | top-level `main(argv=None) -> int` entrypoint |
| `ArgumentParserBuilder` | builds stdlib `argparse` parser and subcommands |
| `CommandNormalizer` | converts `argparse.Namespace` or wizard answers to command dicts |
| `JobConfigBuilder` | builds validated `JobConfig` |
| `ResumeRequestBuilder` | builds validated `ResumeRequest` |
| `WizardSession` | numbered interactive menu and prompt I/O |
| `ErrorReporter` | safe summary plus traceback output |
| `ProxyEnvUpdater` | preserves `.env` and updates only proxy keys |
| `UserAgentImporter` | validates and atomically imports `user-agents.txt` |
| `LocalRuntimeBuilder` | assembles existing runtime/search/detail/output/checkpoint objects |
| `InterruptController` | maps Ctrl+C to graceful stop and forced exit boundary |
| `EntrypointWrappers` | console script, `python -m`, and root `main.py` delegation |

## CliMain

Location:

- `src/dcinside_scraper/adapters/cli.py`

Responsibilities:

- build parser
- dispatch subcommands
- call wizard or command handlers
- map exceptions to exit codes
- return integer exit code

Must not:

- run on import
- read `.env` on import
- read `user-agents.txt` on import
- prompt on import
- perform network I/O on import

## ArgumentParserBuilder

Responsibilities:

- define `run`
- define `resume`
- define `import-user-agents`
- define `configure-proxy`
- define `wizard`
- attach only parsing metadata and defaults

The parser should not create runtime clients or files while being built.

## CommandNormalizer

Inputs:

- `argparse.Namespace`
- wizard answer dict

Output:

- small command dict

Responsibilities:

- normalize source names
- normalize option keys
- normalize boolean flags
- preserve unknown validation for Pydantic model builders

The command dict is internal to `cli.py`.

## JobConfigBuilder

Function:

```text
build_job_config(command: Mapping[str, object]) -> JobConfig
```

Responsibilities:

- build selected source model
- apply realtime environment when enabled
- build `ScrapeOptions`
- build `WorkerConfig`
- build `StorageConfig`
- assemble `LocalMediaStore` with the same `OutputRunLayout` used by `LocalOutputStore`
- validate through Pydantic model construction

Must reuse existing UOW-001 models.

## ResumeRequestBuilder

Function:

```text
build_resume_request(command: Mapping[str, object]) -> ResumeRequest
```

Responsibilities:

- accept explicit `job_id`
- allow omitted `job_id`
- validate through Pydantic model construction

## WizardSession

Constructor shape:

```text
WizardSession(input_stream, output_stream)
```

Responsibilities:

- show main menu
- collect start-scrape answers
- collect resume answers
- collect import User-Agent answers
- delegate Proxy configure prompts
- support retry on invalid input
- support cancel/back/exit
- return command dicts or command intent

Must not:

- scrape
- parse HTML
- call HTTP
- write output JSONL
- own a separate validation system

## ErrorReporter

Function:

```text
print_error(exc, *, stage: str | None, output, include_traceback: bool = True) -> None
```

Responsibilities:

- call `ErrorMapper.map`
- print safe code/message/details
- print traceback when enabled

Forbidden output:

- proxy password
- raw `.env`
- cookies
- raw headers
- raw HTML/body/content
- tokens
- locals dump
- full config dump

## ProxyEnvUpdater

Function:

```text
update_proxy_env(path, values) -> None
```

Responsibilities:

- read existing `.env` if present
- preserve unrelated lines
- replace or append `DCINSIDE_PROXY_HOST`
- replace or append `DCINSIDE_PROXY_ID`
- replace or append `DCINSIDE_PROXY_PW`
- write temp file
- replace target atomically

Uses:

- `pathlib`
- `tempfile`
- `os.replace`

Does not use:

- `load_dotenv`
- process environment mutation

## UserAgentImporter

Function:

```text
import_user_agents(source, destination) -> None
```

Responsibilities:

- reject missing path
- reject non-regular file
- reject invalid UTF-8
- reject all-blank file
- write destination atomically

Does not:

- validate browser grammar
- fetch User-Agent lists from the network

## LocalRuntimeBuilder

Function or async context helper:

```text
build_local_runtime(config, runtime_options)
```

Creates:

- `HttpRuntimeConfig`
- `HttpClient`
- `LinkCollectorService`
- `PostDetailService`
- `OutputRunLayout`
- `LocalOutputStore`
- `LocalCheckpointStore`
- `JobRunner`

This component wires existing services only.

## InterruptController

Responsibilities:

- install a scoped interrupt handler during a running Job
- call `runner.request_stop()` on first interrupt
- mark second interrupt as forced exit
- restore previous handler when feasible
- return exit code `1` for forced exit

It must not bypass UOW-005 final checkpoint behavior on the first interrupt path.

## EntrypointWrappers

Supported wrappers:

| Wrapper | Behavior |
|---|---|
| `python -m dcinside_scraper.adapters.cli ...` | executes module wrapper that calls `main()` |
| console script | calls `dcinside_scraper.adapters.cli:main` |
| `python main.py ...` | thin root compatibility wrapper calling the same `main()` |

Only `CliMain` owns CLI behavior.

## Test Components

### Example Tests

File:

- `tests/test_cli_adapter.py`

Covers:

- import safety
- parser subcommands
- builders
- wizard input/output
- fake runner
- Ctrl+C hook
- config file helpers

### Property Tests

File:

- `tests/test_cli_properties.py`

Strategies:

- `tests/strategies/cli.py`

Covers:

- command dict normalization
- wizard answer normalization
- realtime env exactly-one rule
- exit code mapping
- safe error redaction
- local config path handling

## Boundary Summary

UOW-007 owns terminal input/output and dependency wiring.

It delegates:

- validation to UOW-001 models
- HTTP behavior to UOW-002
- link collection to UOW-003
- post parsing to UOW-004
- orchestration/checkpoints to UOW-005
- file layout/storage safety to UOW-006
