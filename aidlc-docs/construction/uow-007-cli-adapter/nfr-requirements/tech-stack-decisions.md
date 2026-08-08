# Tech Stack Decisions - UOW-007 CLI Adapter

## Runtime And Language

| Decision | Selection | Rationale |
|---|---|---|
| Language | Python 3.11+ | Matches existing package baseline. |
| CLI parser | stdlib `argparse` | Confirmed by Functional Design and Q1. |
| Wizard input | stdlib `input`-style stream reads | Numbered menu does not need a TUI dependency. |
| Password input | stdlib `getpass` | Prevents terminal echo for proxy password. |
| File copy | stdlib `shutil` and `pathlib` | Enough for `user-agents.txt` import. |
| Traceback output | stdlib `traceback` | Confirmed by Q2/Q9, with redaction boundaries. |
| Signal handling | stdlib `signal` plus `JobRunner.request_stop()` | Maps terminal Ctrl+C to UOW-005 manual stop. |

## Dependency Decisions

| Dependency | Selection | Scope |
|---|---|---|
| Click | Not added | `argparse` covers required command mode. |
| Typer | Not added | Adds dependency and typing layer without current need. |
| Rich | Not added | Progress/color UI is out of scope. |
| prompt-toolkit | Not added | Wizard is a simple numbered text menu. |
| Pydantic | existing dependency | Existing `JobConfig`/`ResumeRequest` validation. |
| Hypothesis | existing test extra | Used for pure mapping and redaction PBT. |
| pytest | existing test extra | Used for adapter example tests. |

## CLI UX Strategy

| Area | Decision |
|---|---|
| Command mode | `run`, `resume`, `import-user-agents`, `configure-proxy`, `wizard` |
| Wizard mode | numbered text menu |
| Wizard defaults | show default values where available |
| Invalid wizard input | safe message and retry current prompt |
| Wizard cancel | `q`, back, or empty required input cancellation |
| Stream handling | injectable input/output streams for tests |

## Runtime Strategy

| Area | Decision |
|---|---|
| New Job | build `JobConfig`, assemble local dependencies, call `core.api.run_job()` |
| Resume | build `ResumeRequest`, assemble local dependencies, call `core.api.resume_job()` |
| HTTP lifecycle | async context or `try/finally` close |
| First Ctrl+C | call `JobRunner.request_stop()` |
| Second Ctrl+C | best-effort cleanup and exit code `1` |
| Output layout | delegated to UOW-006 stores |
| Worker orchestration | delegated to UOW-005 runner |

## Configuration File Strategy

| File | Decision |
|---|---|
| `user-agents.txt` | import only readable UTF-8 regular files with at least one non-blank line |
| `.env` | preserve unrelated lines and update only `DCINSIDE_PROXY_*` keys |
| Proxy password | collect with `getpass.getpass()` |
| Proxy warning | print plaintext storage warning before write |
| Environment mutation | do not call `load_dotenv()`; do not mutate `os.environ` for Proxy loading |

## Security Strategy

| Area | Decision |
|---|---|
| Error summary | `ErrorMapper`-style safe summary first |
| Traceback | allowed, but no locals/config/raw details dump |
| Proxy password | never echoed or printed |
| Raw `.env` | never printed |
| Raw HTTP data | cookies, headers, HTML/body/content forbidden in output |
| Command side effects | import/config commands do not start scraper network activity |

## Testing Stack

| Decision | Selection | Rationale |
|---|---|---|
| Example tests | pytest | Existing test runner. |
| PBT | Hypothesis | Existing project choice. |
| CLI runner tests | direct `main(argv)` and helper calls | Avoid shelling out for most tests. |
| Wizard tests | injected input/output streams | No real terminal required. |
| Network tests | excluded from default gate | Keeps tests deterministic. |
| Signal tests | fake runner/handler hooks | Avoid OS-specific signal flakiness. |

Required default test categories:

- import side-effect safety
- command parsing
- command builder mapping
- wizard answer mapping
- realtime env validation
- safe error/traceback output boundary
- exit code mapping
- fake runner invocation
- Ctrl+C graceful stop hook
- User-Agent import file validation
- Proxy `.env` update and password output safety
- pure function PBT

## Deferred Decisions

These are intentionally left for later units or later product work:

- GUI/Web UI
- Rich/progress TUI
- Docker entrypoint UX
- MCP adapter UX
- live DCinside CLI smoke tests as default gate
