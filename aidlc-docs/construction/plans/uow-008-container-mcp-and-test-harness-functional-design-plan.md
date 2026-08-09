# Functional Design 계획 - UOW-008 Container, MCP, And Test Harness

이 계획은 `UOW-008 Container, MCP, And Test Harness`의 기능 설계를 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-008 Container, MCP, And Test Harness
- **Depends On**: UOW-001 Core Models And Config, UOW-002 HTTP Runtime Policy, UOW-003 Search And Link Collection, UOW-004 Post Detail And Content Parsing, UOW-005 Job Runner And Checkpoint, UOW-006 Output And Storage, UOW-007 CLI Adapter
- **Primary Stories**: US-013, US-018, US-019
- **Related Stories**: US-002, US-006A, US-012, US-014, US-015, US-017
- **Scope**: one-shot worker container entrypoint, container environment mapping, PostgreSQL checkpoint adapter, S3-compatible/Garage output wiring, MCP tool adapter, result quality test harness, fixture/PBT/smoke hooks
- **Out Of Scope**: scraper parsing logic, HTTP retry policy, worker queue internals, CLI wizard UX, CAPTCHA bypass, GUI/Web UI, distributed scheduler, production Kubernetes deployment

## Functional Design 작업 체크리스트

- [x] UOW-007 Build and Test 승인 확인
- [x] UOW-008 범위 확인
- [x] UOW-001~UOW-007 계약 확인
- [x] Functional Design 질문 생성
- [x] Functional Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-008-container-mcp-and-test-harness/functional-design/business-logic-model.md` 생성
- [x] `aidlc-docs/construction/uow-008-container-mcp-and-test-harness/functional-design/business-rules.md` 생성
- [x] `aidlc-docs/construction/uow-008-container-mcp-and-test-harness/functional-design/domain-entities.md` 생성

## Answer Validation Notes

- Q1-Q4 and Q6-Q10 were explicitly answered as A.
- Q5 was blank at confirmation. Because all surrounding answers selected A and Q5-A is the only option that preserves the UOW-005 "checkpoint advances only after durable storage success" contract, Q5 is treated as A.
- No follow-up question is required.

## Functional Design Questions

### Question 1. Container Entrypoint Shape

컨테이너 실행 진입점은 어떻게 둘까요?

A) (권장) `dcinside_scraper.adapters.container.main()`을 만들고, Docker entrypoint가 이 함수를 호출한다. 새 Job 설정은 UOW-007 CLI와 같은 인자 형태를 재사용하고, container 전용 저장소/재개 설정은 환경변수로 주입한다.

추천 사유: 이미 CLI에서 `JobConfig` 변환 경로를 만들었습니다. 컨테이너가 별도 설정 문법을 만들면 같은 validation을 두 번 유지해야 합니다.

B) 컨테이너는 `JOB_CONFIG_JSON` 환경변수 하나만 읽고 CLI 인자는 받지 않는다.

C) 별도 container adapter 없이 Docker entrypoint가 `dcinside-scraper` CLI를 그대로 실행한다.

X) 기타

[Answer]: A

### Question 2. Container Resume Flow

컨테이너 재개 flow는 어떻게 둘까요?

A) (권장) `RESUME=true`이면 `JOB_ID`가 있을 때 해당 checkpoint를, 없으면 PostgreSQL checkpoint store의 최신 checkpoint를 재개한다. `RESUME`이 true가 아니면 새 Job을 실행한다.

추천 사유: 기존 요구사항의 `RESUME`, `JOB_ID` 규칙과 UOW-005 `ResumeRequest(job_id=None)` 계약이 그대로 맞습니다.

B) 재개 시 항상 `JOB_ID`를 필수로 요구한다.

C) 컨테이너 재개는 UOW-008에서 제외하고 CLI resume만 지원한다.

X) 기타

[Answer]: A

### Question 3. Container Environment Variables

컨테이너가 읽을 환경변수 범위는 어디까지 둘까요?

A) (권장) 필수 저장소 env는 `DATABASE_URL`, `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`로 두고, 선택 env는 `S3_REGION`, `S3_FORCE_PATH_STYLE`, `RESUME`, `JOB_ID`, `DCINSIDE_REALTIME_*`, Proxy/User-Agent 관련 env 또는 파일 마운트로 둔다.

추천 사유: 기능명세서의 컨테이너 저장소 요구사항을 만족하면서도 Job 자체 옵션은 CLI 인자 경로로 재사용할 수 있습니다.

B) 모든 Job 옵션과 저장소 옵션을 환경변수로만 받는다.

C) 컨테이너는 `.env` 파일만 읽고 docker run 환경변수는 직접 읽지 않는다.

X) 기타

[Answer]: A

### Question 4. PostgreSQL Checkpoint Store

PostgreSQL checkpoint adapter는 어떤 구조로 둘까요?

A) (권장) `PostgresCheckpointStore`를 UOW-006 checkpoint port 구현체로 추가하고, 단일 테이블 `dcinside_checkpoints(job_id primary key, updated_at, checkpoint_json json/jsonb)`에 checkpoint 전체를 저장한다. `load_latest()`는 `updated_at desc` 기준으로 조회한다.

추천 사유: 기존 `Checkpoint` 모델을 그대로 저장하면 schema migration 범위가 작고, 컨테이너 resume 요구사항을 바로 만족합니다.

B) checkpoint 필드를 모두 PostgreSQL 컬럼으로 정규화한다.

C) UOW-008에서는 PostgreSQL adapter를 만들지 않고 local `Checkpoint.json`을 볼륨으로만 사용한다.

X) 기타

[Answer]: A

### Question 5. Garage/S3 Output Semantics

컨테이너에서 JSONL과 media를 Garage/S3 호환 저장소에 쓰는 방식은 어떻게 둘까요?

A) (권장) `S3OutputStore`를 추가해 local spool 파일을 유지하되, `append_post`/`write_failure` 성공 전에 해당 JSONL object를 S3에 업로드한다. media와 report도 저장 성공 후 `StoredObjectRef`를 반환한다.

추천 사유: S3는 append가 없으므로 구현은 단순하지 않지만, checkpoint가 저장 성공 이후에만 전진한다는 UOW-005 계약을 지키려면 저장 성공을 S3 durable write 기준으로 봐야 합니다.

B) 실행 중에는 local temp에만 쓰고 Job 종료 시 한 번에 S3로 업로드한다.

C) JSONL 대신 게시글마다 별도 JSON object를 저장한다.

X) 기타

[Answer]: A

### Question 6. MCP Tool Scope

MCP tool은 1차로 어디까지 제공할까요?

A) (권장) `search_gallery`, `search_integrated`, `fetch_post`, `fetch_comments`, `run_job`, `resume_job` 6개 tool을 제공하고, 모두 기존 core API 또는 UOW-007과 같은 builder 경로를 호출한다.

추천 사유: 요구사항의 검색/fetch tool과 UOW 계획의 Job run/resume tool을 모두 포함하면서도 새 scraping 로직을 만들지 않습니다.

B) 조회성 tool인 search/fetch만 제공하고 Job run/resume은 제외한다.

C) Job run/resume만 제공하고 search/fetch는 제외한다.

X) 기타

[Answer]: A

### Question 7. MCP Job Execution Mode

MCP의 `run_job`/`resume_job`은 어떻게 실행할까요?

A) (권장) 1차 구현은 동기식 one-shot 호출로 두고, tool 호출이 끝나면 `JobReport` JSON을 반환한다. 백그라운드 Job registry, cancel tool, progress polling은 후속 플랫폼 단계로 둔다.

추천 사유: UOW-005 JobRunner는 이미 one-shot 실행을 지원합니다. 별도 scheduler를 만들면 UOW-008 범위가 커집니다.

B) MCP 서버 내부에 background job registry를 만들고 run은 즉시 job handle을 반환한다.

C) MCP에서는 Job 실행을 금지하고 단건 fetch/search만 허용한다.

X) 기타

[Answer]: A

### Question 8. Adapter Error Shape

컨테이너와 MCP 오류 응답은 어떻게 만들까요?

A) (권장) 모든 adapter 오류는 `ErrorMapper`를 사용해 safe code/message/details로 변환한다. 컨테이너는 exit code `0/1/2`, MCP는 JSON 직렬화 가능한 error object를 반환하며 stack trace, Proxy password, raw env, raw HTTP body는 노출하지 않는다.

추천 사유: UOW-001/UOW-007에서 이미 안전 오류 매핑 경계를 사용하고 있어 재사용 비용이 가장 작습니다.

B) container와 MCP에서 원본 exception 문자열과 traceback을 그대로 반환한다.

C) 모든 오류를 하나의 `"failed"` 메시지로만 반환한다.

X) 기타

[Answer]: A

### Question 9. Result Quality Harness

수집 결과 품질 검토 하네스는 어떤 형태로 둘까요?

A) (권장) 작은 JSONL fixture와 `JobReport` fixture를 대상으로 필수 top-level 필드, repost title normalization, null/optional 구조, failure/report count를 검증한다. Polars 기반 읽기 검증은 test extra에 Polars를 추가하거나 설치 가능할 때만 실행한다.

추천 사유: 품질 검토 요구사항을 자동화하면서도 기본 테스트가 무거워지는 것을 피할 수 있습니다.

B) Polars를 런타임 필수 의존성으로 추가하고 모든 품질 테스트를 Polars로만 실행한다.

C) 품질 검토 하네스는 문서로만 남기고 자동 테스트는 만들지 않는다.

X) 기타

[Answer]: A

### Question 10. Default Test And Smoke Scope

UOW-008 기본 테스트와 선택 smoke 테스트는 어떻게 나눌까요?

A) (권장) 기본 테스트는 Docker/Garage/PostgreSQL/MCP 네트워크 없이 fake client, sqlite/임시 DB 대체 또는 mock port, static fixtures, PBT로 실행한다. Docker compose, Garage, PostgreSQL, live DCinside, MCP server smoke는 env-gated optional smoke로 둔다.

추천 사유: 기본 테스트는 빠르고 재현 가능해야 합니다. 외부 서비스가 필요한 검증은 명시적으로 켤 때만 실행하는 편이 CI와 로컬 모두 안정적입니다.

B) 기본 테스트에서 Docker compose로 PostgreSQL과 Garage를 항상 띄운다.

C) UOW-008 테스트는 수동 smoke만 수행한다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-008 Functional Design 산출물 3개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-008 NFR Requirements로 넘어가지 않습니다.
