# Infrastructure Design 계획 - UOW-006 Output And Storage

이 계획은 `UOW-006 Output And Storage`의 논리 저장 컴포넌트를 실제 실행/검증 인프라 접점에 어떻게 매핑할지 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-006 Output And Storage
- **Functional Design**: 승인됨
- **NFR Requirements**: 승인됨
- **NFR Design**: 승인됨
- **Scope**: local JSONL/report/media/checkpoint file layout, output base directory, path containment, optional S3-compatible object storage boundary, optional Garage smoke env contract
- **Likely Infrastructure Scope**: standalone service 없음, local filesystem과 optional S3-compatible object store 접점만 해당
- **Out Of Scope**: JobRunner orchestration, HTTP media download, PostgreSQL checkpoint adapter, container Garage provisioning, CLI prompt UX, MCP hosting

## Infrastructure Design 작업 체크리스트

- [x] UOW-006 Functional Design 승인 확인
- [x] UOW-006 NFR Design 승인 확인
- [x] Functional/NFR 산출물 확인
- [x] logical components의 인프라 필요 여부 분석
- [x] Infrastructure Design 질문 생성
- [x] Infrastructure Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-006-output-and-storage/infrastructure-design/infrastructure-design.md` 생성
- [x] `aidlc-docs/construction/uow-006-output-and-storage/infrastructure-design/deployment-architecture.md` 생성
- [x] shared infrastructure 산출물 필요 여부 확인

## Infrastructure Design Questions

### Question 1. Deployment Environment

UOW-006 자체를 배포 가능한 런타임으로 볼까요?

A) (권장) 아니요. UOW-006은 import 가능한 storage library이며, 독립 서비스/컨테이너 배포는 N/A로 문서화한다. 실제 worker container와 Garage/PostgreSQL 배포는 후속 adapter/container unit에서 다룬다.

추천 사유: 이 unit은 저장 포트 구현입니다. 배포 가능한 프로세스가 아니므로 인프라는 파일시스템/S3 접점만 잡는 편이 작고 명확합니다.

B) local 개발/검증용 파일 저장 환경만 Infrastructure Design에 포함한다.

C) Garage, PostgreSQL, worker container compose 배포까지 UOW-006에서 확정한다.

X) 기타

[Answer]: A

### Question 2. Local Output Base Directory

로컬 출력 기준 디렉터리는 어떻게 정할까요?

A) (권장) `StorageConfig.base_output_path`가 있으면 그 값을 사용하고, 없으면 현재 작업 디렉터리를 기준으로 `outputs/`와 `Checkpoint.json`을 둔다. 생성 경로는 base directory 하위인지 검증한다.

추천 사유: CLI/라이브러리/테스트에서 같은 규칙을 쓸 수 있고, 실행 파일 옆 저장 요구사항도 만족합니다.

B) 항상 사용자 홈 디렉터리 아래 고정 경로를 사용한다.

C) 항상 프로젝트 루트 아래에 저장한다.

X) 기타

[Answer]: A

### Question 3. Generated Local Files And Git Ignore

로컬 생성 파일은 버전 관리 관점에서 어떻게 다룰까요?

A) (권장) `outputs/`, `Checkpoint.json`, 다운로드 미디어, `.env`, S3 credential 관련 파일은 `.gitignore` 보호 대상으로 둔다. UOW-006은 파일을 만들 수 있지만 git 추적은 하지 않는다.

추천 사유: 수집 결과와 credential이 실수로 커밋되는 것을 막아야 합니다.

B) `outputs/`만 ignore하고 `Checkpoint.json`은 추적한다.

C) 사용자가 알아서 제외하도록 문서화만 한다.

X) 기타

[Answer]: A

### Question 4. S3-Compatible Runtime Boundary

S3/Garage 접속 정보는 어디에서 주입받을까요?

A) (권장) UOW-006은 validated `StorageConfig.s3`와 adapter가 주입한 credential/provider를 받는다. `.env` 직접 읽기와 docker env parsing은 CLI/container unit 책임으로 둔다.

추천 사유: storage library가 실행 환경을 직접 읽으면 import API와 테스트가 무거워집니다. 실행 환경별 입력은 adapter가 처리하는 편이 맞습니다.

B) UOW-006이 `.env`와 환경변수를 직접 읽어 S3 config를 만든다.

C) S3 credential을 `Checkpoint.json`에 저장해 재사용한다.

X) 기타

[Answer]: A

### Question 5. S3 Object Namespace

S3-compatible object key namespace는 어떻게 구성할까요?

A) (권장) `<prefix>/outputs/<job_id>/<run_id>/...`로 local relative layout을 그대로 미러링한다. prefix는 선택값이고, 없으면 `outputs/<job_id>/<run_id>/...`부터 시작한다.

추천 사유: local과 S3 결과 구조가 같으면 테스트, 재개, 후처리 경로가 단순합니다.

B) S3에서는 bucket root에 `posts.jsonl`만 둔다.

C) S3 object key는 날짜 기준으로만 나눈다.

X) 기타

[Answer]: A

### Question 6. Local Checkpoint Infrastructure

로컬 `Checkpoint.json` 인프라 경계는 어떻게 둘까요?

A) (권장) 단일 프로세스 local 실행을 대상으로 base directory의 `Checkpoint.json` 하나를 사용한다. 다중 프로세스/컨테이너 공유 checkpoint는 PostgreSQL adapter로 넘긴다.

추천 사유: 파일 기반 다중 프로세스 lock을 여기서 완성하려면 복잡해집니다. 컨테이너 공유 상태는 DB가 맞습니다.

B) 파일 lock으로 다중 프로세스 checkpoint 공유까지 지원한다.

C) checkpoint는 UOW-006에서 제외한다.

X) 기타

[Answer]: A

### Question 7. Optional Garage Smoke Infrastructure

Garage/S3 smoke test 실행 환경은 어떻게 문서화할까요?

A) (권장) `DCINSIDE_S3_SMOKE_ENABLED=true`이고 endpoint, bucket, access key, secret key env가 모두 있을 때만 실행한다. 기본 pytest/CI에서는 skip한다.

추천 사유: 외부 서비스 의존 테스트를 기본 gate에서 분리하면서도 호환성 확인 경로는 유지할 수 있습니다.

B) 모든 CI에서 Garage smoke를 필수 실행한다.

C) S3/Garage smoke 환경은 문서화하지 않는다.

X) 기타

[Answer]: A

### Question 8. Shared Infrastructure Artifact

UOW-006에서 shared infrastructure 산출물이 필요할까요?

A) (권장) 필요하지 않다. UOW-006은 storage port와 optional S3 client boundary만 다루고, 실제 Garage/PostgreSQL/container compose 배포 문서는 UOW-008에서 작성한다.

추천 사유: 지금 shared infra를 만들면 아직 없는 container/JobRunner 요구사항까지 추측하게 됩니다.

B) Garage 단독 배포 문서를 지금 shared infrastructure로 만든다.

C) Garage, PostgreSQL, worker container를 포함한 전체 compose 문서를 지금 만든다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-006 Infrastructure Design 산출물 2개를 생성합니다.
4. shared infrastructure 산출물 필요 여부를 기록합니다.
5. 산출물 생성 후 사용자 승인 전에는 Code Generation으로 넘어가지 않습니다.

## 검토 결과

- 모든 답변은 A로 확정되었습니다.
- 답변 간 충돌은 없습니다.
- follow-up 질문은 필요하지 않습니다.
- shared infrastructure 산출물은 필요하지 않습니다.
- 산출물 생성 후 UOW-006 Infrastructure Design Review 단계에서 사용자 승인을 대기합니다.
