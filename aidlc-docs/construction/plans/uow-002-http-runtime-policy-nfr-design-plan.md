# NFR Design 계획 - UOW-002 HTTP Runtime Policy

이 계획은 `UOW-002 HTTP Runtime Policy`의 NFR 요구사항을 구현 패턴과 논리 컴포넌트로 구체화하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-002 HTTP Runtime Policy
- **NFR Requirements**: 승인됨
- **Depends On**: UOW-001 Core Models And Config
- **Scope**: async HTTP client lifecycle, limiter, retry/backoff, timeout, proxy `.env`, User-Agent rotation, response classification, safe observability, tests
- **Out Of Scope**: search traversal, post/comment/media parsing, checkpoint persistence, CLI prompt UX, container entrypoint

## NFR Design 작업 체크리스트

- [x] UOW-002 NFR Requirements 승인 확인
- [x] NFR Requirements 산출물 확인
- [x] NFR Design 질문 생성
- [x] NFR Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-002-http-runtime-policy/nfr-design/nfr-design-patterns.md` 생성
- [x] `aidlc-docs/construction/uow-002-http-runtime-policy/nfr-design/logical-components.md` 생성
- [x] Security/Resiliency/PBT compliance 확인

## NFR Design Questions

### Question 1. Rate Limiter Pattern

전역 요청 간격 limiter는 어떻게 설계할까요?

A) (권장) `HttpClient` 인스턴스마다 하나의 `RequestRateLimiter`를 두고, `asyncio.Lock`과 monotonic clock으로 요청 시작 시각 간격만 직렬화한다.

추천 사유: 전역 간격 보장에 필요한 최소 구조입니다. 동시 worker가 같은 client를 공유해도 interval 불변식을 테스트하기 쉽습니다.

B) Job 전체에 하나의 프로세스 전역 limiter singleton을 둔다.

C) 각 요청 함수에서 개별적으로 `asyncio.sleep()`을 호출한다.

X) 기타

[Answer]: A

### Question 2. Retry And Backoff Pattern

retry/backoff는 어디에 배치할까요?

A) (권장) `HttpClient.request()` 내부의 작은 retry loop로 구현하고, `RetryPolicy`가 max attempts, retryable status, backoff 상한만 제공한다.

추천 사유: retry는 transport 정책입니다. 별도 retry framework 없이도 요구사항을 만족하며, 모든 재시도가 limiter를 지나도록 강제할 수 있습니다.

B) 별도 `RetryExecutor` 클래스로 모든 request 실행을 감싼다.

C) retry는 후속 JobRunner에서만 처리하고 `HttpClient`는 단일 요청만 수행한다.

X) 기타

[Answer]: A

### Question 3. Sleep And Clock Injection

limiter/backoff 테스트를 위해 시간 의존성은 어떻게 주입할까요?

A) (권장) production 기본값은 `time.monotonic`과 `asyncio.sleep`을 쓰고, 테스트에서만 clock/sleeper callable을 주입한다.

추천 사유: 실제 구현은 단순하게 두면서 느린 sleep 없는 단위 테스트와 PBT가 가능합니다.

B) 모든 시간 처리를 UOW-001 `ClockPort` 구현체로 강제한다.

C) 실제 `asyncio.sleep`만 사용하고 테스트도 실제 시간을 기다린다.

X) 기타

[Answer]: A

### Question 4. `python-dotenv` Usage Pattern

Q6에서 선택한 `python-dotenv`는 어떻게 사용할까요?

A) (권장) runtime creation 시점에 `dotenv_values(path)`로 지정 `.env`만 읽고, `DCINSIDE_PROXY_*` allowlist만 추출한다. process environment는 변경하지 않는다.

추천 사유: 사용자가 선택한 dependency를 쓰면서도 import side effect와 환경 오염을 피할 수 있습니다.

B) `load_dotenv()`로 process environment에 주입한 뒤 `os.environ`에서 읽는다.

C) `python-dotenv`를 dependency로 추가하지만 실제 파싱은 직접 구현한다.

X) 기타

[Answer]: A

### Question 5. User-Agent Rotation And Cookie Reset

User-Agent 교체와 cookie reset은 어떻게 연결할까요?

A) (권장) `UserAgentProvider.next_for_request()`가 `(user_agent, changed)`를 반환하고, `HttpClient`가 `changed=True`일 때 request 전 cookie jar를 clear한다.

추천 사유: provider는 rotation만 알고, cookie lifecycle은 client가 소유합니다. 책임이 작고 테스트도 단순합니다.

B) `UserAgentProvider`가 `httpx.AsyncClient`를 직접 받아 cookie까지 삭제한다.

C) User-Agent는 변경하지만 cookie reset은 후속 parser에서 처리한다.

X) 기타

[Answer]: A

### Question 6. Response Classification Pattern

CAPTCHA/block/unavailable/retryable 분류는 어떻게 설계할까요?

A) (권장) `ResponseClassifier`가 status code, final URL, content-type, 제한된 body sample 문자열만 받아 `ResponseClassification` enum/value object를 반환한다.

추천 사유: parser 이전 단계에서 필요한 최소 정보만 사용합니다. 전체 HTML 파싱이나 BeautifulSoup 의존성을 runtime 정책에 넣지 않아도 됩니다.

B) `ResponseClassifier`가 BeautifulSoup으로 HTML 구조까지 파싱한다.

C) 각 caller가 response body를 보고 직접 예외를 결정한다.

X) 기타

[Answer]: A

### Question 7. Safe Logging Pattern

HTTP runtime 로그는 어디에서 sanitizing할까요?

A) (권장) `SafeHttpEventBuilder` helper가 URL query 제거, proxy label redaction, header/body 제외를 처리하고 UOW-001 `LoggerPort`로 safe dict만 전달한다.

추천 사유: logging 호출마다 redaction을 반복하지 않고, 금지 필드를 한 경계에서 막을 수 있습니다.

B) 각 logging call site에서 직접 문자열을 조립하며 민감값을 제외한다.

C) debug 모드에서는 raw URL/header/body를 그대로 남긴다.

X) 기타

[Answer]: A

### Question 8. Test Design Pattern

UOW-002 테스트 구조는 어떻게 둘까요?

A) (권장) `httpx.MockTransport` 또는 작은 fake transport, fake clock/sleeper, `tests/strategies/`의 Hypothesis strategy를 사용한다. live smoke는 `DCINSIDE_LIVE_SMOKE_ENABLED=true`에서만 별도 marker로 실행한다.

추천 사유: unit test와 PBT는 빠르고 결정적으로 유지하고, 실제 DCinside 네트워크 의존성은 명시적 선택 실행으로 분리할 수 있습니다.

B) 모든 HTTP 테스트를 실제 DCinside live 요청으로 검증한다.

C) retry/limiter/classifier는 문서만 두고 테스트하지 않는다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-002 NFR Design 산출물 2개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 Infrastructure Design 또는 Code Generation으로 넘어가지 않습니다.
