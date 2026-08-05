# Application Design 계획

이 계획은 `requirements.md`, `stories.md`, `personas.md`, `execution-plan.md`를 바탕으로 Application Design 산출물을 생성하기 위한 질문지입니다.

답변 방법: 아래 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## 설계 범위 요약

- Greenfield Python project
- 1차 실행 방식: CLI, Python library API, worker container, MCP tool
- 핵심 런타임: `httpx`, `asyncio`, BeautifulSoup, 표준 `json`
- 핵심 흐름: Job 설정, 검색/링크 수집, 게시글 상세 수집, 댓글/덧글 수집, JSONL 저장, checkpoint 재개
- 주요 제약: Playwright 런타임 의존 금지, CAPTCHA 우회 금지, 공개 콘텐츠만 수집

## Application Design 작업 체크리스트

- [x] 요구사항, 유저 스토리, 실행 계획 확인
- [x] 설계 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 불필요 확인
- [x] `aidlc-docs/inception/application-design/components.md` 생성
- [x] `aidlc-docs/inception/application-design/component-methods.md` 생성
- [x] `aidlc-docs/inception/application-design/services.md` 생성
- [x] `aidlc-docs/inception/application-design/component-dependency.md` 생성
- [x] `aidlc-docs/inception/application-design/application-design.md` 생성
- [x] 설계 완전성과 일관성 검증
- [x] 완료한 항목은 즉시 체크리스트에 반영

## 설계 질문

### Question 1. 패키지와 컴포넌트 경계

Python 패키지 구조를 어떻게 나눌까요?

A) (권장) 단일 패키지 `dcinside_scraper` 안에 `core`, `models`, `parsers`, `http`, `jobs`, `outputs`, `adapters` 하위 모듈을 둔다.

추천 사유: CLI, library, container, MCP가 같은 core를 공유해야 하므로 경계는 필요합니다. 하지만 별도 Python package로 쪼개면 1차 구현 관리 비용이 커지므로, 단일 패키지 안에서 하위 모듈로 나누는 정도가 적절합니다.

B) CLI, core library, MCP, container를 별도 Python package로 분리한다.

C) 1차 구현은 `dcinside_scraper` 단일 패키지와 적은 수의 파일로 시작하고, 커질 때 하위 모듈을 분리한다.

X) 기타

[Answer]: A

### Question 2. 데이터 모델 방식

게시글, 댓글, 이미지, repost, checkpoint 같은 결과 모델을 어떤 방식으로 정의할까요?

A) (권장) 표준 `dataclasses`를 사용하고, JSONL 저장 직전에 dict로 변환한다.

추천 사유: 결과 schema는 명확해야 하지만 Pydantic까지 추가할 필요는 아직 없습니다. `dataclasses`는 의존성을 늘리지 않고 타입 힌트와 JSON 변환 경계를 잡기 좋습니다.

B) Pydantic 모델을 사용해 validation과 serialization을 맡긴다.

C) 별도 모델 없이 plain dict 중심으로 구현한다.

X) 기타

[Answer]: B

### Question 3. Public API 형태

Python library API는 async/sync 중 어떤 형태를 기본으로 할까요?

A) (권장) `async` API를 기본으로 제공하고, CLI는 내부에서 `asyncio.run()`으로 실행한다.

추천 사유: 요구사항의 핵심이 `httpx`와 `asyncio` 기반 멀티 워커입니다. public API도 async를 기본으로 두면 내부 구조와 맞고, sync wrapper는 실제 필요가 생겼을 때 추가해도 늦지 않습니다.

B) sync API를 기본으로 제공하고 내부에서 async 처리를 숨긴다.

C) async API와 sync wrapper를 모두 public API로 제공한다.

X) 기타

[Answer]: A

### Question 4. HTTP 클라이언트 경계

요청 속도, retry, timeout, User-Agent, Proxy 적용을 어디에서 담당하게 할까요?

A) (권장) 단일 `HttpClient` 컴포넌트가 모든 외부 요청 정책을 담당한다.

