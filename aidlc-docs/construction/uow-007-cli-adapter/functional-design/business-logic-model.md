# Business Logic Model - UOW-007 CLI Adapter

## Purpose

UOW-007 provides the local terminal adapter for running the scraper.

This unit owns command parsing, the interactive wizard menu, CLI-to-model mapping, local dependency assembly, User-Agent import, Proxy `.env` setup, terminal messages, exit codes, and the resume command. It does not own scraping logic, parser selectors, worker queue internals, storage layout rules, container entrypoints, PostgreSQL checkpoint storage, MCP tools, or GUI/Web UI.

## Confirmed Decisions

| Area | Decision |
|---|---|
| Entrypoint | `dcinside_scraper.adapters.cli.main(argv: list[str] | None = None) -> int` |
| Console script | `pyproject.toml` console script calls `main` |
| Import safety | importing the CLI module must not run a Job, create files, prompt, or perform network I/O |
| Command shape | stdlib `argparse` with `run`, `resume`, `import-user-agents`, `configure-proxy`, and `wizard` subcommands |
| Run sources | `run --source direct-post|gallery-search|integrated-search|deep-search|no-keyword-range` |
| Realtime source | read `DCINSIDE_REALTIME_*` environment variables and build realtime source models |
| Model mapping | pure `build_job_config(args) -> JobConfig` and `build_resume_request(args) -> ResumeRequest` helpers |
| Runtime assembly | CLI creates existing runtime/search/detail/output/checkpoint objects and calls `core.api.run_job()` or `core.api.resume_job()` |
| Output base | `--output-path` maps to `StorageConfig.base_output_path`; omitted value uses current working directory through UOW-006 |
| User-Agent | `--user-agent-file` and `--user-agent-rotate-every` configure current run; `import-user-agents` copies to `user-agents.txt` |
| Proxy | explicit CLI proxy values win, then `.env`, then disabled; `configure-proxy` writes plaintext `.env` after warning |
| Scrape options | media, dccon, comments, delay, worker count, queue size, and comment page limit map to existing models |
| Terminal output | print safe start summary, final report summary, resume command, and traceback |
| Exit codes | success `0`, validation error `2`, stopped/CAPTCHA/runtime error `1` |
| Wizard | interactive numbered wizard is included in UOW-007 and must reuse the same builders and core API as command mode |

## Command Flow

1. `main(argv)` builds an `argparse.ArgumentParser`.
2. Parser selects one subcommand.
3. CLI resolves the execution directory from the process working directory unless a later design explicitly adds another base option.
4. CLI builds command-specific models or performs command-specific file operations.
5. CLI prints safe human-readable status.
6. CLI returns a process exit code.

`main()` returns an integer. The console script or `if __name__ == "__main__"` wrapper may call `raise SystemExit(main())`.

## `run` Flow

1. Parse `run` options.
2. If `DCINSIDE_REALTIME_ENABLED=true`, build a realtime source from environment variables.
3. If realtime environment is not enabled, build the selected source from `--source`.
4. Build `ScrapeOptions`, `WorkerConfig`, and `StorageConfig`.
5. Validate the resulting `JobConfig` through Pydantic model construction.
6. Build `HttpRuntimeConfig` from request interval, User-Agent, Proxy, and execution directory.
7. Open one `HttpClient` lifecycle for the Job run.
8. Create:
   - `LinkCollectorService`
   - `PostDetailService`
   - `OutputRunLayout`
   - `LocalOutputStore`
   - `LocalCheckpointStore`
9. Call `core.api.run_job(config, ...)`.
10. Print final `JobReport` summary and resume command.
11. Return the mapped exit code.

The CLI must not implement gallery traversal, post parsing, media parsing, worker scheduling, checkpoint ordering, or JSONL path rules itself.

## `wizard` Flow

1. Parse the `wizard` subcommand.
2. Print a numbered menu for:
   - start scraping
   - resume scraping
   - import User-Agent file
   - configure Proxy
   - exit
3. For start scraping, ask the same required source/options that `run` accepts.
4. Convert wizard answers into the same internal command shape used by `build_job_config`.
5. For resume, convert wizard answers into the same internal command shape used by `build_resume_request`.
6. For User-Agent import and Proxy configure, call the same command handlers as command mode.
7. Run through the same runtime assembly and terminal reporting path as command mode.

The wizard is an input convenience layer only. It must not duplicate scraping, parsing, storage, or worker logic.

## `resume` Flow

1. Parse optional `job_id`.
2. Build `ResumeRequest(job_id=...)`.
3. Build the same local dependencies as `run`.
4. Call `core.api.resume_job(request, ...)`.
5. If `job_id` is omitted, the underlying checkpoint store may load the latest checkpoint through the UOW-006 checkpoint contract.
6. Print final summary and resume command.
7. Return the mapped exit code.

## `import-user-agents` Flow

1. Read the source file path from CLI arguments.
2. Validate that the file exists and is readable.
3. Copy it to `<execution_dir>/user-agents.txt`.
4. Preserve plaintext UTF-8 content so users can edit it.
5. Do not validate every User-Agent string in this command; runtime loading already ignores blank lines and falls back safely.

## `configure-proxy` Flow

1. Print a plaintext credential storage warning.
2. Prompt for host, ID, and password or accept explicit command options if provided by the final CLI design.
3. Write `<execution_dir>/.env` with only:
   - `DCINSIDE_PROXY_HOST`
   - `DCINSIDE_PROXY_ID`
   - `DCINSIDE_PROXY_PW`
4. Keep the file editable plaintext by requirement.
5. Do not print the password or raw `.env` content.

## Realtime Environment Flow

Realtime execution is enabled only when `DCINSIDE_REALTIME_ENABLED=true`.

Supported variables:

- `DCINSIDE_REALTIME_MODE=keyword|all`
- `DCINSIDE_REALTIME_KEYWORD`
- `DCINSIDE_REALTIME_DURATION_SECONDS`
- `DCINSIDE_REALTIME_END_AT`
- `DCINSIDE_REALTIME_POLL_INTERVAL_SECONDS`

Rules:

- `keyword` mode requires a keyword.
- `all` mode requires CLI gallery scope options such as `--gallery-type` and `--gallery-id`.
- `keyword` mode may use CLI gallery scope options when the user wants to scope keyword polling to one gallery.
- exactly one of duration seconds or end-at is required.
- both missing or both present is a validation error.
- realtime environment and non-realtime `--source` must not silently combine.

## Terminal Output Flow

Start output includes:

- `job_id`
- output base path
- source summary
- worker count
- request interval
- media and dccon mode

Completion output includes:

- status
- success count
- failure count
- deduped count
- filtered count
- output references when available
- resume command

For errors, CLI first prints an `ErrorMapper`-style safe summary and then prints traceback as confirmed in Q9. The traceback path must still preserve existing redaction boundaries: proxy password, raw `.env`, cookies, raw headers, raw HTML/body/content, and tokens must not be printed as user-facing fields.

## Testable Properties

- CLI import has no side effects.
- Parser accepts all confirmed subcommands.
- `build_job_config` creates the matching `JobConfig.source` variant.
- realtime environment validation preserves the exactly-one termination rule.
- `build_resume_request` accepts explicit and omitted `job_id`.
- `--output-path` maps only to `StorageConfig.base_output_path`.
- User-Agent import writes `user-agents.txt`.
- Proxy configuration writes only documented `.env` keys.
- Wizard answers map to the same model builders as command arguments.
- CLI uses fake runner/dependencies in tests without live network.
- exit codes match success, validation error, and runtime/stopped failure classes.
