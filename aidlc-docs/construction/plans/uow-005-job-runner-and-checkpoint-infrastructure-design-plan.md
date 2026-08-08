# Infrastructure Design 계획 - UOW-005 Job Runner And Checkpoint

이 계획은 `UOW-005 Job Runner And Checkpoint`의 runner 논리 컴포넌트를 실제 실행/검증 인프라 접점에 어떻게 매핑할지 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-005 Job Runner And Checkpoint
- **Functional Design**: 승인됨
- **NFR Requirements**: 승인됨
- **NFR Design**: 승인됨
- **Scope**: import 가능한 JobRunner library, in-process async worker orchestration, injected UOW-002/003/004/006 ports, checkpoint/output port usage, fake-service test infrastructure, `anyio` runtime dependency
- **Likely Infrastructure Scope**: standalone service 없음, external queue 없음, concrete storage/network/container infrastructure 없음
- **Out Of Scope**: CLI signal handling, Docker worker container, PostgreSQL checkpoint adapter, Garage provisioning, MCP hosting, distributed worker queue, live DCinside smoke infrastructure

## Infrastructure Design 작업 체크리스트

- [x] UOW-005 Functional Design 승인 확인
- [x] UOW-005 NFR Design 승인 확인
- [x] Functional/NFR 산출물 확인
- [x] logical components의 인프라 필요 여부 분석
- [x] Infrastructure Design 질문 생성
- [x] Infrastructure Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-005-job-runner-and-checkpoint/infrastructure-design/infrastructure-design.md` 생성
- [x] `aidlc-docs/construction/uow-005-job-runner-and-checkpoint/infrastructure-design/deployment-architecture.md` 생성
- [x] shared infrastructure 산출물 필요 여부 확인

## Infrastructure Design Questions

### Question 1. Deployment Environment

UOW-005 자체를 배포 가능한 런타임으로 볼까요?

A) (권장) 아니요. UOW-005는 import 가능한 runner library이며, 독립 서비스/컨테이너 배포는 N/A로 문서화한다. CLI/container/MCP는 후속 adapter unit에서 같은 `JobRunner`를 호출한다.

추천 사유: 이 unit은 orchestration 코드입니다. 배포 단위를 지금 만들면 CLI, container, MCP 책임까지 섞입니다.

B) UOW-005를 local worker process로 보고 실행 스크립트까지 포함한다.

C) UOW-005에서 Docker worker container 배포까지 확정한다.

X) 기타

[Answer]: A

### Question 2. Worker Execution Boundary

post worker 병렬 실행은 어떤 인프라 경계로 둘까요?

A) (권장) 단일 Python 프로세스 안의 `anyio` task group과 `asyncio.Queue[PostCandidate]`로 제한한다. 멀티프로세스/분산 queue는 후속 container/platform unit으로 둔다.

추천 사유: 현재 요구는 한 Job 안의 비동기 병렬 처리입니다. 외부 queue는 운영 구조가 필요할 때 추가하는 편이 작습니다.

B) Python `multiprocessing` 기반 worker pool을 UOW-005에서 도입한다.

C) Redis/Celery/RQ 같은 외부 queue를 UOW-005에서 도입한다.

X) 기타

[Answer]: A

### Question 3. Runtime Configuration Source

JobRunner 실행 설정은 어디에서 주입받을까요?

A) (권장) 이미 검증된 `JobConfig`, `WorkerConfig`, storage/checkpoint/output/http/parser port 객체를 호출자가 주입한다. `.env`, CLI 입력, Docker env parsing은 UOW-005 밖 adapter 책임으로 둔다.

추천 사유: library로 import할 때 환경 읽기가 숨어 있으면 테스트와 재사용이 어려워집니다.

B) UOW-005가 `.env`와 환경변수를 직접 읽어 runner config를 만든다.

C) UOW-005가 터미널 입력까지 직접 처리한다.

X) 기타

[Answer]: A

### Question 4. Checkpoint Infrastructure Boundary

checkpoint 저장 인프라는 UOW-005에서 어디까지 다룰까요?

A) (권장) UOW-005는 `CheckpointStorePort`만 호출한다. local `Checkpoint.json`과 future PostgreSQL adapter 구현은 각각 UOW-006/후속 adapter unit 책임으로 둔다.

추천 사유: JobRunner는 checkpoint를 언제 저장할지만 알아야 하고, 어디에 저장하는지는 port 구현 책임입니다.

B) UOW-005가 local `Checkpoint.json` 파일 구현을 직접 포함한다.

C) UOW-005에서 PostgreSQL checkpoint adapter까지 구현한다.

X) 기타

[Answer]: A

### Question 5. Output Infrastructure Boundary

게시글/실패/report output 인프라는 UOW-005에서 어디까지 다룰까요?

A) (권장) UOW-005는 `OutputStorePort`를 호출해 성공/실패/report를 저장한다. local JSONL, Garage/S3, media path 구성은 UOW-006 또는 후속 storage adapter 책임으로 둔다.

추천 사유: UOW-005의 핵심은 저장 순서와 checkpoint commit ordering입니다. 저장 구현을 섞지 않는 편이 안전합니다.

B) UOW-005가 `posts.jsonl`/`failures.jsonl` 직접 쓰기를 구현한다.

C) UOW-005가 Garage/S3 upload까지 직접 구현한다.

X) 기타

[Answer]: A

### Question 6. Observability Infrastructure

JobRunner 관측성은 어떤 인프라 접점으로 둘까요?

A) (권장) UOW-005는 safe event를 `LoggerPort`로만 전달한다. 외부 telemetry, metrics backend, log collector 설정은 후속 운영/adapter unit에서 다룬다.

추천 사유: 지금 필요한 것은 safe event boundary입니다. 실제 수집 backend는 배포 환경에 따라 달라집니다.

B) UOW-005에서 OpenTelemetry exporter 설정까지 포함한다.

C) UOW-005에서 파일 로그 경로와 rotation까지 직접 관리한다.

X) 기타

[Answer]: A

### Question 7. Test Infrastructure

UOW-005 기본 검증 인프라는 어떻게 구성할까요?

A) (권장) fake collector/detail/output/checkpoint/logger/clock으로만 default tests를 구성한다. live DCinside, Garage/S3, PostgreSQL, proxy는 기본 gate에서 제외한다.

추천 사유: runner의 인프라 의존성을 port로 끊었는지 가장 빠르게 검증할 수 있습니다.

B) 기본 테스트에서 실제 local output store와 live DCinside를 사용한다.

C) 기본 테스트에서 Docker Compose로 Garage/PostgreSQL까지 띄운다.

X) 기타

[Answer]: A

### Question 8. Shared Infrastructure Artifact

UOW-005에서 shared infrastructure 산출물이 필요할까요?

A) (권장) 필요하지 않다. UOW-005는 standalone infra가 없는 in-process runner이고, shared Docker/Garage/PostgreSQL/MCP 인프라는 후속 platform/container unit에서 작성한다.

추천 사유: 지금 shared infra를 만들면 아직 코드 생성 전인 worker container와 adapter 요구사항을 추측하게 됩니다.

B) worker container만 shared infrastructure 산출물로 지금 만든다.

C) Garage, PostgreSQL, worker container, MCP gateway 전체 shared infrastructure를 지금 만든다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-005 Infrastructure Design 산출물 2개를 생성합니다.
4. shared infrastructure 산출물 필요 여부를 기록합니다.
5. 산출물 생성 후 사용자 승인 전에는 Code Generation으로 넘어가지 않습니다.

## 검토 결과

- 모든 답변은 A로 확정되었습니다.
- 답변 간 충돌은 없습니다.
- follow-up 질문은 필요하지 않습니다.
- shared infrastructure 산출물은 필요하지 않습니다.
- 산출물 생성 후 UOW-005 Infrastructure Design Review 단계에서 사용자 승인을 대기합니다.
