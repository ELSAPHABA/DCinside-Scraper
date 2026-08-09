# Build Instructions - UOW-008 Container, MCP, And Test Harness

## Prerequisites

- **Build Tool**: Python `pip` with PEP 517 build support
- **Runtime**: Python 3.11+
- **Verified Runtime**: clean temporary venv at `.tmp\uow008-build-venv`
- **Default Runtime Dependencies**: `anyio`, `beautifulsoup4`, `httpx`, `pydantic`, `python-dotenv`
- **Test Dependencies**: `pytest`, `hypothesis`
- **Optional Extras**: `s3`, `postgres`, `mcp`, `analysis`
- **Environment Variables**: none required for the default build/test path

## Build Steps

### 1. Create A Clean Environment

```powershell
python -m venv .tmp\uow008-build-venv
```

### 2. Install Default Test Dependencies

```powershell
& .\.tmp\uow008-build-venv\Scripts\python.exe -m pip install -e ".[test]"
```

### 3. Verify Dependencies

```powershell
& .\.tmp\uow008-build-venv\Scripts\python.exe -m pip check
```

Observed result:

```text
No broken requirements found.
```

### 4. Build Package Wheel

```powershell
& .\.tmp\uow008-build-venv\Scripts\python.exe -m pip wheel . --no-deps -w dist
```

Observed artifact:

- **Build Artifact**: `dist/dcinside_scraper-0.1.0-py3-none-any.whl`
- **Build Artifact Size**: 80,639 bytes
- **Build Artifact SHA256**: `AEF0A3970D85F30465556C448834DE63FA18FB60E9888C2C0DAAB573C957AC04`

## Container Artifact

`Dockerfile` is present for worker image builds.

Docker was available:

```text
Docker version 29.6.2, build dfc4efb
```

Docker image build was not part of the default gate because it may require base-image pull/network access. Docker build remains an optional smoke check.
