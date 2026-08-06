# Build Instructions - UOW-003 Search And Link Collection

## Prerequisites

- **Build Tool**: Python `pip` with PEP 517 build support
- **Runtime**: Python 3.11+
- **Verified Runtime**: Python 3.12 through `py -3.12`
- **Runtime Dependencies**: `pydantic>=2,<3`, `httpx>=0.28,<1`, `python-dotenv>=1,<2`, `beautifulsoup4>=4.12,<5`
- **Test Dependencies**: `pytest>=8,<9`, `hypothesis>=6,<7`
- **Environment Variables**: none required for default build/test path
- **System Requirements**: local Python environment with dependency install access when cache is empty

## Build Steps

### 1. Create A Clean Environment

```powershell
py -3.12 -m venv $env:TEMP\dcinside_scraper_uow003_<unique>
& $env:TEMP\dcinside_scraper_uow003_<unique>\Scripts\python.exe -m pip install --upgrade pip
```

### 2. Install Dependencies

```powershell
& $env:TEMP\dcinside_scraper_uow003_<unique>\Scripts\python.exe -m pip install -e ".[test]"
```

### 3. Configure Environment

No runtime environment variables are required for UOW-003 default tests.

Optional live smoke tests may use:

```powershell
$env:DCINSIDE_LIVE_SMOKE_ENABLED = "true"
```

Live smoke is not part of the default gate.

### 4. Build Package

```powershell
& $env:TEMP\dcinside_scraper_uow003_<unique>\Scripts\python.exe -m pip wheel . --no-deps -w dist
```

### 5. Verify Build Success

- **Expected Output**: a `dcinside_scraper-*.whl` file is created under `dist/`
- **Build Artifact**: `dist/dcinside_scraper-0.1.0-py3-none-any.whl`
- **Common Warnings**: pip may use an isolated build environment for `hatchling`

## Troubleshooting

### Build Fails With Python Version Error

- **Cause**: default `python` may point to Python 3.10 or older
- **Solution**: use `py -3.12` or another Python 3.11+ interpreter

### Tests Fail After Build

- **Cause**: search collector/parser behavior changed without updating fixture tests or PBT strategies
- **Solution**: run the smallest failing `pytest` target, fix the affected parser/policy component, then rerun the full suite
