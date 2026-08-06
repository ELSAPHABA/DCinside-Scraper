# NFR Requirements 계획 - UOW-004 Post Detail And Content Parsing

이 계획은 `UOW-004 Post Detail And Content Parsing`의 비기능 요구사항과 기술 선택을 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-004 Post Detail And Content Parsing
- **Functional Design**: 승인됨
- **Depends On**: UOW-001 Core Models And Config, UOW-002 HTTP Runtime Policy, UOW-003 Search And Link Collection
- **Primary Stories**: US-007, US-008, US-009, US-010, US-011
- **Scope**: detail HTML fetch, metadata parsing, ordered content blocks, repost AJAX parsing, DC video iframe metadata, comment/reply AJAX parsing, dccon metadata parsing
- **Security Focus**: no raw HTML/body dump in logs or failures, no cookie/proxy leakage, safe partial failure metadata, CAPTCHA/block propagation
- **Resiliency Focus**: optional subfetch isolation, bounded comment pagination, malformed DOM handling, future targeted retry handoff
- **PBT Focus**: title normalization, count/date parsing, nickname type parsing, content block order, safe failure record shape
- **Out Of Scope**: JSONL/Garage storage, media file download, checkpoint persistence, queue lifecycle, CLI prompt UX, container/MCP hosting

## NFR Requirements 작업 체크리스트

