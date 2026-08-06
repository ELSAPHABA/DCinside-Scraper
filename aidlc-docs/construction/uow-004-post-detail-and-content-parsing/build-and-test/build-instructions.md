# Build Instructions - UOW-004 Post Detail And Content Parsing

## Prerequisites

- **Build Tool**: Python `pip` with PEP 517 build support
- **Runtime**: Python 3.11+
- **Verified Runtime**: Python 3.13 through `C:\ProgramData\anaconda3\python.exe`
- **Runtime Dependencies**: `pydantic>=2,<3`, `httpx>=0.28,<1`, `python-dotenv>=1,<2`, `beautifulsoup4>=4.12,<5`
- **Test Dependencies**: `pytest>=8,<9`, `hypothesis>=6,<7`
- **Environment Variables**: none required for default build/test path
- **System Requirements**: local Python environment with dependency install access when cache is empty

## Build Steps

### 1. Create A Clean Environment

```powershell
C:\ProgramData\anaconda3\python.exe -m venv .tmp\uow004-build-venv
```

### 2. Install Dependencies

```powershell
& .\.tmp\uow004-build-venv\Scripts\python.exe -m pip install -e ".[test]"
```

### 3. Configure Environment

No runtime environment variables are required for UOW-004 default tests.

Optional live smoke tests may use:

```powershell
$env:DCINSIDE_LIVE_SMOKE_ENABLED = "true"
```

Live smoke is not part of the default gate.

### 4. Build Package

```powershell
& .\.tmp\uow004-build-venv\Scripts\python.exe -m pip wheel . --no-deps -w dist
```

### 5. Verify Build Success

- **Expected Output**: a `dcinside_scraper-*.whl` file is created under `dist/`
- **Build Artifact**: `dist/dcinside_scraper-0.1.0-py3-none-any.whl`
- **Build Artifact Size**: 54,214 bytes
- **Build Artifact SHA256**: `8041F57615CB18513C7E834124381743A101EFBF1E2BD600113B3768DC09B7D0`

## Troubleshooting

### Build Backend Download Fails

- **Cause**: `hatchling` or other build dependencies are not cached and network access is unavailable
- **Solution**: rerun after dependency index access is available

### Tests Fail After Build

- **Cause**: post body, media, repost, or comment parser behavior changed without updating fixtures/properties
- **Solution**: run the smallest failing `pytest` target, fix the affected parser/model, then rerun the full suite
