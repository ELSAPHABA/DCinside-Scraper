# Public Contracts - UOW-007 CLI Adapter

## Entrypoints

```powershell
python -m dcinside_scraper.adapters.cli wizard
dcinside-scraper wizard
python main.py wizard
```

All wrappers delegate to:

```python
from dcinside_scraper.adapters.cli import main

exit_code = main(["run", "--source", "direct-post", "--url", "https://gall.dcinside.com/board/view/?id=dcbest&no=1"])
```

Contract:

- importing `dcinside_scraper.adapters.cli` has no runtime side effects
- `main(argv=None) -> int` returns `0`, `1`, or `2`
- root `main.py` is only a compatibility wrapper

## Supported Commands

```powershell
dcinside-scraper run --source direct-post --url "https://gall.dcinside.com/board/view/?id=dcbest&no=1"
dcinside-scraper resume --job-id job-1
dcinside-scraper import-user-agents .\my-agents.txt
dcinside-scraper configure-proxy --host proxy.local:8080 --id user
dcinside-scraper wizard
```

`run --source` supports:

- `direct-post`
- `gallery-search`
- `integrated-search`
- `deep-search`
- `no-keyword-range`

Realtime scraping is enabled through `DCINSIDE_REALTIME_ENABLED=true` and builds `realtime_keyword` or `realtime_all` sources without a non-realtime `--source`.

## Model Builders

```python
from dcinside_scraper.adapters.cli import build_job_config, build_resume_request

job = build_job_config({"source": "gallery-search", "gallery_type": "minor", "gallery_id": "singlebungle1472", "keyword": "test"})
request = build_resume_request({"job_id": "job-1"})
```

Contract:

- returns validated UOW-001 Pydantic models
- does not pass raw `argparse.Namespace` into the runner
- validation failures are surfaced as `ValidationFailure` or Pydantic `ValidationError`

## Runtime Execution Helpers

```python
from dcinside_scraper.adapters.cli import run_scrape_command_async, resume_scrape_command_async

await run_scrape_command_async(command)
await resume_scrape_command_async(command)
```

Contract:

- creates `HttpClient`, `LinkCollectorService`, `PostDetailService`, `LocalOutputStore`, `LocalFailureStore`, `LocalCheckpointStore`, and `JobRunner`
- calls `core.api.run_job()` or `core.api.resume_job()`
- supports fake runner injection for tests
- does not implement search pagination, post parsing, worker queue logic, or output layout rules

Runtime scrape options:

- `--max-post-retries N` maps to `ScrapeOptions.max_post_retries=N`
- the local `HttpClient` uses `RetryPolicy.max_attempts=N + 1`

## User-Agent Import

```python
from dcinside_scraper.adapters.cli import import_user_agents

import_user_agents("source.txt", "user-agents.txt")
```

Contract:

- source must be a regular UTF-8 text file
- all-blank files are rejected
- destination is written through temp-file replace
- command mode writes to `<cwd>/user-agents.txt`

## Proxy Env Update

```python
from dcinside_scraper.adapters.cli import update_proxy_env

update_proxy_env(".env", {
    "DCINSIDE_PROXY_HOST": "proxy.local:8080",
    "DCINSIDE_PROXY_ID": "user",
    "DCINSIDE_PROXY_PW": "password",
})
```

Contract:

- updates only `DCINSIDE_PROXY_HOST`, `DCINSIDE_PROXY_ID`, and `DCINSIDE_PROXY_PW`
- preserves unrelated `.env` lines
- removes stale duplicate proxy keys
- writes plaintext by explicit product requirement
- does not call `load_dotenv()` or mutate process environment

## Wizard

```python
from dcinside_scraper.adapters.cli import WizardSession

command = WizardSession(input_stream, output_stream).collect_command()
```

Contract:

- presents a numbered menu
- returns the same internal command dict shape used by command mode
- does not scrape, parse HTML, write JSONL, or own separate validation logic

## Error And Interrupt Boundaries

```python
from dcinside_scraper.adapters.cli import InterruptController, print_error
```

Contract:

- first Ctrl+C calls `JobRunner.request_stop()`
- second Ctrl+C raises `KeyboardInterrupt`
- `print_error()` prints a safe `ErrorMapper` summary before a traceback
- traceback output avoids locals/config dumps and uses the mapped safe message

## Boundaries

UOW-007 does not:

- implement parser selectors
- implement BeautifulSoup scraping logic
- implement Docker entrypoints
- implement Garage/PostgreSQL provisioning
- implement MCP tools
- implement GUI/Web UI
