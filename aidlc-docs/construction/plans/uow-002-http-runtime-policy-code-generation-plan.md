# Code Generation Plan - UOW-002 HTTP Runtime Policy

이 문서는 `UOW-002 HTTP Runtime Policy` 코드 생성을 위한 단일 기준 계획입니다. 이번 요청에서 계획 생성과 코드 생성을 함께 완료했습니다.

## Unit Context

- **Unit**: UOW-002 HTTP Runtime Policy
- **Project Type**: Greenfield Python package
- **Workspace Root**: `D:\HongDev\ELSAPHABA\DCinside-Scraper`
- **Code Location**: workspace root의 `src/`, `tests/`, `pyproject.toml`
- **Documentation Location**: `aidlc-docs/construction/uow-002-http-runtime-policy/code/`
- **Primary Stories**: US-002, US-003, US-016, US-017
- **Supporting Role**: UOW-003 to UOW-008이 공유할 async HTTP runtime policy 제공

## Dependencies

| Dependency | Status |
|---|---|
| Prior unit dependency | UOW-001 approved and implemented |
| Functional Design | Approved |
| NFR Requirements | Approved |
| NFR Design | Approved |
| Infrastructure Design | Approved |

## Scope

UOW-002 implements:

- `httpx.AsyncClient` 기반 async HTTP client
- explicit timeout config
- per-client request rate limiter
- retry and bounded backoff
- User-Agent file loading and rotation
- in-memory cookie clear on User-Agent rotation
- Proxy resolution from explicit option or `.env`
- `python-dotenv` based runtime-only `.env` loading
- `trust_env=False`
- response classification before parsing
- safe HTTP event builder
- fake transport, fake time, and property-based tests

UOW-002 does not implement:

- search URL construction
- `search_pos` traversal
- post/comment/media HTML parsing
- JSONL/media/checkpoint storage
- CLI terminal prompts or file creation
- container entrypoint
- Docker, Terraform, queue, Garage, PostgreSQL, or monitoring infrastructure

## Expected Interfaces And Contracts

| Contract | Target Path |
|---|---|
| Runtime dependencies | `pyproject.toml` |
| Public HTTP package exports | `src/dcinside_scraper/http/__init__.py` |
| HTTP runtime implementation | `src/dcinside_scraper/http/runtime.py` |
| Top-level convenience exports | `src/dcinside_scraper/__init__.py` |
| HTTP runtime example tests | `tests/test_http_runtime.py` |
| HTTP runtime PBT tests | `tests/test_http_properties.py` |
| HTTP PBT strategies | `tests/strategies/http_runtime.py` |
| Public contract documentation | `aidlc-docs/construction/uow-002-http-runtime-policy/code/public-contracts.md` |
| Code generation summary | `aidlc-docs/construction/uow-002-http-runtime-policy/code/code-generation-summary.md` |

## Database Entities

No database entities or migration scripts are owned by UOW-002.

## Step Sequence

### Step 1. Dependency Update

- [x] Add `httpx>=0.28,<1`.
- [x] Add `python-dotenv>=1,<2`.
- [x] Do not add `requests`, retry/backoff library, scraping framework, or browser automation dependency.

### Step 2. HTTP Runtime Package

- [x] Create `src/dcinside_scraper/http/`.
- [x] Create import-safe public exports.
- [x] Avoid reading `.env` or `user-agents.txt` at package import.

### Step 3. Runtime Config And Providers

- [x] Implement `TimeoutConfig`.
- [x] Implement `RetryPolicy`.
- [x] Implement `HttpRuntimeConfig`.
- [x] Implement `UserAgentConfig` and `UserAgentProvider`.
- [x] Implement `ProxyConfig`, `DotenvProxyLoader`, and `ProxyProvider`.

### Step 4. Request Policy Components

- [x] Implement `RequestRateLimiter`.
- [x] Implement `BackoffCalculator`.
- [x] Implement `HeaderBuilder`.
- [x] Implement `ResponseClassifier`.
- [x] Implement `SafeHttpEventBuilder`.

### Step 5. HttpClient

- [x] Implement `HttpClient`.
- [x] Support `get`, `post`, `download`, and generic `request`.
- [x] Apply limiter before first attempts and retries.
- [x] Retry only network/timeout/429/5xx conditions.
- [x] Fail closed on CAPTCHA/block/unavailable classification.
- [x] Close underlying client on final error, cancellation, and async context exit.
- [x] Clear in-memory cookies on User-Agent rotation.

### Step 6. Testing

- [x] Add example tests for `.env` proxy loading, proxy priority, User-Agent cookie clear, retry/limiter, CAPTCHA no retry, cancellation cleanup, and safe event redaction.
- [x] Add PBT tests for header merge, User-Agent rotation, proxy safe label, classification idempotence, and secret redaction.
- [x] Keep all live DCinside network tests out of default test path.

### Step 7. Documentation

- [x] Generate public contract documentation.
- [x] Generate code generation summary.
- [x] Record no deployment artifacts for this unit.

## Story Traceability

| Story | Coverage In This Unit |
|---|---|
| US-002 | request delay, retry, timeout, response classification foundation |
| US-003 | proxy and User-Agent runtime policy foundation |
| US-016 | CAPTCHA/block fail-closed typed exceptions |
| US-017 | import-safe HTTP runtime library API |

## Completion Criteria

- [x] UOW-002 source files exist under `src/dcinside_scraper/http/`.
- [x] Tests for UOW-002 runtime behavior exist under `tests/`.
- [x] Documentation summary exists under `aidlc-docs/construction/uow-002-http-runtime-policy/code/`.
- [x] No runtime infrastructure artifact is created for UOW-002.
- [x] `python -m pytest -q` passes.
