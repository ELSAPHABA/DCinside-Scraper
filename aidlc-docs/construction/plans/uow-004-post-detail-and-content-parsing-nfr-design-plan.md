# NFR Design 계획 - UOW-004 Post Detail And Content Parsing

이 계획은 `UOW-004 Post Detail And Content Parsing`의 NFR 요구사항을 구현 패턴과 논리 컴포넌트로 구체화하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-004 Post Detail And Content Parsing
- **NFR Requirements**: 승인됨
- **Depends On**: UOW-001 Core Models And Config, UOW-002 HTTP Runtime Policy, UOW-003 Search And Link Collection
- **Scope**: parser fixture layout, bounded comment pagination, optional subfetch isolation, safe failure metadata, raw HTML exclusion, PBT strategy, live smoke boundary
- **Out Of Scope**: JSONL/Garage storage, media file download, checkpoint persistence, queue lifecycle, CLI prompt UX, container/MCP hosting

## NFR Design 작업 체크리스트

- [x] UOW-004 NFR Requirements 승인 확인
- [x] NFR Requirements 산출물 확인
- [x] NFR Design 질문 생성
- [x] NFR Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-004-post-detail-and-content-parsing/nfr-design/nfr-design-patterns.md` 생성
- [x] `aidlc-docs/construction/uow-004-post-detail-and-content-parsing/nfr-design/logical-components.md` 생성
- [x] Security/Resiliency/PBT compliance 확인

## NFR Design Questions

### Question 1. Fixture Organization

UOW-004 parser fixture는 어디에 둘까요?

A) (권장) `tests/fixtures/post_detail/` 아래에 일반 게시글, 혼합 본문, `(펌)` AJAX, DC video iframe, 댓글 AJAX JSON, 렌더링 댓글 HTML fallback, 선택 필드 누락 fixture를 작은 파일로 나눈다.

추천 사유: 상세 HTML과 댓글/AJAX fixture는 길어지기 쉽습니다. 파일로 분리하면 selector 변경과 회귀 테스트 추적이 단순합니다.

B) 모든 HTML/JSON fixture를 test file 안에 inline string으로 둔다.

C) fixture 없이 live 페이지 요청으로만 검증한다.

X) 기타

[Answer]: A

### Question 2. Comment Pagination Guard Pattern

댓글 페이지 상한은 어떤 컴포넌트가 적용할까요?

A) (권장) `CommentPaginationGuard`가 pagination 종료, 빈 페이지 종료, 기본 `max_comment_pages=100` 초과를 한 곳에서 판단하고 safe failure reason을 반환한다.

추천 사유: 댓글 수집 loop 안에 조건을 흩뿌리면 페이지 한계와 부분 실패 기록이 누락되기 쉽습니다. 작은 guard 하나면 충분합니다.

B) `CommentService` loop 안에서 조건을 직접 구현한다.

C) 댓글 페이지 상한은 UOW-005 JobRunner에서만 처리한다.

X) 기타

[Answer]: A

### Question 3. Optional Subfetch Failure Pattern

`(펌)` AJAX, DC video iframe, 댓글 AJAX 실패는 어떻게 모을까요?

A) (권장) `DetailFailureRecorder`가 optional subfetch/subparse 실패를 `stage`, `reason`, `retryable`, `field_path`, `failed_fields` 형태로 누적하고, CAPTCHA/block은 기록하지 않고 전파한다.

추천 사유: 실패 metadata shape를 한 곳에서 만들면 raw HTML/URL 누출을 막고 차후 재시도 유닛 입력도 안정화됩니다.

B) 각 parser/service가 `metadata["detail_failures"]` dict를 직접 수정한다.

C) optional subfetch 실패는 모두 무시한다.

X) 기타

[Answer]: A

### Question 4. Raw HTML Exclusion Pattern

raw HTML/AJAX body 저장 금지는 어디에서 보장할까요?

A) (권장) parser/service public output은 `PostResult` 모델만 반환하고, failure recorder와 logger event builder가 raw body 필드를 허용하지 않는다. fixture 파일은 테스트 경로에만 둔다.

추천 사유: 출력 모델과 event 생성 경계에서 막으면 운영 JSONL/로그에 원문이 새지 않습니다.

B) raw HTML을 `metadata.raw_html`에 넣고 저장 단계에서 제거한다.

C) raw HTML 저장 여부는 호출자가 알아서 결정한다.

X) 기타

[Answer]: A

### Question 5. Normalization Utility Pattern

제목, 숫자, 날짜, nickname type 같은 순수 정규화 로직은 어디에 둘까요?

A) (권장) `post_detail.normalization` 같은 작은 모듈에 순수 함수로 두고, parser와 PBT가 함께 사용한다.

추천 사유: BeautifulSoup selector 코드와 순수 변환 코드를 분리하면 PBT가 쉬워지고 중복이 줄어듭니다.

B) 각 parser method 안에 정규화 코드를 직접 작성한다.

C) 정규화 없이 문자열을 그대로 모델에 넣는다.

X) 기타

[Answer]: A

### Question 6. Safe Parser Event Pattern

파서/상세 수집 로그의 sanitizing은 어디에서 처리할까요?

A) (권장) `SafeDetailEventBuilder`가 raw HTML/body, cookie, proxy, full query URL을 제외한 count/state 중심 event를 만들고 UOW-001 `LoggerPort`로 전달한다.

추천 사유: UOW-002/UOW-003의 safe event 방식과 맞고, call site마다 sanitizing을 반복하지 않아도 됩니다.

B) 각 parser/service가 logging call site마다 직접 dict를 만든다.

C) debug log에는 raw HTML과 full URL query를 허용한다.

X) 기타

[Answer]: A

### Question 7. PBT Strategy Organization

UOW-004 Hypothesis strategy는 어디에 둘까요?

A) (권장) `tests/strategies/post_detail.py`에 제목, 숫자 문자열, 날짜 문자열, nickname 입력, content block order, failure record strategy를 둔다.

추천 사유: DOM fixture 테스트와 순수 정규화 PBT 입력을 분리하면 테스트가 짧고 재사용 가능해집니다.

B) 각 test file 안에 필요한 strategy를 인라인으로 둔다.

C) production code 안에 generator를 둔다.

X) 기타

[Answer]: A

### Question 8. Live Smoke Design Boundary

UOW-004 live smoke test는 코드 구조상 어떻게 분리할까요?

A) (권장) `tests/test_post_detail_live_smoke.py`에 marker와 env guard를 두고, 기본 pytest에서는 skip한다. 실행 시 게시글 1개와 댓글 1페이지까지만 확인하고 media download는 하지 않는다.

추천 사유: live smoke 경로는 남기되 CI 기본 안정성을 지킬 수 있습니다.

B) 일반 parser unit test 안에서 live request를 같이 실행한다.

C) live smoke test 파일을 만들지 않는다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-004 NFR Design 산출물 2개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 Infrastructure Design 또는 Code Generation으로 넘어가지 않습니다.

## 검토 결과

- 모든 답변은 A로 확정되었습니다.
- 답변 간 충돌은 없습니다.
- follow-up 질문은 필요하지 않습니다.
- 산출물 생성 후 UOW-004 NFR Design Review 단계에서 사용자 승인을 대기합니다.