- [x] UOW-004 Functional Design 승인 확인
- [x] Functional Design 산출물 확인
- [x] Security Baseline 적용 항목 확인
- [x] Resiliency Baseline 적용 항목 확인
- [x] Property-Based Testing 적용 항목 확인
- [x] NFR Requirements 질문 생성
- [x] NFR Requirements 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-004-post-detail-and-content-parsing/nfr-requirements/nfr-requirements.md` 생성
- [x] `aidlc-docs/construction/uow-004-post-detail-and-content-parsing/nfr-requirements/tech-stack-decisions.md` 생성

## NFR Requirements Questions

### Question 1. Parser Fixture Coverage

UOW-004의 BeautifulSoup parser fixture 테스트 범위는 어디까지 둘까요?

A) (권장) 일반 게시글, 혼합 본문(텍스트/이미지/DC video/YouTube/link/series), `(펌)` AJAX 응답, DC video iframe, 댓글 AJAX JSON, 렌더링 댓글 HTML fallback, 선택 필드 누락 fixture를 최소 1개씩 둔다.

추천 사유: UOW-004의 주된 리스크는 DCinside DOM과 AJAX 응답 구조입니다. live 요청보다 fixture가 빠르고 재현성이 좋습니다.

B) 일반 게시글과 댓글 AJAX fixture만 둔다.

C) fixture 없이 live smoke test로만 검증한다.

X) 기타

[Answer]: A

### Question 2. Comment Pagination Bound

댓글 페이지 수집 상한은 어떻게 둘까요?

A) (권장) AJAX 응답의 pagination 또는 빈 댓글 페이지를 종료 조건으로 사용하되, 기본 `max_comment_pages=100` guardrail을 둔다. 상한 도달 시 해당 게시글은 반환하고 `detail_failures`에 `comment_page_limit`을 기록한다.

추천 사유: 댓글이 많은 글에서 무한/과도 요청을 막으면서도 본문 수집 결과는 보존할 수 있습니다.

B) 상한 없이 pagination이 끝날 때까지 전부 수집한다.

C) 댓글은 첫 페이지만 수집한다.

X) 기타

[Answer]: A

### Question 3. Optional Subfetch Policy

`(펌)` AJAX, DC video iframe, 댓글 AJAX 같은 하위 요청의 실패와 재시도는 어떻게 처리할까요?

A) (권장) UOW-004 자체 재시도 루프는 만들지 않고 UOW-002 HTTP 정책에 맡긴다. 실패한 하위 요청은 CAPTCHA/block이 아니면 `detail_failures`에 기록하고 가능한 `PostResult`를 반환한다.

추천 사유: 재시도 정책이 여러 계층에 흩어지면 요청 수 제어가 어려워집니다. UOW-004는 파싱 결과 조립에 집중하는 편이 안전합니다.

B) UOW-004가 하위 요청별로 별도 재시도 횟수를 가진다.

C) 하위 요청 실패 시 전체 게시글을 실패 처리한다.

X) 기타

[Answer]: A

### Question 4. Failure Metadata Shape

부분 실패 정보를 어떤 수준으로 저장할까요?

A) (권장) `PostResult.metadata["detail_failures"]`에 `stage`, `reason`, `retryable`, `field_path`, `failed_fields`만 저장한다. raw HTML, 전체 URL, 쿠키, proxy 정보는 저장하지 않는다.

추천 사유: 차후 “메타데이터 파싱 실패 게시글 재시도 유닛”에 필요한 최소 정보만 남기고 민감/대용량 데이터를 피할 수 있습니다.

B) 디버깅을 위해 실패한 HTML 조각과 전체 요청 URL도 저장한다.

C) 실패 여부만 boolean으로 저장한다.

X) 기타

[Answer]: A

### Question 5. Raw HTML Retention

게시글/댓글 원본 HTML 또는 AJAX 원문은 저장 결과에 포함할까요?

A) (권장) 저장 결과와 로그에는 포함하지 않는다. 테스트 fixture와 수동 디버깅 파일에만 원문을 둘 수 있고, 운영 `PostResult`에는 파싱된 구조만 남긴다.

추천 사유: 원문 HTML은 크고 변동이 심하며, 쿠키/광고/추적 값이 섞일 수 있습니다. JSONL 분석/RAG 입력에도 구조화 결과가 더 적합합니다.

B) `metadata.raw_html`에 게시글 HTML 전체를 저장한다.

C) 파싱 실패한 경우에만 원문 HTML을 저장한다.

X) 기타

[Answer]: A

### Question 6. Parser Test Strategy

Property-Based Test는 어디에 적용할까요?

A) (권장) DOM 전체 랜덤 생성은 하지 않고, 순수 함수 중심으로 적용한다. 대상은 제목 `(펌)` 제거, 숫자/날짜 정규화, nickname type 판정, content block order 보존, safe failure record shape로 둔다. DOM 파싱은 fixture/example 테스트로 검증한다.

추천 사유: PBT는 순수 변환 로직에 잘 맞고, BeautifulSoup DOM 구조는 사람이 만든 fixture가 더 명확합니다.

B) BeautifulSoup DOM까지 전부 랜덤 생성해 PBT로 검증한다.

C) UOW-004에서는 PBT를 생략한다.

X) 기타

[Answer]: A

### Question 7. Memory Bound

상세 게시글 파싱 중 메모리 사용은 어떻게 제한할까요?

A) (권장) 한 게시글 단위로 detail HTML과 하위 AJAX 응답만 메모리에 들고 파싱 후 버린다. `PostResult`에는 구조화된 block/comment/media metadata만 남기며, 댓글은 `max_comment_pages` guardrail로 제한한다.

추천 사유: 멀티 워커에서 원문 HTML을 누적 보관하면 메모리 사용량이 쉽게 커집니다.

B) 디버깅 편의를 위해 Job 전체의 원문 HTML을 메모리에 보관한다.

C) 메모리 제한은 후속 UOW에서만 다룬다.

X) 기타

[Answer]: A

### Question 8. Live Smoke Test Policy

UOW-004의 DCinside live smoke test는 어떤 기준으로 둘까요?

A) (권장) 기본 unit test와 CI 필수 gate에서는 제외한다. 환경변수로 명시적으로 켠 경우에만 게시글 1개와 댓글 1페이지 수준의 선택적 smoke test를 허용한다.

추천 사유: DCinside DOM과 차단 정책은 바뀔 수 있습니다. 기본 테스트는 fixture로 안정화하고 live smoke는 수동 검증 경로로 두는 편이 낫습니다.

B) 모든 CI에서 게시글 상세와 댓글 live smoke를 필수 실행한다.

C) live smoke 경로를 아예 만들지 않는다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-004 NFR Requirements 산출물 2개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-004 NFR Design으로 넘어가지 않습니다.
