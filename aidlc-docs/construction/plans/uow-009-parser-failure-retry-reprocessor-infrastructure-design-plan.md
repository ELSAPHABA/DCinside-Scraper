# Infrastructure Design 계획 - UOW-009 Parser Failure Retry Reprocessor

이 계획은 `UOW-009 Parser Failure Retry Reprocessor`의 논리 컴포넌트를 실제 CLI/container/S3/local runtime 접점에 어떻게 매핑할지 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-009 Parser Failure Retry Reprocessor
- **Functional Design**: 승인됨
- **NFR Requirements**: 승인됨
- **NFR Design**: 승인됨
- **Scope**: `retry-failures` CLI entrypoint, local/S3 failure input refs, optional existing posts refs, option restoration inputs, existing local/container output runtime, optional S3/Garage smoke, report metadata storage
- **Likely Infrastructure Scope**: no new production service; reuse existing local filesystem, S3/Garage object storage, container env contract, and existing runner/output/checkpoint runtime
- **Out Of Scope**: new worker image, new database table, migration framework, distributed DLQ, background scheduler, production cloud provisioning, AWS CDK implementation

## Infrastructure Design 작업 체크리스트

- [x] UOW-009 Functional Design 승인 확인
- [x] UOW-009 NFR Design 승인 확인
- [x] Functional/NFR 산출물 확인
- [x] logical components의 인프라 필요 여부 분석
- [x] Infrastructure Design 질문 생성
- [x] Infrastructure Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-009-parser-failure-retry-reprocessor/infrastructure-design/infrastructure-design.md` 생성
- [x] `aidlc-docs/construction/uow-009-parser-failure-retry-reprocessor/infrastructure-design/deployment-architecture.md` 생성
- [x] shared infrastructure 산출물 필요 여부 확인

## 검토 결과

- Q1-Q5, Q7-Q10은 A로 확정되었습니다.
- Q6은 A에 `--existing-posts-root` 편의 옵션 추가로 확정되었습니다.
- `--existing-posts-root`는 local filesystem 전용으로 해석합니다. S3/Garage prefix scan은 Q5의 명시 object ref 결정에 따라 UOW-009 범위에서 제외합니다.
- 새 production infrastructure, 새 container image, 새 DB table, distributed DLQ, scheduler는 만들지 않습니다.
- shared infrastructure 산출물은 별도로 만들지 않고 UOW-009 Infrastructure Design 문서 안에 재사용 경계를 요약합니다.
- 답변 간 충돌은 없습니다.
- follow-up 질문은 필요하지 않습니다.
- 산출물 생성 후 UOW-009 Infrastructure Design Review 단계에서 사용자 승인을 대기합니다.

## Infrastructure Design Questions

### Question 1. New Infrastructure Requirement

UOW-009를 위해 새 production infrastructure를 추가할까요?

A) (권장) 추가하지 않는다. UOW-009는 기존 local filesystem, S3/Garage object storage, PostgreSQL checkpoint, container/CLI runtime을 재사용한다.

추천 사유: retry-failures는 운영 기능이지만 새 서비스가 아닙니다. 새 DB/table/queue/scheduler를 만들면 UOW-009 범위가 불필요하게 커집니다.

B) retry 전용 PostgreSQL table과 DLQ queue를 추가한다.

C) retry 전용 worker container image를 별도로 만든다.

X) 기타

[Answer]: A

### Question 2. CLI Entrypoint Exposure

`retry-failures`는 어디에 노출할까요?

A) (권장) 기존 `dcinside-scraper` console script와 `python -m dcinside_scraper.adapters.cli retry-failures`에서 같은 subcommand로 노출한다. 별도 executable은 만들지 않는다.

추천 사유: 기존 CLI 운영 방식과 도움말 구조를 유지할 수 있습니다. 같은 runtime option parsing도 재사용됩니다.

B) `dcinside-retry-failures` 별도 console script를 새로 만든다.

C) CLI에는 노출하지 않고 library API만 제공한다.

X) 기타

[Answer]: A

### Question 3. Container Runtime Mapping

컨테이너 환경에서 retry는 어떻게 실행할까요?

A) (권장) 기존 worker container 이미지와 entrypoint를 재사용하고, argv/subcommand로 `retry-failures`를 실행한다. 필요한 failure refs와 output/storage env만 런타임에 주입한다.

추천 사유: UOW-008 컨테이너는 이미 one-shot worker입니다. retry용 이미지를 새로 만들 필요가 없습니다.

B) retry 전용 컨테이너 entrypoint를 별도 module로 만든다.

C) 컨테이너에서는 retry를 지원하지 않는다.

X) 기타

[Answer]: A

### Question 4. Local Failure Input Path Boundary

local failure input path는 어떤 경계로 받을까요?

A) (권장) CLI/library에서 명시 경로만 받는다. wildcard, recursive output-root auto-discovery는 후속 기능으로 둔다.

추천 사유: 명시 경로가 가장 예측 가능합니다. 자동 탐색은 잘못된 run의 failure를 섞을 위험이 있습니다.

B) output root를 받으면 모든 하위 `failures.jsonl`을 자동 탐색한다.

C) 최신 run 하나만 자동 탐색한다.

X) 기타

[Answer]: A

### Question 5. S3/Garage Failure Input Ref Boundary

S3/Garage failure input은 어떤 URI 형식으로 받을까요?

A) (권장) 명시적인 `s3://bucket/key` object ref만 받는다. bucket listing이나 prefix scan은 하지 않는다.

