# Build Instructions - UOW-009 Parser Failure Retry Reprocessor

## Runtime

Use Python 3.11+.

Verified runtime:

```text
Python 3.12 temporary venv at .tmp\uow009-build-venv312
```

## Setup

```text
py -3.12 -m venv .tmp\uow009-build-venv312
.\.tmp\uow009-build-venv312\Scripts\python.exe -m pip install -e ".[test]"
```

## Dependency Check

```text
.\.tmp\uow009-build-venv312\Scripts\python.exe -m pip check
```

Expected:

```text
No broken requirements found.
```

## Wheel Build

```text
.\.tmp\uow009-build-venv312\Scripts\python.exe -m pip wheel . --no-deps -w dist
```

Expected artifact:

```text
dist\dcinside_scraper-0.1.0-py3-none-any.whl
```

## Compile Check

```text
.\.tmp\uow009-build-venv312\Scripts\python.exe -m compileall -q src\dcinside_scraper
```
