# Build Instructions - UOW-007 CLI Adapter

## Prerequisites

- **Build Tool**: Python `pip` with PEP 517 build support
- **Runtime**: Python 3.11+
- **Verified Runtime**: Python 3.13.9 clean temporary venv
- **Runtime Dependencies**: `anyio>=4,<5`, `beautifulsoup4>=4.12,<5`, `httpx>=0.28,<1`, `pydantic>=2,<3`, `python-dotenv>=1,<2`
- **Test Dependencies**: `pytest>=8,<9`, `hypothesis>=6,<7`
- **Environment Variables**: none required for default build/test path

## Build Steps

### 1. Create A Clean Environment

```powershell
C:\ProgramData\anaconda3\python.exe -m venv .tmp\uow007-build-venv
```

### 2. Install Dependencies

```powershell
& .\.tmp\uow007-build-venv\Scripts\python.exe -m pip install -e ".[test]"
```

### 3. Build Package

```powershell
& .\.tmp\uow007-build-venv\Scripts\python.exe -m pip wheel . --no-deps -w dist
```

### 4. Verify Build Success

- **Expected Output**: a `dcinside_scraper-*.whl` file is created under `dist/`
- **Build Artifact**: `dist/dcinside_scraper-0.1.0-py3-none-any.whl`
- **Build Artifact Size**: 72,409 bytes
- **Build Artifact SHA256**: `0B661646FC769B25B83CB29BCE4AC9901683E1667DD2B163C8C84654ECF1372D`

## CLI Smoke Checks

```powershell
& .\.tmp\uow007-build-venv\Scripts\dcinside-scraper.exe --help
python main.py --help
$env:PYTHONPATH = "src"; python -m dcinside_scraper.adapters.cli --help
```

All three commands should print the same command list.
