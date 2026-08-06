# NFR Design 계획 - UOW-003 Search And Link Collection

이 계획은 `UOW-003 Search And Link Collection`의 NFR 요구사항을 구현 패턴과 논리 컴포넌트로 구체화하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-003 Search And Link Collection
- **NFR Requirements**: 승인됨
- **Depends On**: UOW-001 Core Models And Config, UOW-002 HTTP Runtime Policy
- **Scope**: traversal guardrails, parser fixtures, row-level failures, dedupe bounds, range filter accuracy, safe collector logging, PBT design, live smoke boundary
- **Out Of Scope**: post detail parsing, output storage, checkpoint persistence, queue lifecycle, CLI prompt UX, container/MCP hosting

## NFR Design 작업 체크리스트

- [x] UOW-003 NFR Requirements 승인 확인
- [x] NFR Requirements 산출물 확인
- [x] NFR Design 질문 생성
- [x] NFR Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-003-search-and-link-collection/nfr-design/nfr-design-patterns.md` 생성
- [x] `aidlc-docs/construction/uow-003-search-and-link-collection/nfr-design/logical-components.md` 생성
- [x] Security/Resiliency/PBT compliance 확인

## NFR Design Questions

### Question 1. Traversal Guardrail Pattern

탐색 상한은 어떤 컴포넌트로 적용할까요?

A) (권장) `TraversalGuard`가 integrated max page 120, optional `max_pages`, optional `max_segments`, `max_seen_candidates`를 한 곳에서 검사하고 safe stop/error를 반환한다.

추천 사유: 각 collector에 상한 검사를 흩뿌리면 누락되기 쉽습니다. 작은 policy helper 하나면 충분합니다.

B) 각 collector loop 안에서 상한 조건을 직접 구현한다.

C) 상한 검사는 UOW-005 JobRunner에서만 수행한다.

X) 기타

[Answer]: A

### Question 2. Parser Fixture Organization

검색 parser fixture는 어디에 둘까요?

A) (권장) `tests/fixtures/search/` 아래에 gallery, subject-head, integrated, search-date JSON fixture를 두고, 테스트가 파일을 읽어 BeautifulSoup/parser에 전달한다.

추천 사유: DOM fixture는 테스트 파일 안에 길게 넣으면 읽기 어렵습니다. 작은 fixture 파일이 selector 변경 추적에 좋습니다.

B) 모든 HTML/JSON fixture를 test file 안에 inline string으로 둔다.

C) fixture 없이 live 페이지를 저장하지 않고 매번 외부 요청한다.

X) 기타

[Answer]: A

### Question 3. Row Failure Pattern

개별 row 파싱 실패는 어떻게 표현할까요?

A) (권장) parser가 `(candidates, failures)`를 함께 반환하고, 실패에는 row index, stage, safe reason, retryable=false만 저장한다. raw row HTML은 저장하지 않는다.

추천 사유: 실패를 버리지 않되, raw HTML 로그/결과 누출을 피할 수 있습니다.

B) 예외를 throw해 collector가 페이지 전체를 실패 처리한다.

C) 실패 행은 아무 기록 없이 무시한다.

X) 기타

[Answer]: A

### Question 4. Dedupe Bound Pattern

dedupe memory bound는 어떻게 구현할까요?

A) (권장) `CandidateDeduper`가 seen set과 optional `max_seen_candidates`를 소유하고, 초과 시 typed validation/runtime error를 반환한다. 대용량 영속 dedupe는 구현하지 않는다.

추천 사유: UOW-003 범위에서는 in-memory set이면 충분합니다. 상한 검사는 같은 컴포넌트가 갖는 편이 작습니다.

B) SQLite dedupe store를 UOW-003에 포함한다.

C) dedupe set 상한을 코드에 두지 않고 문서만 둔다.

X) 기타

[Answer]: A

### Question 5. Date Parse Accuracy Pattern

목록 작성일 파싱 정확도는 어떻게 설계할까요?

A) (권장) `DateParser`가 absolute date/datetime만 강한 필터 대상으로 반환하고, 상대/모호 날짜는 `date_precision="ambiguous"` metadata로 표시해 포함한다.

추천 사유: 링크 단계에서 날짜 해석을 과하게 하면 누락됩니다. 상세 페이지에서 더 정확히 검증할 여지를 남깁니다.

B) 상대/모호 날짜는 현재 날짜 기준으로 추정해 필터링한다.

C) 날짜 파싱 실패 후보는 무조건 제외한다.

X) 기타

[Answer]: A

### Question 6. Safe Collector Event Pattern

collector logging sanitizing은 어디에서 처리할까요?

A) (권장) `SafeCollectorEventBuilder`가 URL query 제거, raw HTML/body 제외, `ci_t` 제외, count/state 중심 event를 만들고 UOW-001 `LoggerPort`로 전달한다.

추천 사유: UOW-002의 HTTP event builder와 같은 방식으로 한 경계에서 safe fields만 통과시키면 됩니다.

B) 각 collector가 logging call site마다 직접 dict를 만든다.

C) raw HTML과 full URL query를 debug log에 허용한다.

X) 기타

[Answer]: A

### Question 7. PBT Strategy Organization

UOW-003 Hypothesis strategy는 어디에 둘까요?

A) (권장) `tests/strategies/search.py`에 URL parts, encoded keywords, candidates, ranges, gallery candidates, realtime seen set strategy를 둔다.

추천 사유: URL/정책 PBT 입력을 parser fixture와 분리해 재사용하기 쉽습니다.

B) 각 test file 안에 필요한 strategy를 인라인으로 둔다.

C) production code 안에 generator를 둔다.

X) 기타

[Answer]: A

### Question 8. Live Smoke Design Boundary

UOW-003 live smoke test는 코드 구조상 어떻게 분리할까요?

A) (권장) `tests/test_search_live_smoke.py`에 marker와 env guard를 두고, 기본 pytest에서는 skip한다. 실행 시 gallery search 1페이지 또는 integrated search 1페이지 중 하나만 확인한다.

추천 사유: live smoke 경로는 남기되 CI 기본 안정성을 지킬 수 있습니다.

B) 일반 parser unit test 안에서 live request를 같이 실행한다.

C) live smoke test 파일을 만들지 않는다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-003 NFR Design 산출물 2개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 Infrastructure Design 또는 Code Generation으로 넘어가지 않습니다.

## 검토 결과

- 모든 답변은 A로 확정되었습니다.
- Q4의 `Av` 입력은 선택지 A를 의미하는 오타로 정규화했습니다.
- 답변 간 충돌은 없습니다.
- follow-up 질문은 필요하지 않습니다.
- 산출물 생성 후 UOW-003 NFR Design Review 단계에서 사용자 승인을 대기합니다.
