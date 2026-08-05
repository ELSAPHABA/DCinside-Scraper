# Build Instructions

## Prerequisites

- **Build Tool**: Python `pip` with PEP 517 build support
- **Runtime**: Python 3.11+
- **Dependencies**: `pydantic>=2,<3`
- **Test Dependencies**: `pytest>=8,<9`, `hypothesis>=6,<7`
- **Lock File**: `requirements.lock`
- **Environment Variables**: none required for UOW-001
- **System Requirements**: local Python environment with network access for dependency install when cache is empty

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

No runtime environment variables are required for UOW-001.

### 3. Build UOW-001 Package

```bash
python -m pip wheel . --no-deps -w dist
```

### 4. Verify Build Success

- **Expected Output**: a `dcinside_scraper-*.whl` file is created under `dist/`
- **Build Artifacts**: `dist/dcinside_scraper-0.1.0-py3-none-any.whl`
- **Common Warnings**: pip may use an isolated build environment for `hatchling`

## Troubleshooting

### Build Fails with Dependency Errors

- **Cause**: missing build backend or dependency download failure
- **Solution**: rerun `python -m pip install -e ".[test]"`, then rerun the wheel command

### Build Fails with Validation or Import Errors

- **Cause**: source package contract changed without updating tests
- **Solution**: run `python -m pytest -q`, fix the failing contract, then rebuild