추천 사유: object ref는 권한과 결과 범위가 명확합니다. prefix scan은 권한, 비용, 중복 처리 범위를 키웁니다.

B) `s3://bucket/prefix/`를 받아 내부에서 전체 listing한다.

C) S3/Garage input은 CLI에서는 받지 않고 library에서만 받는다.

X) 기타

[Answer]: A

### Question 6. Existing Posts Skip Input Boundary

기존 성공 `posts.jsonl` skip input은 어떻게 받을까요?

A) (권장) failure input과 같은 방식으로 local path 또는 `s3://bucket/key` object ref를 명시적으로 받는다. 자동 output-root scan은 하지 않는다.

추천 사유: 어떤 성공 파일로 skip할지 운영자가 명시하는 편이 안전합니다. 자동 scan은 정상 재수집이 필요한 경우까지 skip할 수 있습니다.

B) 같은 output root 아래 모든 `posts.jsonl`을 자동 탐색한다.

C) existing success skip은 local file만 지원한다.

X) 기타

[Answer]: A + `--existing-posts-root` 옵션도 추가한다.

### Question 7. Option Restore Input Boundary

`--from-report`, `--from-checkpoint` 입력은 어떤 경계로 받을까요?

A) (권장) `--from-report`는 local path 또는 `s3://bucket/key` report ref를 받고, `--from-checkpoint`는 기존 checkpoint store의 job id 또는 local checkpoint ref를 받는다. 둘은 동시에 허용하지 않는다.

추천 사유: report는 output object이고 checkpoint는 store에 있을 수 있습니다. 입력 경계를 분리하면 복원 의미가 명확합니다.

B) 둘 다 파일 경로만 받는다.

C) 둘 다 같은 `--restore-from` 옵션 하나로 받는다.

X) 기타

[Answer]: A

### Question 8. Output And Checkpoint Storage Boundary

retry run의 output/checkpoint 저장소는 어떻게 정할까요?

A) (권장) 일반 `run`과 같은 `StorageConfig`/container env 계약을 따른다. retry 결과는 새 run output으로 저장하고, checkpoint도 기존 store를 사용한다.

추천 사유: UOW-005/UOW-006 계약을 유지합니다. retry라고 별도 저장소를 만들 필요가 없습니다.

B) retry 결과는 원본 run output에 append한다.

C) retry 결과는 별도 retry-only directory/table에만 저장한다.

X) 기타

[Answer]: A

### Question 9. Optional Smoke Infrastructure

UOW-009 optional smoke 테스트는 어떤 인프라를 사용할까요?

A) (권장) 기본 테스트는 temp files/fakes만 사용한다. S3/Garage input read smoke와 live post retry smoke는 pytest marker/env flag로만 실행한다.

추천 사유: retry selection은 외부 인프라 없이 검증 가능합니다. S3/live smoke는 필요할 때만 실행해야 기본 gate가 안정적입니다.

B) 기본 테스트에서 Garage와 live DCinside retry를 항상 실행한다.

C) optional smoke 경로도 만들지 않는다.

X) 기타

[Answer]: A

### Question 10. Shared Infrastructure Artifact

UOW-009에서 shared infrastructure 산출물이 필요할까요?

A) (권장) 별도 shared infrastructure 산출물은 만들지 않는다. UOW-009는 기존 UOW-008 shared runtime/storage 경계를 재사용하며, 변경점은 UOW-009 infrastructure 문서 안에 요약한다.

추천 사유: 새 저장소나 네트워크 경계가 없습니다. 별도 shared infra 문서를 만들면 중복 문서만 늘어납니다.

B) retry 전용 shared infrastructure 문서를 새로 만든다.

C) AWS CDK/UOW-010 내용을 이 단계의 shared infra에 미리 포함한다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-009 Infrastructure Design 산출물 2개를 생성합니다.
4. shared infrastructure 산출물 필요 여부를 기록합니다.
5. 산출물 생성 후 사용자 승인 전에는 Code Generation으로 넘어가지 않습니다.
