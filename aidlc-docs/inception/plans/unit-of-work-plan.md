# Unit Of Work 계획

이 계획은 Application Design 산출물을 바탕으로 구현 단위를 나누기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Units Generation 작업 체크리스트

- [x] Application Design 승인 확인
- [x] 요구사항, 유저 스토리, Application Design 산출물 확인
- [x] 단위 분해 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 불필요 확인
- [x] 사용자 요청을 Unit of Work 계획 승인으로 기록
- [x] `aidlc-docs/inception/application-design/unit-of-work.md` 생성
- [x] `aidlc-docs/inception/application-design/unit-of-work-dependency.md` 생성
- [x] `aidlc-docs/inception/application-design/unit-of-work-story-map.md` 생성
- [x] Greenfield code organization strategy를 `unit-of-work.md`에 기록
- [x] 모든 스토리의 unit 배정 검증

## 설계 전제

- 단일 Python 패키지 `dcinside_scraper`를 사용합니다.
- CLI, library, container, MCP는 같은 core API를 호출합니다.
- JobRunner 중심 orchestration과 ports/adapters 경계를 적용합니다.
- 컨테이너 JSONL/media 출력은 Garage 기반 S3 호환 저장소를 기본값으로 둡니다.

## 단위 분해 질문

### Question 1. 구현 단위 크기

전체 구현을 어떤 크기의 Unit of Work로 나눌까요?

A) (권장) 기능 흐름 기준 8개 내외 unit으로 나눈다: models/config, HTTP runtime, search collectors, post parser, comments/media/repost, job runner/checkpoint, outputs/storage, adapters/tests.

추천 사유: 이 프로젝트는 parser, runtime, storage, adapters가 서로 다릅니다. 한 unit으로 묶으면 Functional Design과 구현 검토가 커지고, 너무 잘게 쪼개면 승인 비용이 늘어납니다.

B) 패키지 모듈 기준으로 `core`, `models`, `parsers`, `http`, `jobs`, `outputs`, `adapters` 7개 unit으로 나눈다.

C) MVP 우선 단일 unit으로 두고 구현 단계에서 내부 task만 나눈다.

X) 기타

[Answer]: A

### Question 2. Parser 단위 분리

HTML/API parser를 어떤 단위로 묶을까요?

A) (권장) 검색 parser와 게시글 상세 parser를 분리하고, 댓글/미디어/`(펌)` parser는 게시글 상세 unit의 하위 작업으로 둔다.

추천 사유: 검색 수집과 상세 수집은 입력 HTML, 실패 양상, 테스트 fixture가 다릅니다. 댓글/미디어/`(펌)`은 상세 수집 결과를 완성하는 하위 흐름이라 처음부터 별도 unit으로 쪼개지 않아도 됩니다.

B) 검색, 게시글, 댓글, 미디어, `(펌)` parser를 모두 별도 unit으로 나눈다.

C) 모든 parser를 하나의 parser unit으로 묶는다.

X) 기타

[Answer]: A

### Question 3. Storage 단위 범위

저장소 구현 unit에는 어디까지 포함할까요?

A) (권장) local JSONL/media, local checkpoint, S3-compatible output port를 한 unit에 포함하고 PostgreSQL checkpoint는 별도 container/storage unit에서 다룬다.

추천 사유: local output과 S3-compatible output은 Job 결과 저장이라는 같은 경계입니다. PostgreSQL checkpoint는 schema, connection, resume query가 달라 container 실행 계약과 함께 설계하는 편이 낫습니다.

B) 모든 output, media, checkpoint 구현을 하나의 storage unit에 포함한다.

C) local output, S3 output, PostgreSQL checkpoint를 각각 별도 unit으로 나눈다.

X) 기타

[Answer]: A

### Question 4. Adapter 구현 순서

CLI, container, MCP adapter는 어떤 순서로 구현할까요?

A) (권장) CLI를 먼저 구현하고, container와 MCP는 같은 core API가 안정된 뒤 별도 unit으로 구현한다.

추천 사유: CLI가 Job 설정과 실행 흐름을 가장 빨리 검증합니다. container/MCP는 core API가 흔들릴 때 같이 구현하면 수정 비용이 커집니다.

B) CLI, container, MCP를 하나의 adapter unit에서 같이 구현한다.

C) MCP를 먼저 구현해 AI agent 호출 흐름을 우선 검증한다.

X) 기타

[Answer]: A

### Question 5. Realtime과 Deep Search 배치

실시간 수집과 심층검색은 어느 unit에 배치할까요?

A) (권장) 둘 다 link collector unit에 포함하되, realtime 종료 조건/checkpoint는 job runner unit과 함께 검증한다.

추천 사유: 둘 다 게시글 후보를 queue에 넣는 링크 수집 전략입니다. 다만 realtime은 종료 조건과 checkpoint가 강하므로 JobRunner와의 연결 테스트가 필요합니다.

B) 실시간 수집과 심층검색을 각각 별도 unit으로 분리한다.

C) 1차 구현에서는 일반 검색 unit만 만들고 실시간/심층검색은 후순위 unit으로 둔다.

X) 기타

[Answer]: A

### Question 6. 팀/소유권 기준

향후 여러 사람이 작업한다면 unit 소유권은 어떻게 잡을까요?

A) (권장) 기능 경계별 소유로 둔다: runtime/search/detail/storage/adapters/tests.

추천 사유: 현재는 개인 프로젝트에 가깝지만, 향후 커뮤니티별 scraper와 통합 플랫폼으로 확장할 계획이 있습니다. 기능 경계별 소유가 나중에 병렬 작업하기 쉽습니다.

B) 레이어별 소유로 둔다: core/parsers/jobs/outputs/adapters.

C) 별도 소유권 기준은 지금 문서화하지 않는다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 Unit of Work 계획 승인을 요청합니다.
4. 승인 후 `unit-of-work.md`, `unit-of-work-dependency.md`, `unit-of-work-story-map.md`를 생성합니다.
