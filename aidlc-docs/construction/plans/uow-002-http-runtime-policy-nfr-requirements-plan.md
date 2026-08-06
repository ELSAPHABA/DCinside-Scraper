# NFR Requirements 계획 - UOW-002 HTTP Runtime Policy

이 계획은 `UOW-002 HTTP Runtime Policy`의 비기능 요구사항과 기술 선택을 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-002 HTTP Runtime Policy
- **Functional Design**: 승인됨
- **Depends On**: UOW-001 Core Models And Config
- **Primary Stories**: US-002, US-003, US-016
- **Scope**: async HTTP runtime, global request delay, retry/timeout, User-Agent rotation, Proxy resolution, response classification
- **Security Focus**: Proxy secret redaction, raw `.env`/cookie logging 금지, CAPTCHA fail-closed
- **Resiliency Focus**: explicit timeout, retry bounds, resource cleanup, dependency failure isolation
- **PBT Focus**: config normalization, User-Agent rotation, Proxy resolution, retry/classification invariants
- **Out Of Scope**: parser correctness, checkpoint persistence, Garage/PostgreSQL storage, CLI prompt UX, container entrypoint

## NFR Requirements 작업 체크리스트

- [x] UOW-002 Functional Design 승인 확인
- [x] Functional Design 산출물 확인
- [x] Security Baseline 적용 항목 확인
- [x] Resiliency Baseline 적용 항목 확인
- [x] Property-Based Testing 적용 항목 확인
- [x] NFR Requirements 질문 생성
- [x] NFR Requirements 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-002-http-runtime-policy/nfr-requirements/nfr-requirements.md` 생성
- [x] `aidlc-docs/construction/uow-002-http-runtime-policy/nfr-requirements/tech-stack-decisions.md` 생성

## NFR Requirements Questions

### Question 1. Request Throughput And Delay Baseline

UOW-002의 기본 요청 속도 기준은 어떻게 둘까요?

A) (권장) 전역 요청 간격 기본값 1초를 유지하고, 테스트는 limiter가 동시 요청에서도 요청 시작 간격을 지키는지만 검증한다. 실제 초당 처리량 목표는 UOW-003 to UOW-005 통합 후 측정한다.

추천 사유: 지금은 HTTP runtime 단위라 실제 갤러리/게시글 처리량을 정확히 잡기 어렵습니다. 단위 테스트에서는 rate limiter의 불변식만 검증하는 편이 작고 정확합니다.

B) UOW-002에서부터 전체 Job 처리량 목표를 정한다.

C) 요청 간격을 성능 목표에서 제외하고 후속 unit에서만 다룬다.

X) 기타

[Answer]: A

### Question 2. Retry And Backoff Guardrail

retry/backoff 비기능 기준은 어떻게 둘까요?

A) (권장) 기본 최대 3회 시도, bounded exponential backoff, retry 전에도 rate limiter 적용을 요구한다. CAPTCHA/block/unavailable은 retry 금지로 테스트한다.

추천 사유: 무한 재시도와 retry storm을 막고, 차단 의심 응답 반복 요청을 방지할 수 있습니다.

B) retry 횟수와 backoff는 구현자가 나중에 결정한다.

C) 모든 retry 정책은 JobRunner로 미루고 UOW-002에서는 timeout만 둔다.

X) 기타

[Answer]: A

### Question 3. Timeout And Resource Cleanup

timeout과 resource cleanup 요구사항은 어디까지 둘까요?

A) (권장) 모든 외부 HTTP 호출은 명시적 timeout을 가져야 하며, 정상/오류/취소 경로에서 `AsyncClient`가 닫히고 cookie jar가 폐기되는 것을 테스트 요구사항으로 둔다.

추천 사유: UOW-002는 외부 HTTP 경계입니다. timeout과 close 누락은 worker 정체와 resource leak으로 이어집니다.

B) timeout만 요구하고 close/resource cleanup 테스트는 생략한다.

C) httpx 기본 timeout과 context manager 사용만 문서화한다.

X) 기타

[Answer]: A

### Question 4. Proxy Secret Protection

Proxy와 `.env` secret 보호 기준은 어떻게 둘까요?

A) (권장) raw `.env`, proxy password, credential 포함 proxy URL, raw cookie는 로그와 `ErrorResult.details`에 절대 포함하지 않는다. 테스트에서 secret-like 값 redaction을 확인한다.

추천 사유: 기능명세서상 평문 `.env`는 문서화된 보안 예외입니다. 그래서 logging/error boundary에서 강하게 막아야 합니다.

B) password만 숨기고 host/user는 그대로 로그에 남긴다.

C) secret redaction은 UOW-001 `ErrorMapper`에만 맡기고 UOW-002 테스트에서는 다루지 않는다.

X) 기타

[Answer]: A

### Question 5. Observability Scope

UOW-002의 structured logging 요구사항은 어디까지 둘까요?

A) (권장) request start/end, retry, classified failure, proxy enabled state, User-Agent rotation event를 safe structured event로 남긴다. URL은 query를 제거하거나 redacted 형태로만 남긴다.

추천 사유: HTTP 문제 추적에는 stage와 classification 정보가 필요하지만, query/cookie/proxy credential을 남기면 보안 위험이 커집니다.

B) 모든 요청 URL과 header를 debug log에 남긴다.

C) UOW-002에서는 logging을 하지 않고 후속 JobRunner만 logging한다.

X) 기타

[Answer]: A

### Question 6. Tech Stack Dependency Boundary

UOW-002에서 추가할 runtime dependency 범위는 어떻게 둘까요?

A) (권장) runtime dependency는 `httpx`만 추가한다. `.env` 파싱은 간단한 key-value parser를 직접 구현하고, 별도 `python-dotenv`는 1차에서 추가하지 않는다.

추천 사유: `.env` 포맷이 `DCINSIDE_PROXY_*` 3개로 제한됩니다. 새 dependency 없이 충분하며 supply-chain 표면을 줄일 수 있습니다.

B) `httpx`와 `python-dotenv`를 추가한다.

C) `httpx`, `python-dotenv`, 별도 retry/backoff 라이브러리를 추가한다.

X) 기타

[Answer]: B

### Question 7. Property-Based Test Targets

UOW-002에서 PBT 대상으로 삼을 속성은 무엇으로 할까요?

A) (권장) User-Agent rotation invariant, proxy resolution priority, safe header merge, retry classification idempotence, redaction safety를 PBT 대상으로 둔다. 실제 네트워크 I/O는 example/fake transport 테스트로 둔다.

추천 사유: PBT는 순수 정책 로직에 잘 맞습니다. 실제 네트워크 호출을 랜덤 생성하면 flaky test가 되기 쉽습니다.

B) 실제 DCinside live 요청까지 PBT로 수행한다.

C) UOW-002에서는 PBT를 생략한다.

X) 기타

[Answer]: A

### Question 8. Live Smoke Test Policy

DCinside live smoke test는 어떤 기준으로 둘까요?

A) (권장) 기본 unit test와 CI 필수 gate에서는 제외한다. 환경변수로 명시적으로 켠 경우에만 단일 HEAD/GET 수준의 선택적 smoke test를 허용한다.

추천 사유: 외부 사이트 상태와 차단 정책에 따라 테스트가 흔들릴 수 있습니다. 라이브 테스트는 수동/선택 실행 경로로 두는 편이 안정적입니다.

B) 모든 CI에서 live smoke test를 필수로 실행한다.

C) live smoke test 경로를 아예 만들지 않는다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-002 NFR Requirements 산출물 2개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-002 NFR Design으로 넘어가지 않습니다.
