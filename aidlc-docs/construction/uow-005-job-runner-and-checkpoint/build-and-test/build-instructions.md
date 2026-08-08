# Build Instructions - UOW-005 Job Runner And Checkpoint

## Prerequisites

- **Build Tool**: Python `pip` with PEP 517 build support
- **Runtime**: Python 3.11+
- **Verified Runtime**: Python 3.13.9
- **Runtime Dependencies**: `anyio>=4,<5`, `beautifulsoup4>=4.12,<5`, `httpx>=0.28,<1`, `pydantic>=2,<3`, `python-dotenv>=1,<2`
- **Test Dependencies**: `pytest>=8,<9`, `hypothesis>=6,<7`
- **Environment Variables**: none required for default build/test path

## Build Steps

### 1. Create A Clean Environment

```powershell
C:\ProgramData\anaconda3\python.exe -m venv .tmp\uow005-build-venv
```

### 2. Install Dependencies

```powershell
& .\.tmp\uow005-build-venv\Scripts\python.exe -m pip install -e ".[test]"
```

### 3. Check Dependencies

```powershell
& .\.tmp\uow005-build-venv\Scripts\python.exe -m pip check
```

### 4. Build Package

```powershell
& .\.tmp\uow005-build-venv\Scripts\python.exe -m pip wheel . --no-deps -w dist
```

### 5. Verify Build Success

- **Expected Output**: a `dcinside_scraper-*.whl` file is created under `dist/`
- **Build Artifact**: `dist/dcinside_scraper-0.1.0-py3-none-any.whl`
- **Build Artifact Size**: 64,771 bytes
- **Build Artifact SHA256**: `847516FC5AF391DD94D6FEFF9D9C35E1E0CD226BFB221D29FF2D3EF2935A127C`

## Troubleshooting

### Runner Tests Fail

- **Cause**: JobRunner orchestration, checkpoint ordering, or fake port contract changed
- **Solution**: run `tests\test_job_runner.py` first, fix the smallest failing runner path, then rerun focused and full suites

### Import Fails

- **Cause**: new runner dependency or package export is missing
- **Solution**: verify `pyproject.toml`, `src\dcinside_scraper\runner\__init__.py`, and root exports