추천 사유: 요청 간격, retry, timeout, User-Agent, Proxy, secret masking은 모든 요청에 일관되게 적용돼야 합니다. 한 컴포넌트에 모아야 누락이 줄고 테스트도 단순합니다.

B) 각 scraper/parser 서비스가 직접 `httpx` 요청 옵션을 관리한다.

C) 요청 종류별로 GalleryClient, SearchClient, CommentClient, MediaClient를 완전히 분리한다.

X) 기타

[Answer]: A

### Question 5. Job 오케스트레이션 구조

검색 페이지 탐색과 게시글 worker 병렬 수집을 어떤 서비스가 조율하게 할까요?

A) (권장) `JobRunner`가 link collector와 post worker queue를 조율한다.

추천 사유: CLI가 orchestration을 직접 가지면 library/container/MCP에서 재사용하기 어렵습니다. `JobRunner`를 중심에 두면 adapter는 얇게 유지하고, link collector와 post worker의 책임도 분리할 수 있습니다.

B) CLI가 직접 link collector와 post worker를 조율한다.

C) entry point별 GallerySearchJob, IntegratedSearchJob, DirectPostJob이 각각 전체 흐름을 소유한다.

X) 기타

[Answer]: A

최신 명세 반영 메모:

- `JobRunner`는 batch 검색 수집, 심층검색, 노키워드 범위 수집, 실시간 키워드 수집, 실시간 전체 수집을 같은 queue/worker 흐름으로 조율한다.
- 심층검색은 통합 검색 gallery discovery 단계와 후보 갤러리별 keyword search 단계를 link collector 안에서 순차 처리한다.
- 노키워드 수집은 link collector가 `search_date` AJAX 응답의 `search_pos`를 시작점으로 사용한다.
- 실시간 수집은 매 반복마다 최신 목록/검색 결과를 확인하고 이미 처리한 `(gallery_id, post_number)`를 dedupe한다.

### Question 6. 저장소 경계

JSONL, 실패 기록, 이미지/디시콘 파일, checkpoint 저장을 어떻게 나눌까요?

A) (권장) `OutputWriter`, `MediaStore`, `CheckpointStore` 컴포넌트로 분리한다.

추천 사유: JSONL, media, checkpoint는 저장 시점과 실패 처리 방식이 서로 다릅니다. 다만 1차 구현부터 storage interface를 크게 만들 필요는 없으므로 concrete 컴포넌트 분리가 적당합니다.

B) `JobRunner`가 모든 파일 쓰기를 직접 담당한다.

C) 1차 구현부터 storage adapter interface를 두고 JSONL adapter를 붙인다.

X) 기타

[Answer]: C

최신 명세 반영 메모:

- 저장소 adapter는 로컬 파일, PostgreSQL checkpoint, Garage 기반 S3 호환 JSONL/미디어 출력 경로를 분리해서 설계한다.
- 1차 로컬 실행은 `Checkpoint.json`과 Job JSONL 파일을 실행 파일과 같은 위치에 저장한다.
- 단일 컨테이너 실행은 checkpoint를 PostgreSQL에, Job JSONL 파일과 다운로드 미디어를 Garage 기반 S3 호환 오브젝트 스토리지에 저장한다.
- 향후 통합 플랫폼에서는 checkpoint를 RDS, Job JSONL 파일과 미디어를 S3 호환 adapter로 확장한다.
- SeaweedFS는 대량 미디어/소파일 저장, FUSE, Iceberg 요구가 생길 때 대체 저장소로 검토한다.

### Question 7. Checkpoint 정밀도

중단점은 어느 수준까지 복원하도록 설계할까요?

A) (권장) Job 설정, 검색 위치, 완료 key 집합, 가능한 남은 link queue를 저장한다. in-flight 요청의 정확한 복원은 보장하지 않는다.

추천 사유: 중단 후 재개에 충분한 정보를 저장하면서도 worker별 in-flight 상태까지 복원하는 복잡도를 피할 수 있습니다. 이미 저장된 게시글은 dedupe로 건너뛰면 됩니다.

B) worker별 in-flight 요청까지 정확히 저장해 거의 완전한 queue 복원을 목표로 한다.

