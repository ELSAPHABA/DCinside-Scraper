# Build Instructions - UOW-002 HTTP Runtime Policy

## Prerequisites

- **Build Tool**: Python `pip` with PEP 517 build support
- **Runtime**: Python 3.11+
- **Runtime Dependencies**: `pydantic>=2,<3`, `httpx>=0.28,<1`, `python-dotenv>=1,<2`
- **Test Dependencies**: `pytest>=8,<9`, `hypothesis>=6,<7`
- **Lock File**: `requirements.lock`
- **Environment Variables**: none required for default build/test path
- **System Requirements**: local Python environment with dependency install access when cache is empty

## Build Steps

### 1. Install Dependencies

```bash
python -m pip install -e ".[test]"
```

For locked installs in a clean environment:

```bash
python -m pip install -r requirements.lock
python -m pip install -e .
```

### 2. Configure Environment

No runtime environment variables are required for UOW-002 default tests.

Optional live smoke tests may use:

```bash
DCINSIDE_LIVE_SMOKE_ENABLED=true
```

Live smoke is not part of the default gate.

### 3. Build Package

```bash
python -m pip wheel . --no-deps -w dist
```

### 4. Verify Build Success

- **Expected Output**: a `dcinside_scraper-*.whl` file is created under `dist/`
- **Build Artifact**: `dist/dcinside_scraper-0.1.0-py3-none-any.whl`
- **Common Warnings**: pip may use an isolated build environment for `hatchling`

## Troubleshooting

### Build Fails with Dependency Errors

- **Cause**: missing build backend or dependency download failure
- **Solution**: rerun `python -m pip install -e ".[test]"`, then rerun the wheel command

### Tests Fail After Build

- **Cause**: HTTP runtime policy changed without updating fake transport tests or PBT strategies
- **Solution**: run `python -m pytest -q`, fix the smallest affected runtime component, then rebuild
