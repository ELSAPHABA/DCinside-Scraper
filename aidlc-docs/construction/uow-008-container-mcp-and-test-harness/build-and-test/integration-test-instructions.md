# Integration Test Instructions - UOW-008 Container, MCP, And Test Harness

## Default Integration-Like Coverage

The default gate uses deterministic fakes instead of external services.

Covered by default tests:

- container `run` command builds S3/PostgreSQL storage config without network
- container `RESUME=true` maps `JOB_ID` into `ResumeRequest`
- S3 output store uploads JSONL/report/media through an injected fake S3 client
- PostgreSQL checkpoint store saves, loads, and loads latest through fake connection/cursor objects
- MCP handlers return JSON-serializable success/error payloads without starting an MCP server
- quality fixtures validate JSONL/report shape and repost title normalization

Command:

```powershell
& .\.tmp\uow008-build-venv\Scripts\python.exe -m pytest tests\test_container_adapter.py tests\test_s3_output_and_postgres.py tests\test_mcp_adapter.py tests\test_quality_harness.py -q -p no:cacheprovider --basetemp .tmp\pytest-uow008-focused-build
```

Observed result:

```text
12 passed, 1 skipped in 6.93s
```

## Optional Smoke Tests

Optional smoke checks are not part of the default gate.

| Marker | External Dependency |
|---|---|
| `docker` | Docker image build/start |
| `garage` | Garage/S3-compatible endpoint |
| `postgres` | PostgreSQL endpoint |
| `mcp` | MCP runtime extra/server |
| `live` | live DCinside network |

Run optional smoke only when the relevant service and env are explicitly configured.

Example:

```powershell
& .\.tmp\uow008-build-venv\Scripts\python.exe -m pytest -m "docker or garage or postgres or mcp" -q
```

No optional smoke was executed in this Build and Test pass.
