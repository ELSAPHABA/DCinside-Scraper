# Functional Design 계획 - UOW-002 HTTP Runtime Policy

이 계획은 `UOW-002 HTTP Runtime Policy`의 기능 설계를 만들기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-002 HTTP Runtime Policy
- **Depends On**: UOW-001 Core Models And Config
- **Primary Stories**: US-002 User-Agent와 Proxy 설정을 불러온다, US-003 요청 속도와 worker 수를 조절한다, US-016 실패한 게시글 요청을 재시도하고 실패 기록을 남긴다
- **Used By**: UOW-003 Search And Link Collection, UOW-004 Post Detail And Content Parsing, UOW-005 Job Runner And Checkpoint
- **Scope**: HTTP client wrapper, request delay, retry, timeout, User-Agent rotation, Proxy resolution, CAPTCHA/block response classification
- **Out Of Scope**: HTML parsing, search URL construction, post/comment parsing, output storage, checkpoint write ordering, CLI prompt UI, container entrypoint

## Functional Design 작업 체크리스트

- [x] UOW-001 completion and approval 확인
- [x] UOW-002 unit definition 확인
- [x] UOW-002 assigned stories 확인
- [x] RuntimePolicyService high-level design 확인
- [x] Functional Design 질문 생성
- [x] Functional Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-002-http-runtime-policy/functional-design/business-logic-model.md` 생성
- [x] `aidlc-docs/construction/uow-002-http-runtime-policy/functional-design/business-rules.md` 생성
- [x] `aidlc-docs/construction/uow-002-http-runtime-policy/functional-design/domain-entities.md` 생성

## Functional Design Questions

### Question 1. HTTP Client Runtime

HTTP 요청 구현은 어떤 방식으로 고정할까요?

A) (권장) `httpx.AsyncClient`를 사용한다. UOW-001의 async port/API와 후속 멀티 워커 구조에 맞춘다.

추천 사유: 후속 UOW-003 to UOW-005가 비동기 링크 수집과 worker pool을 사용합니다. `requests` 기반 동기 구현을 넣으면 나중에 thread wrapper가 필요해집니다.

B) `requests`를 사용한다. 기능명세서의 초기 기술 스택 문구를 그대로 따른다.

C) `httpx`와 `requests`를 모두 지원한다.

X) 기타

[Answer]: A

### Question 2. Request Delay Scope

요청 간격 제한은 어느 범위에 적용할까요?

A) (권장) 하나의 `HttpClient` 인스턴스 전체에 global request interval을 적용한다. 모든 worker 요청이 같은 limiter를 공유한다.

추천 사유: DCinside 요청 속도를 제어하는 목적이면 worker별 제한보다 process/client 단위 제한이 예측 가능합니다. 기본값 1초 정책과도 맞습니다.

B) worker별로 request interval을 적용한다.

C) host/path별로 별도 limiter를 둔다.

X) 기타

[Answer]: A

### Question 3. Retry Policy

재시도 대상과 기본 정책은 어떻게 둘까요?

A) (권장) 네트워크 오류, timeout, 429, 5xx만 재시도한다. 기본 최대 3회, backoff 적용, CAPTCHA/block/access denied는 재시도하지 않고 typed exception으로 넘긴다.

추천 사유: 차단 또는 CAPTCHA를 반복 요청하면 상황이 악화될 수 있습니다. 일시적 네트워크 실패만 재시도하는 편이 안전합니다.

B) 모든 non-2xx 응답을 재시도한다.

C) 재시도는 하지 않고 후속 JobRunner가 실패 처리를 전담한다.

X) 기타

[Answer]: A

### Question 4. Timeout Defaults

기본 timeout 값은 어떻게 설정할까요?

A) (권장) connect 10초, read 30초, write 30초, pool 10초를 기본값으로 둔다. adapter/config에서 override 가능하게 한다.

추천 사유: 게시글 HTML과 댓글 API는 길게 잡을 필요가 없지만, 네트워크 지연에는 어느 정도 버틸 필요가 있습니다. 너무 긴 timeout은 worker 정체를 만듭니다.

B) 단일 total timeout 60초만 둔다.

C) timeout 기본값을 두지 않고 httpx 기본값을 따른다.

X) 기타

[Answer]: A

### Question 5. User-Agent Provider

`user-agents.txt` 로딩과 교체는 어떻게 설계할까요?

A) (권장) runtime 생성 시점에만 로드한다. explicit path가 있으면 우선 사용하고, 없으면 실행 위치의 `user-agents.txt`를 시도한다. 빈 줄은 무시하고, 유효 목록이 없으면 기본 User-Agent 1개를 사용한다. 기본 교체 주기는 요청 10회다.

추천 사유: UOW-001 import side-effect 규칙을 지키면서 기존 기능명세서의 자동 로드/기본 교체 주기를 충족합니다.

B) package import 시점에 `user-agents.txt`를 자동 로드한다.

C) User-Agent 파일은 CLI adapter가 전부 처리하고 HTTP runtime은 문자열 하나만 받는다.

X) 기타

[Answer]: A

### Question 6. Proxy Resolution Flow

Proxy 설정 우선순위는 어떻게 둘까요?

A) (권장) explicit runtime option이 최우선, 다음은 실행 위치의 `.env`, 없거나 유효하지 않으면 disabled로 둔다. `.env`는 runtime 생성 시점에만 읽고, 로그에는 host 일부와 enabled 여부만 남긴다.

추천 사유: 기능명세서의 우선순위를 따르면서 import side-effect와 secret redaction 요구를 만족합니다.

B) `.env`를 항상 우선하고 explicit option은 override하지 못하게 한다.

C) Proxy는 CLI/container adapter가 전부 처리하고 HTTP runtime은 이미 만들어진 proxy URL만 받는다.

X) 기타

[Answer]: A

### Question 7. CAPTCHA And Block Classification

CAPTCHA, 차단, 접근 불가 응답은 어디서 분류할까요?

A) (권장) `HttpClient`가 status code, final URL, response body marker를 기준으로 `CaptchaDetectedError`, `BlockedResponseError`, `UnavailableContentError` 등 typed exception으로 분류한다. CAPTCHA 자동 우회는 하지 않는다.

추천 사유: 검색/게시글/댓글 parser가 차단 페이지를 정상 HTML로 오인하지 않게 하려면 HTTP 경계에서 fail-closed 분류가 필요합니다.

B) parser가 HTML을 보고 CAPTCHA/block 여부를 판단한다.

C) JobRunner가 모든 응답을 받아 마지막에 분류한다.

X) 기타

[Answer]: A

### Question 8. Session, Header, And Referer Handling

세션 쿠키와 요청별 header/referer는 어떻게 처리할까요?

A) (권장) 요청별 `Referer`와 header 전달을 우선한다. 서버가 같은 `HttpClient` 생명주기 안에서 내려준 임시 cookie jar만 허용하고, 쿠키는 디스크에 저장하지 않는다. Job 재시작, resume, Proxy 변경, User-Agent 변경 시 기존 쿠키를 재사용하지 않는다.

추천 사유: AJAX 요청에는 쿠키보다 `Referer`, User-Agent, AJAX header, 요청 파라미터가 더 중요할 가능성이 큽니다. 오래된 쿠키나 다른 Proxy/User-Agent에서 받은 쿠키를 섞으면 fingerprint가 이상해질 수 있으므로, 실행 중 임시 쿠키만 보수적으로 허용합니다.

B) 요청마다 완전히 독립적인 stateless client를 사용한다.

C) 쿠키를 파일로 저장해 다음 실행에도 재사용한다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-002 Functional Design 산출물 3개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-002 NFR Requirements로 넘어가지 않습니다.
