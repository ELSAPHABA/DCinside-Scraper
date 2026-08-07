# NFR Requirements 계획 - UOW-006 Output And Storage

이 계획은 `UOW-006 Output And Storage`의 비기능 요구사항과 기술 선택을 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-006 Output And Storage
- **Functional Design**: 승인됨
- **Depends On**: UOW-001 Core Models And Config
- **Primary Stories**: US-012
- **Scope**: Job JSONL output, failure JSONL output, Job report output, local media storage, S3-compatible object storage boundary, Garage default target, local `Checkpoint.json`
- **Security Focus**: path traversal prevention, secret redaction, safe failure context, `.env`/credential exclusion, local output gitignore protection
- **Resiliency Focus**: atomic checkpoint replace, append-only JSONL writes, clear storage errors, resume-safe run directories
- **PBT Focus**: path sanitization, JSONL round trip, checkpoint save/load round trip, failure redaction, object key generation
- **Out Of Scope**: worker queue lifecycle, retry scheduling, HTTP media download, PostgreSQL checkpoint adapter, CLI prompt UX, container/MCP hosting

## NFR Requirements 작업 체크리스트

- [x] UOW-006 Functional Design 승인 확인
- [x] Functional Design 산출물 확인
- [x] Security Baseline 적용 항목 확인
- [x] Resiliency Baseline 적용 항목 확인
- [x] Property-Based Testing 적용 항목 확인
- [x] NFR Requirements 질문 생성
- [x] NFR Requirements 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-006-output-and-storage/nfr-requirements/nfr-requirements.md` 생성
- [x] `aidlc-docs/construction/uow-006-output-and-storage/nfr-requirements/tech-stack-decisions.md` 생성

## NFR Requirements Questions

### Question 1. JSONL Durability Policy

`posts.jsonl`과 `failures.jsonl`의 내구성은 어느 수준으로 둘까요?

A) (권장) 각 record append 후 flush를 수행하고, OS-level fsync는 기본 비활성화 옵션으로 둔다. JobRunner가 checkpoint를 결과 저장 성공 후 갱신하므로 기본 안정성과 속도의 균형을 맞춘다.

추천 사유: 매 줄 fsync는 로컬 디스크와 네트워크 파일시스템에서 매우 느릴 수 있습니다. flush는 기본으로 두고 fsync는 사용자가 강한 내구성이 필요할 때 켜는 편이 적절합니다.

B) 각 record append마다 flush와 fsync를 항상 수행한다.

C) 파일 close 시점까지 flush하지 않는다.

X) 기타

[Answer]: A

### Question 2. Atomic Write Scope

원자적 쓰기 보장은 어디까지 적용할까요?

A) (권장) `Checkpoint.json`과 `report.json`은 temp file 후 replace로 원자적 갱신한다. JSONL은 append-only 특성상 한 줄 단위 유효성 검증으로 복구 가능하게 하고 파일 전체 replace는 하지 않는다.

추천 사유: 체크포인트/리포트는 작은 단일 문서라 atomic replace가 쉽고 효과적입니다. JSONL 전체 replace는 수집이 커질수록 비용이 커집니다.

B) 모든 JSONL append마다 전체 파일을 temp file로 다시 쓴다.

C) 어떤 파일에도 atomic replace를 적용하지 않는다.

X) 기타

[Answer]: A

### Question 3. Path And Filename Safety

경로와 파일명 안전성은 어떤 규칙을 적용할까요?

A) (권장) 모든 사용자/원격 입력 기반 path segment는 허용 문자 기반으로 sanitize하고, 최종 resolved path가 base output directory 아래인지 검증한다. 빈 파일명은 deterministic fallback을 사용한다.

추천 사유: gallery ID, post 번호, media URL filename은 외부 입력입니다. 저장소 경계에서 한 번 막는 것이 가장 작은 보안 장치입니다.

B) DCinside 값은 신뢰하고 그대로 path segment로 사용한다.

C) sanitize는 CLI adapter에서만 수행한다.

X) 기타

[Answer]: A

### Question 4. Failure Redaction Policy

실패 기록과 저장소 오류 메시지의 redaction은 어떤 기준으로 둘까요?

A) (권장) allow-list 방식을 사용한다. `proxy_host`, `user_agent`, status code, stage, retryable, post key만 허용하고 proxy ID/PW, cookie, token, raw header, raw body/html은 버린다.

추천 사유: 차단/프록시 환경에서는 민감값이 섞이기 쉽습니다. deny-list보다 allow-list가 작고 안전합니다.

B) 알려진 secret 키워드만 마스킹하고 나머지는 저장한다.

C) 디버깅 편의를 위해 원본 오류 context를 모두 저장한다.

X) 기타

[Answer]: A

### Question 5. S3-Compatible Dependency

Garage/S3-compatible 업로드 구현 의존성은 어떻게 둘까요?

A) (권장) core 기본 의존성에는 추가하지 않고 `s3` optional extra로 `boto3` 또는 `aioboto3` 계열을 둔다. UOW-006 코드 생성 시 실제 비동기 요구가 작으면 동기 `boto3`를 얇게 감싸는 방식을 우선 검토한다.

추천 사유: 로컬 JSONL만 쓰는 사용자는 S3 의존성을 설치할 필요가 없습니다. S3 서명 직접 구현은 피하는 게 맞습니다.

B) `boto3`를 기본 의존성에 추가한다.

C) S3 서명과 업로드를 직접 구현한다.

X) 기타

[Answer]: A

### Question 6. Local Checkpoint Concurrency

`Checkpoint.json` 동시 접근은 어느 수준까지 지원할까요?

A) (권장) 1차 구현은 단일 프로세스/단일 Job 쓰기를 기준으로 하고, 프로세스 내 lock과 atomic replace만 보장한다. 다중 프로세스 동시 쓰기는 PostgreSQL checkpoint adapter가 담당할 범위로 둔다.

추천 사유: 로컬 파일 lock을 플랫폼별로 완성도 있게 구현하는 것은 비용이 큽니다. 컨테이너/통합 환경의 동시성은 PostgreSQL이 맞습니다.

B) Windows/Linux 파일 lock으로 다중 프로세스 동시 쓰기를 지원한다.

C) 동시성 보호 없이 단순 write만 사용한다.

X) 기타

[Answer]: A

### Question 7. Storage Test Strategy

UOW-006 테스트는 어떤 범위를 기본 gate로 둘까요?

A) (권장) 로컬 파일 저장, JSONL round trip, media bytes 저장, checkpoint save/load/load_latest, path traversal 거부, failure redaction, S3 object key 생성은 기본 테스트로 둔다. 실제 Garage 연동은 optional smoke로 둔다.

추천 사유: 기본 테스트는 빠르고 재현 가능해야 합니다. Garage는 외부 서비스이므로 선택 실행이 적절합니다.

B) 모든 테스트에서 실제 Garage 컨테이너를 띄워 필수 검증한다.

C) 저장소 테스트는 코드 생성 이후 수동 확인만 한다.

X) 기타

[Answer]: A

### Question 8. Property-Based Test Scope

Property-Based Test는 어디에 적용할까요?

A) (권장) path segment sanitize, output key generation, JSONL serialization round trip, checkpoint document round trip, failure redaction idempotence에 적용한다. 실제 파일 I/O 대량 랜덤 테스트는 example test로 제한한다.

추천 사유: PBT는 순수 변환 규칙에 잘 맞습니다. 파일 I/O 랜덤 테스트를 과하게 늘리면 느리고 불안정해집니다.

B) 모든 파일 I/O 조합을 PBT로 생성해 검증한다.

C) UOW-006에서는 PBT를 생략한다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-006 NFR Requirements 산출물 2개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-006 NFR Design으로 넘어가지 않습니다.
