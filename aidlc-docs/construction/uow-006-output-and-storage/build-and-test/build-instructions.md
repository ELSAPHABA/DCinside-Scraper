# Build Instructions - UOW-006 Output And Storage

## Prerequisites

- **Build Tool**: Python `pip` with PEP 517 build support
- **Runtime**: Python 3.11+
- **Verified Runtime**: Python 3.13.9
- **Runtime Dependencies**: `beautifulsoup4>=4.12,<5`, `httpx>=0.28,<1`, `pydantic>=2,<3`, `python-dotenv>=1,<2`
- **Optional S3 Dependency**: `boto3>=1.34,<2` through the `s3` extra
- **Test Dependencies**: `pytest>=8,<9`, `hypothesis>=6,<7`
- **Environment Variables**: none required for default build/test path

## Build Steps

### 1. Create A Clean Environment

```powershell
python -m venv .tmp\uow006-build-venv
```

### 2. Install Dependencies

```powershell
& .\.tmp\uow006-build-venv\Scripts\python.exe -m pip install -e ".[test]"
```

### 3. Configure Environment

No runtime environment variables are required for UOW-006 default tests.

Optional S3/Garage smoke tests may use:

```powershell
$env:DCINSIDE_S3_SMOKE_ENABLED = "true"
```

Smoke tests are not part of the default gate.

### 4. Build Package

```powershell
& .\.tmp\uow006-build-venv\Scripts\python.exe -m pip wheel . --no-deps -w dist
```

### 5. Verify Build Success

- **Expected Output**: a `dcinside_scraper-*.whl` file is created under `dist/`
- **Build Artifact**: `dist/dcinside_scraper-0.1.0-py3-none-any.whl`
- **Build Artifact Size**: 59,462 bytes
- **Build Artifact SHA256**: `A3573E34332D91399A75095EB2E5E9932C849C72676DF0C700354A0071F3EC3B`

## Troubleshooting

### S3 Mode Fails With Missing Dependency

- **Cause**: `boto3` is not installed because `s3` extra was not selected
- **Solution**: install with `.[s3]` or `.[test,s3]` when S3-compatible output is needed

### Tests Fail After Build

- **Cause**: storage pathing, JSONL serialization, redaction, checkpoint, or S3 key behavior changed
- **Solution**: run the smallest failing `pytest` target, fix the affected storage component, then rerun focused and full suites
