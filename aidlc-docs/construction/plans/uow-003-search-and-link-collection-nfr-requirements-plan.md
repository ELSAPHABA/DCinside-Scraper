# NFR Requirements 계획 - UOW-003 Search And Link Collection

이 계획은 `UOW-003 Search And Link Collection`의 비기능 요구사항과 기술 선택을 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-003 Search And Link Collection
- **Functional Design**: 승인됨
- **Depends On**: UOW-001 Core Models And Config, UOW-002 HTTP Runtime Policy
- **Primary Stories**: US-004, US-005, US-006, US-006A, US-006B
- **Scope**: search/list URL generation, BeautifulSoup parser correctness, traversal bounds, dedupe, range filtering, no-keyword date jump, deep search discovery, realtime collection cycle
- **Security Focus**: safe URL logging, no raw HTML/body dump, no cookie/proxy leakage, CAPTCHA/block propagation
- **Resiliency Focus**: bounded traversal, partial deep-search failure handling, parser failure isolation, deterministic resume handoff state
- **PBT Focus**: URL/query round trip, keyword encoding, page limit, dedupe idempotence, range filter invariants
- **Out Of Scope**: post detail parsing, result storage, checkpoint persistence, queue lifecycle, CLI prompt UX, container/MCP hosting

## NFR Requirements 작업 체크리스트

