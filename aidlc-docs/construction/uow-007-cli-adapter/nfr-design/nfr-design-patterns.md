# NFR Design Patterns - UOW-007 CLI Adapter

This document translates UOW-007 NFR requirements into implementation patterns for the CLI adapter.

## Confirmed Design Answers

| Question | Answer | Design Pattern |
|---|---|---|
| Q1 | A | Keep first implementation in `src/dcinside_scraper/adapters/cli.py`; split later only if tests or file size force it. |
| Q2 | A | Normalize both `argparse.Namespace` and wizard answers to a small command dict before model building. |
| Q3 | A | Use a small `WizardSession(input_stream, output_stream)` helper for prompt/read/write only. |
| Q4 | A | Use one `print_error(exc, *, stage, output, include_traceback=True)` function. |
| Q5 | A | Update `.env` through `update_proxy_env(path, values)` using temp file and `os.replace`. |
| Q6 | A | Import User-Agent files through `import_user_agents(source, destination)` with validation and atomic replace. |
| Q7 | A | Connect first interrupt to `JobRunner.request_stop()` and second interrupt to best-effort exit `1`. |
| Q8 | A | Use a function/context helper for local runtime assembly; do not add a factory class. |
| Q9 | A | Put example tests in `tests/test_cli_adapter.py`, PBT in `tests/test_cli_properties.py`, strategies in `tests/strategies/cli.py`. |
| Q10 | A + B | Support console script, `python -m dcinside_scraper.adapters.cli`, and a thin root `main.py` wrapper. |

No follow-up question is required.

## Module Pattern

First implementation lives in one module:

```text
src/dcinside_scraper/adapters/
  __init__.py
  cli.py
```

The root wrapper is intentionally thin:

```text
main.py
```

`main.py` may only import and call `dcinside_scraper.adapters.cli.main`.

It must not contain parser setup, wizard prompts, model building, runtime assembly, or scraping logic.

## Command Normalization Pattern

Both command mode and wizard mode flow into the same model builders:

```text
argparse.Namespace
  -> command dict
  -> build_job_config(command)
  -> JobConfig

wizard answers
  -> command dict
  -> build_job_config(command)
  -> JobConfig
```

For resume:

```text
argparse.Namespace or wizard answers
  -> command dict
  -> build_resume_request(command)
  -> ResumeRequest
```

The command dict is an internal adapter shape. It must not become a public model unless later reuse requires it.

## Wizard Pattern

`WizardSession` owns only terminal interaction:

- read one line from input stream
- write prompts and safe messages to output stream
- show numbered menu
- retry invalid input
- return a command dict or exit intent

It does not:

- validate Pydantic models directly
- create HTTP clients
- call `run_job`
- parse DCinside pages
- write output files unless delegating to import/config command handlers

Wizard defaults and cancel paths:

- defaults are shown inline when available
- invalid values retry current prompt
- `q` returns to previous menu or exits
- empty required input cancels the current action when no default exists

## Safe Error Pattern

`print_error` writes:

1. safe mapped error summary from `ErrorMapper.map(exc, stage=...)`
2. traceback from `traceback.format_exception(...)` when enabled

It must not print:

- locals
- full config objects
- raw `.env`
- proxy password
- cookies
- raw headers
- raw HTML/body/content
- tokens

Known validation and scraper errors should use the safe mapped summary before traceback output.

## `.env` Update Pattern

`update_proxy_env(path, values)`:

1. reads existing file if present
2. preserves unrelated lines
3. replaces or appends only:
   - `DCINSIDE_PROXY_HOST`
   - `DCINSIDE_PROXY_ID`
   - `DCINSIDE_PROXY_PW`
4. writes to temp file in the same directory
5. calls `os.replace`

The helper must not call `load_dotenv()` and must not mutate `os.environ`.

## User-Agent Import Pattern

`import_user_agents(source, destination)`:

1. verifies source is a regular file
2. reads UTF-8 text
3. requires at least one non-blank line
4. writes destination through temp file plus `os.replace`

It does not perform browser grammar validation.

## Ctrl+C Pattern

Running command creates a concrete `JobRunner`.

Interrupt behavior:

- first interrupt calls `runner.request_stop()`
- user sees a safe "stopping" message
- CLI waits for final checkpoint/report path
- second interrupt exits with code `1` after best-effort HTTP close

The signal hook must be scoped to the running command and restored afterward when feasible.

## Runtime Assembly Pattern

Use a small helper such as:

```text
build_local_runtime(config, runtime_options)
```

The helper creates:

- `HttpClient`
- `LinkCollectorService`
- `PostDetailService`
- `OutputRunLayout`
- `LocalOutputStore`
- `LocalCheckpointStore`
- `JobRunner`

No factory class is required.

## Entrypoint Pattern

Supported official entrypoints:

- `python -m dcinside_scraper.adapters.cli ...`
- installed console script, for example `dcinside-scraper ...`
- root `python main.py ...`

All three must delegate to the same `main(argv=None) -> int`.

`pyproject.toml` adds a console script. Root `main.py` is only a compatibility wrapper.

## Test Pattern

Default tests:

```text
tests/test_cli_adapter.py
tests/test_cli_properties.py
tests/strategies/cli.py
```

Default tests must not use live network.

Test doubles:

- fake runner
- fake input/output streams
- temporary directories for `.env` and `user-agents.txt`
- monkeypatched runtime helper where needed

PBT targets pure transformations only.

## Compliance Check

| Requirement Area | Design Compliance |
|---|---|
| Security | safe error summary, no locals/config dump, getpass password, allow-list `.env` update |
| Resiliency | atomic config file replace, graceful first Ctrl+C, best-effort second Ctrl+C cleanup |
| Maintainability | one module first, shared builders, no new CLI dependency |
| PBT | pure command/wizard/env/path mappings only |
| Import safety | parser and helpers load without file, prompt, or network side effects |
