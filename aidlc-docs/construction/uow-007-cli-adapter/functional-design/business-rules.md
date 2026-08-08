# Business Rules - UOW-007 CLI Adapter

## Entrypoint Rules

- CLI entrypoint must be `dcinside_scraper.adapters.cli.main(argv: list[str] | None = None) -> int`.
- The package console script must call `main`.
- Importing `dcinside_scraper.adapters.cli` must not execute a scrape.
- Importing the CLI module must not prompt the terminal.
- Importing the CLI module must not read `.env` or `user-agents.txt`.
- Importing the CLI module must not create output files.
- Importing the CLI module must not perform network requests.

## Command Rules

- CLI uses stdlib `argparse`.
- Supported subcommands are `run`, `resume`, `import-user-agents`, `configure-proxy`, and `wizard`.
- `run` must support `--source direct-post`.
- `run` must support `--source gallery-search`.
- `run` must support `--source integrated-search`.
- `run` must support `--source deep-search`.
- `run` must support `--source no-keyword-range`.
- Interactive numbered wizard/menu execution is included in first implementation scope.
- Wizard execution must call the same model-building and core API functions as the command CLI.

## Model Mapping Rules

- CLI must build `JobConfig` through shared Pydantic model validation.
- CLI must build `ResumeRequest` through shared Pydantic model validation.
- CLI must not pass raw `argparse.Namespace` into `JobRunner`.
- CLI must not duplicate source validation already owned by UOW-001 models.
- CLI may assemble plain dictionaries only as temporary inputs to model constructors.
- Validation errors return exit code `2`.

## Runtime Assembly Rules

- CLI creates the local runtime dependencies for local execution.
- CLI uses `HttpClient` for all HTTP I/O.
- CLI uses `LinkCollectorService` for link collection.
- CLI uses `PostDetailService` for post and comment detail collection.
- CLI uses `LocalOutputStore` for local output writes.
- CLI uses `LocalCheckpointStore` for local checkpoint reads and writes.
- CLI calls `core.api.run_job()` for new Jobs.
- CLI calls `core.api.resume_job()` for resume.
- CLI must not implement search pagination.
- CLI must not implement post parsing.
- CLI must not implement worker queue scheduling.
- CLI must not update checkpoints directly except through injected checkpoint store calls made by the runner.

## Output And Checkpoint Rules

- `--output-path` maps to `StorageConfig.base_output_path`.
- Missing `--output-path` leaves `StorageConfig.base_output_path` as `None`.
- When base output path is `None`, UOW-006 local layout uses the current working directory.
- CLI must not reimplement `outputs/<job_id>/<run_id>/...` path rules.
- CLI must not append to old resume JSONL files directly.
- Resume command output must include enough information for the user to run `resume` again.

## Realtime Rules

- Realtime scraping is enabled only by `DCINSIDE_REALTIME_ENABLED=true`.
- `DCINSIDE_REALTIME_MODE` must be `keyword` or `all`.
- `keyword` mode requires `DCINSIDE_REALTIME_KEYWORD`.
- `all` mode requires CLI gallery scope options such as `--gallery-type` and `--gallery-id`.
- `keyword` mode may accept CLI gallery scope options for one-gallery keyword polling.
- `DCINSIDE_REALTIME_DURATION_SECONDS` and `DCINSIDE_REALTIME_END_AT` are mutually exclusive.
- Exactly one realtime termination condition is required.
- Realtime environment and a non-realtime `run --source` selection must not silently merge into one Job.
- Realtime option validation errors return exit code `2`.

## Wizard Rules

- `wizard` must present a numbered terminal menu.
- `wizard` must support starting a scrape.
- `wizard` must support resuming a scrape.
- `wizard` must support importing a User-Agent file.
- `wizard` must support configuring Proxy.
- `wizard` must support exiting without side effects.
- Wizard answers must be converted to the same internal command shape used by command-line arguments.
- Wizard mode must use the same `JobConfig` and `ResumeRequest` validation as command mode.
- Wizard mode must not implement scraping logic directly.
- Wizard mode must not hide validation errors; it must show safe messages and allow correction or exit.

## User-Agent Rules

- `--user-agent-file` applies only to the current run unless imported separately.
- `--user-agent-rotate-every` maps to `UserAgentConfig.rotation_interval_requests`.
- Missing User-Agent file must fall back through UOW-002 runtime rules.
- `import-user-agents` copies the selected file to `user-agents.txt` in the execution directory.
- `user-agents.txt` remains plaintext and user-editable.
- User-Agent import must not start a scrape.

## Proxy Rules

- Explicit CLI proxy values win over `.env`.
- If explicit proxy values are not supplied, `.env` can be used automatically.
- If neither explicit proxy values nor valid `.env` values exist, Proxy is disabled.
- `configure-proxy` writes plaintext `.env` only after warning the user.
- `.env` may contain only documented Proxy keys for this flow.
- CLI must not print Proxy password.
- CLI must not print raw `.env` content.
- CLI must not call `load_dotenv()` or mutate process environment for Proxy loading.

## Scrape Option Rules

- `--image-mode` maps to `ScrapeOptions.image_mode`.
- `--dccon-mode` maps to `ScrapeOptions.dccon_mode`.
- `--include-comments` and `--no-comments` map to `ScrapeOptions.include_comments`.
- `--request-interval-seconds` maps to both HTTP runtime request delay and scrape option request interval where applicable.
- `--post-worker-count` maps to `WorkerConfig.post_worker_count`.
- `--queue-max-size` maps to `WorkerConfig.queue_max_size`.
- `--max-comment-pages` maps to `ScrapeOptions.max_comment_pages`.
- Existing model validation decides invalid values such as worker count less than 1.

## Terminal Output Rules

- Start output must include `job_id`.
- Start output must include source summary.
- Start output must include output path.
- Start output must include worker count.
- Start output must include request interval.
- Final output must include report status.
- Final output must include success and failure counts.
- Final output must include resume command.
- Success returns exit code `0`.
- Stopped, CAPTCHA, blocked, storage, network, parse, and unexpected runtime failures return exit code `1`.
- Validation failures return exit code `2`.
- CLI prints traceback as confirmed by Q9.
- CLI must print a safe mapped error summary before traceback.
- Traceback output must not include proxy password, raw `.env`, cookies, raw headers, raw HTML/body/content, or tokens as user-facing details.

## Test Rules

- Default tests must not perform live DCinside network requests.
- Tests must cover parser construction and subcommand parsing.
- Tests must cover `build_job_config`.
- Tests must cover `build_resume_request`.
- Tests must cover realtime environment validation.
- Tests must cover User-Agent import copy behavior.
- Tests must cover Proxy `.env` writing without password leakage in output.
- Tests must cover import side-effect safety.
- Tests must cover fake-runner execution path.

## Out Of Scope Rules

- UOW-007 does not implement parser selectors.
- UOW-007 does not implement BeautifulSoup scraping logic.
- UOW-007 does not implement Garage provisioning.
- UOW-007 does not implement PostgreSQL checkpoint adapter.
- UOW-007 does not implement Docker entrypoint behavior.
- UOW-007 does not implement MCP tools.
- UOW-007 does not implement GUI/Web UI.