C) 검색 위치와 마지막 처리 글번호만 저장하고, 재개 시 dedupe로 중복을 피한다.

X) 기타

[Answer]: A

최신 명세 반영 메모:

- checkpoint/status는 모든 커뮤니티 스크래퍼가 공유하는 공통 스키마를 사용한다.
- 정상 진행 중에는 `status="running"`을 기록하고, 게시글 10개 처리 완료마다 저장한다.
- 수동 중단, 오류, CAPTCHA, timeout, lease 만료 시 `status="stopped"`와 `reason`을 저장한다.
- 저장 순서는 게시글 결과의 멱등 저장 완료 후 checkpoint 갱신이다.
- in-flight 요청의 완전 복원은 보장하지 않고, 완료 key dedupe로 중복 저장을 방지한다.

### Question 8. Worker container 실행 형태

1차 worker container는 어떤 실행 형태가 좋을까요?

A) (권장) one-shot Job container: 환경변수/인자/설정 파일로 Job을 받고 실행 후 종료한다.

추천 사유: 1차 범위는 로컬/단일 컨테이너입니다. 외부 queue를 가진 daemon은 통합 시스템이 구체화된 뒤 설계하는 편이 낫고, 지금은 Job 단위 실행/종료가 가장 단순합니다.

B) long-running worker daemon: 외부 queue나 API에서 Job을 받아 계속 실행한다.

C) container는 1차에서 Dockerfile만 제공하고 runtime contract는 이후로 미룬다.

X) 기타

[Answer]: A

최신 명세 반영 메모:

- 컨테이너는 `RESUME=true`, `JOB_ID=<checkpoint job_id>`, `DATABASE_URL`, S3 호환 접속 환경변수로 재개와 저장소를 주입받는다.
- 실시간 수집 컨테이너는 `DCINSIDE_REALTIME_ENABLED`, `DCINSIDE_REALTIME_MODE`, `DCINSIDE_REALTIME_KEYWORD`, `DCINSIDE_REALTIME_DURATION_SECONDS`, `DCINSIDE_REALTIME_END_AT`, `DCINSIDE_REALTIME_POLL_INTERVAL_SECONDS` 환경변수로 실행 계약을 받는다.
- `JOB_ID` 없이 재개하면 가장 최근 checkpoint를 자동 선택한다.
- 향후 SQS 기반 long-running worker는 lease 갱신과 `lease_expired` 중단 사유를 추가 설계한다.

### Question 9. MCP adapter 범위

MCP tool은 1차에서 어느 수준까지 제공할까요?

A) (권장) core 함수의 thin wrapper로 `search_gallery`, `search_integrated`, `fetch_post`, `fetch_comments`만 제공한다.

추천 사유: MCP는 CLI와 다른 로직을 가지면 유지보수가 어려워집니다. 1차에서는 core public API를 그대로 감싸고, Job 전체 실행이나 resume tool은 실제 사용 흐름이 확인된 뒤 추가하는 편이 안전합니다.

B) CLI Job 전체 실행과 checkpoint resume까지 MCP tool로 제공한다.

C) MCP는 설계만 하고 1차 코드 구현에서는 제외한다.

X) 기타

[Answer]: B

### Question 10. 설계 패턴 선호

컴포넌트 설계에서 어느 정도의 추상화를 허용할까요?

A) (권장) concrete class/function 중심으로 시작하고, adapter 경계에만 최소 protocol을 둔다.

추천 사유: 이 프로젝트는 아직 Greenfield입니다. 모든 외부 의존성을 interface로 감싸거나 plugin 구조를 전제로 설계하면 구현량이 크게 늘기 때문에, 테스트와 adapter 교체에 필요한 최소 경계만 두는 방식이 적절합니다.

B) ports/adapters 구조를 엄격히 적용해 모든 외부 의존성을 interface로 감싼다.

C) plugin 구조를 전제로 parser, storage, adapter를 모두 확장 가능하게 설계한다.

X) 기타

[Answer]: B

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 Application Design 산출물 5개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 Units Generation으로 넘어가지 않습니다.