- [x] UOW-003 Functional Design 승인 확인
- [x] Functional Design 산출물 확인
- [x] Security Baseline 적용 항목 확인
- [x] Resiliency Baseline 적용 항목 확인
- [x] Property-Based Testing 적용 항목 확인
- [x] NFR Requirements 질문 생성
- [x] NFR Requirements 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-003-search-and-link-collection/nfr-requirements/nfr-requirements.md` 생성
- [x] `aidlc-docs/construction/uow-003-search-and-link-collection/nfr-requirements/tech-stack-decisions.md` 생성

## NFR Requirements Questions

### Question 1. Traversal Bound Guardrail

갤러리 검색, 통합 검색, 심층검색 탐색 제한은 어떻게 둘까요?

A) (권장) 통합 검색은 최대 120페이지를 hard limit으로 두고, 갤러리 검색은 설정 범위나 `search_next` 종료가 기본 종료 조건이다. 다만 설정 실수 방지를 위해 optional `max_pages`/`max_segments` guardrail을 config에 둘 수 있게 한다.

추천 사유: 통합 검색 120페이지 제한은 명세상 고정입니다. 갤러리 검색은 `search_next` 기반이지만, 무한 탐색 방지를 위한 선택 상한은 테스트와 운영 안정성에 유리합니다.

B) 갤러리 검색도 항상 고정 120페이지까지만 탐색한다.

C) 모든 탐색 제한은 후속 JobRunner에서만 처리한다.

X) 기타

[Answer]: A

### Question 2. Parser Fixture Coverage

BeautifulSoup parser fixture 테스트 범위는 어디까지 둘까요?

A) (권장) UOW-003 code generation에서 gallery search, subject head, integrated search, no-keyword search_date JSON, deep-search gallery candidate fixture를 최소 1개씩 둔다.

추천 사유: UOW-003의 주된 리스크는 DOM/URL 파싱입니다. live 요청보다 작은 fixture가 빠르고 재현성이 좋습니다.

B) parser fixture는 gallery search와 integrated search만 둔다.

C) fixture 없이 PBT만 사용한다.

X) 기타

[Answer]: A

### Question 3. Parser Failure Handling

파서가 일부 행을 파싱하지 못할 때 실패 기준은 어떻게 둘까요?

A) (권장) 개별 row 파싱 실패는 safe `CollectorFailure`로 기록하고 나머지 row는 계속 처리한다. 단, 페이지 구조 자체가 검색 결과로 인식되지 않거나 CAPTCHA/block은 UOW-002 오류를 그대로 전파한다.

추천 사유: 한 행의 깨진 HTML 때문에 전체 Job을 멈추면 수집 손실이 커집니다. CAPTCHA/block은 중단점 저장이 필요하므로 삼키면 안 됩니다.

B) 한 row라도 파싱 실패하면 페이지 전체를 실패 처리한다.

C) 파싱 실패는 전부 무시하고 기록하지 않는다.

X) 기타

[Answer]: A

### Question 4. Dedupe Memory Bound

후보 dedupe set은 어떤 수준으로 제한할까요?

A) (권장) UOW-003에서는 in-memory set을 기본으로 쓰고, optional `max_seen_candidates` 초과 시 안전하게 중단/오류 처리한다. 대용량 영속 dedupe는 UOW-006 저장소/idempotency로 미룬다.

추천 사유: UOW-003 단독에서 DB나 bloom filter를 넣을 필요는 없습니다. 하지만 unbounded set은 장시간 realtime/deep-search에서 위험합니다.

B) SQLite 기반 영속 dedupe를 UOW-003에서 구현한다.

C) dedupe memory 제한은 두지 않는다.

X) 기타

[Answer]: A

### Question 5. Range Filter Accuracy

작성일/글번호 범위 필터의 정확도 요구사항은 어떻게 둘까요?

A) (권장) post number 범위는 숫자 파싱 성공 시 강하게 적용하고, 작성일 범위는 목록 날짜가 절대 날짜로 파싱될 때만 강하게 적용한다. 상대/모호 날짜는 포함하되 후속 상세 파싱에서 재검증 가능하게 metadata에 표시한다.

추천 사유: DCinside 목록 날짜 형식은 상황에 따라 달라질 수 있습니다. 링크 단계에서 모호 날짜를 과감히 버리면 누락 위험이 큽니다.

B) 날짜 파싱이 실패하면 후보를 항상 제외한다.

C) 날짜/글번호 범위 필터는 UOW-003에서 적용하지 않는다.

X) 기타

[Answer]: A

### Question 6. Observability Scope

UOW-003의 structured logging 요구사항은 어디까지 둘까요?

A) (권장) collector start/end, page fetched, segment advanced, candidate accepted/skipped/deduped count, range termination, deep-search per-gallery failure를 safe structured event로 남긴다. raw HTML, raw cookie, proxy credential, full query URL은 로그에 남기지 않는다.

추천 사유: 검색 탐색 문제를 추적하려면 카운트와 상태가 필요하지만, raw HTML/전체 URL은 크고 민감할 수 있습니다.

B) 디버깅 편의를 위해 raw HTML과 전체 URL/query를 debug log에 남긴다.

C) UOW-003에서는 logging을 하지 않는다.

X) 기타

[Answer]: A

### Question 7. Property-Based Test Targets

UOW-003에서 PBT 대상으로 삼을 속성은 무엇으로 할까요?

A) (권장) gallery URL round trip, integrated keyword encoding determinism, integrated max page clamp, candidate dedupe idempotence, range filter monotonicity, realtime dedupe exclusion, deep-search gallery dedupe를 PBT 대상으로 둔다. BeautifulSoup DOM 파싱은 fixture/example 테스트로 둔다.

추천 사유: PBT는 순수 URL/정책 로직에 잘 맞고, DOM parser는 사람이 만든 fixture가 더 명확합니다.

B) BeautifulSoup fixture DOM까지 전부 랜덤 생성해 PBT로 검증한다.

C) UOW-003에서는 PBT를 생략한다.

X) 기타

[Answer]: A

### Question 8. Live Smoke Test Policy

UOW-003의 DCinside live smoke test는 어떤 기준으로 둘까요?

A) (권장) 기본 unit test와 CI 필수 gate에서는 제외한다. 환경변수로 명시적으로 켠 경우에만 갤러리 검색 1페이지 또는 통합 검색 1페이지 수준의 선택적 smoke test를 허용한다.

추천 사유: DCinside DOM과 차단 정책은 바뀔 수 있습니다. 기본 테스트는 fixture로 안정화하고, live smoke는 수동 검증 경로로 두는 편이 낫습니다.

B) 모든 CI에서 gallery search와 integrated search live smoke를 필수 실행한다.

C) live smoke 경로를 아예 만들지 않는다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-003 NFR Requirements 산출물 2개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-003 NFR Design으로 넘어가지 않습니다.
