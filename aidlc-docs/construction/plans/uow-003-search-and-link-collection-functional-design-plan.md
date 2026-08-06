# Functional Design 계획 - UOW-003 Search And Link Collection

이 계획은 `UOW-003 Search And Link Collection`의 기능 설계를 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-003 Search And Link Collection
- **Depends On**: UOW-001 Core Models And Config, UOW-002 HTTP Runtime Policy
- **Primary Stories**: US-004, US-005, US-006, US-006A, US-006B
- **Scope**: direct URL normalization, gallery search, integrated search, deep search, no-keyword range search, realtime link discovery, dedupe, range filtering, search position traversal
- **Out Of Scope**: post detail parsing, comments, media download, output storage, checkpoint persistence, CLI prompt UX, container/MCP hosting

## Functional Design 작업 체크리스트

- [x] UOW-002 Build and Test 승인 확인
- [x] UOW-003 범위 확인
- [x] `docs/Function_Specification.md` 검색/링크 수집 항목 확인
- [x] Functional Design 질문 생성
- [x] Functional Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-003-search-and-link-collection/functional-design/business-logic-model.md` 생성
- [x] `aidlc-docs/construction/uow-003-search-and-link-collection/functional-design/business-rules.md` 생성
- [x] `aidlc-docs/construction/uow-003-search-and-link-collection/functional-design/domain-entities.md` 생성

## Functional Design Questions

### Question 1. Collector Output Contract

UOW-003의 링크 수집 결과는 어떤 형태로 후속 unit에 넘길까요?

A) (권장) UOW-003 내부 collector는 `PostCandidate`를 순차 생성하는 async iterator/list API를 제공하고, 실제 `asyncio.Queue` 투입은 UOW-005 JobRunner에서 담당한다.

추천 사유: UOW-003는 검색과 후보 생성만 검증하면 됩니다. Queue lifecycle까지 넣으면 UOW-005 책임이 앞당겨집니다.

B) UOW-003가 직접 `asyncio.Queue`를 인자로 받아 후보를 넣는다.

C) UOW-003는 HTML parser만 제공하고 수집 흐름은 전부 UOW-005로 미룬다.

X) 기타

[Answer]: A

### Question 2. Gallery Search Traversal

갤러리 내 검색의 `page`와 `search_pos` 탐색은 어떻게 설계할까요?

A) (권장) 현재 `search_pos` 구간에서 `page=1`부터 마지막 페이지까지 순차 수집한 뒤, 응답 HTML의 `a.search_next[href]`를 그대로 따라 다음 구간으로 이동한다. 최초 `search_pos`는 생략/빈 값으로 시작하고 직접 계산하지 않는다.

추천 사유: 이미 분석한 DCinside 동작과 맞습니다. 최신 글번호에서 `search_pos`를 계산하는 방식은 깨지기 쉽습니다.

B) 최신 글번호를 구해 `search_pos=최신글번호-10000` 방식으로 직접 구간을 계산한다.

C) `search_pos`를 사용하지 않고 `page`만 증가시킨다.

X) 기타

[Answer]: A

### Question 3. Gallery Row Parser Boundary

갤러리 목록 HTML 파싱은 어디까지 UOW-003에서 처리할까요?

A) (권장) BeautifulSoup 기반 `GallerySearchParser`가 게시글 행, 말머리, `(펌)` 목록 표시, 작성일, 조회수, 추천수, `search_next`, `page_end`를 `GallerySearchPage`/후보 metadata로 변환한다.

추천 사유: 상세 본문 파싱은 UOW-004지만, 목록에서 후보 필터링과 dedupe에 필요한 값은 UOW-003가 알아야 합니다.

B) UOW-003는 상세 URL만 추출하고 나머지 목록 metadata는 버린다.

C) 목록 HTML 전체를 후속 parser unit으로 넘긴다.

X) 기타

[Answer]: A

### Question 4. Integrated Search URL And Parser

통합 검색 URL 생성과 파싱은 어떻게 둘까요?

A) (권장) UTF-8 percent encoding 후 `%`를 `.`로 치환하는 URL builder를 두고, `IntegratedSearchParser`가 결과 item, 마지막 페이지, 갤러리 후보, 상세 URL의 `id`/`no`/갤러리 타입을 추출한다. 페이지는 최대 120으로 제한한다.

추천 사유: 통합 검색 URL 규칙과 120페이지 제한은 UOW-003의 핵심 동작입니다. 후속 unit으로 미루면 심층검색을 설계하기 어렵습니다.

B) 통합 검색 URL은 사용자가 입력한 URL만 받아 그대로 호출한다.

C) 통합 검색은 1차 구현에서 제외한다.

X) 기타

[Answer]: A

### Question 5. Range Filter And Termination

글번호/작성일 범위 필터와 종료 조건은 어디에서 적용할까요?

A) (권장) UOW-003 collector가 `RangeFilter`를 사용해 후보 추가 여부를 결정하고, 정렬상 더 이상 범위에 들어올 수 없다고 판단되면 해당 탐색 구간을 종료한다. 최종 저장 전 중복 방지는 UOW-005/UOW-006에서도 한 번 더 한다.

추천 사유: 링크 단계에서 불필요한 상세 fetch를 줄이되, 저장 단계의 멱등성은 후속 unit에서 보강할 수 있습니다.

B) 모든 후보를 Queue에 넣고 게시글 상세 파싱 후에만 범위 필터링한다.

C) 범위 필터는 CLI validation만 하고 collector에서는 적용하지 않는다.

X) 기타

[Answer]: A

### Question 6. No-Keyword Range Search

노키워드 기간/글번호 범위 수집은 어떻게 구현할까요?

A) (권장) 초기 URL은 `s_type=search_subject_memo&s_keyword=%20`을 사용하고, `date_to`가 있으면 `POST /ajax/search_ajax/search_date/`로 `search_pos`를 받은 뒤 갤러리 검색 traversal을 재사용한다. form의 `keyword`는 빈 문자열로 보낸다.

추천 사유: 브라우저 클릭 없이 BeautifulSoup/httpx만으로 작성일 빠른 이동을 재현하는 현재 명세와 일치합니다.

B) Playwright로 빠른 이동 UI를 클릭해 `search_pos`를 얻는다.

C) 노키워드 수집은 글번호 범위만 지원하고 날짜 이동은 제외한다.

X) 기타

[Answer]: A

### Question 7. Deep Search Flow

심층검색은 어떤 흐름으로 설계할까요?

A) (권장) 1단계 통합 검색으로 최대 120페이지까지 갤러리 후보를 만들고, `(gallery_type, gallery_id)`로 dedupe한 뒤, 후보 갤러리마다 같은 키워드로 갤러리 내 검색을 순차 수행한다. 일부 갤러리 실패는 실패 목록에 기록하고 전체 Job은 계속 진행한다.

추천 사유: 통합 검색의 페이지 제한을 보완하면서도 한 Job에서 과도한 병렬 탐색을 하지 않습니다.

B) 후보 갤러리 검색을 모두 병렬 실행한다.

C) 통합 검색 결과는 갤러리 후보만 만들고, 통합 검색에서 발견한 게시글 후보는 최종 후보에 포함하지 않는다.

X) 기타

[Answer]: A

### Question 8. Realtime Collection Boundary

실시간 키워드/전체 수집은 UOW-003에서 어디까지 담당할까요?

A) (권장) UOW-003는 한 번의 최신 목록/검색 확인을 수행하는 reusable collection cycle과 dedupe set 적용을 제공한다. 반복 타이머, 종료시각, checkpoint 저장은 UOW-005 JobRunner가 소유한다.

추천 사유: 실시간 반복은 lifecycle 문제입니다. UOW-003는 각 cycle에서 새 후보를 찾는 역할만 맡는 편이 작고 테스트하기 쉽습니다.

B) UOW-003가 실시간 while loop, 종료 조건, checkpoint 저장까지 모두 담당한다.

C) 실시간 수집은 UOW-007 CLI에서만 구현한다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-003 Functional Design 산출물 3개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-003 NFR Requirements로 넘어가지 않습니다.
