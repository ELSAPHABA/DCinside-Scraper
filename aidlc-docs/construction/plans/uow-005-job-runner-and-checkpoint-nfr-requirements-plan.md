# NFR Requirements 계획 - UOW-005 Job Runner And Checkpoint

이 계획은 `UOW-005 Job Runner And Checkpoint`의 비기능 요구사항과 기술 선택을 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-005 Job Runner And Checkpoint
- **Functional Design**: 승인됨
- **Depends On**: UOW-001 Core Models And Config, UOW-002 HTTP Runtime Policy, UOW-003 Search And Link Collection, UOW-004 Post Detail And Content Parsing, UOW-006 Output And Storage
- **Primary Stories**: US-014, US-015
- **Scope**: `JobRunner`, sequential collector task, `asyncio.Queue[PostCandidate]`, post worker pool, checkpoint advancement, resume flow, cancellation/manual stop, CAPTCHA/block stop, realtime loop termination, `JobReport`
- **Security Focus**: safe logging, no raw proxy/cookie/header leakage, fail-closed CAPTCHA/block behavior, no raw HTML/body persistence through JobRunner failures
- **Resiliency Focus**: checkpoint-after-storage ordering, final checkpoint on all terminal paths, graceful worker shutdown, resume dedupe, bounded optional queue behavior
- **PBT Focus**: checkpoint advancement invariant, completed-key skip, report counter consistency, stop reason mapping, realtime termination condition validation
- **Out Of Scope**: concrete local/S3 storage internals, parser selectors, HTTP retry policy internals, PostgreSQL checkpoint adapter, CLI prompt UX, container/MCP hosting

## NFR Requirements 작업 체크리스트

- [x] UOW-005 Functional Design 승인 확인
- [x] Functional Design 산출물 확인
- [x] Security Baseline 적용 항목 확인
- [x] Resiliency Baseline 적용 항목 확인
- [x] Property-Based Testing 적용 항목 확인
- [x] NFR Requirements 질문 생성
- [x] NFR Requirements 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-005-job-runner-and-checkpoint/nfr-requirements/nfr-requirements.md` 생성
- [x] `aidlc-docs/construction/uow-005-job-runner-and-checkpoint/nfr-requirements/tech-stack-decisions.md` 생성

## NFR Requirements Questions

### Question 1. Async Runtime Dependency

UOW-005의 worker/collector 실행은 어떤 런타임 의존성으로 구현할까요?

A) (권장) Python 표준 `asyncio`만 사용한다. `asyncio.Queue`, task, cancellation 처리를 직접 얇게 구성하고 Celery/RQ/anyio 같은 별도 실행 프레임워크는 추가하지 않는다.

추천 사유: UOW-005는 단일 프로세스 안의 Job orchestration입니다. 외부 queue 프레임워크는 컨테이너/분산 실행 단계에서 필요해질 때 추가하는 편이 작습니다.

B) `anyio`를 추가해 task group과 cancellation scope를 사용한다.

C) Celery/RQ 같은 외부 worker queue를 UOW-005부터 도입한다.

X) 기타

[Answer]: B

### Question 2. Queue Backpressure Policy

`asyncio.Queue[PostCandidate]`의 크기와 backpressure는 어떻게 둘까요?

A) (권장) `WorkerConfig.queue_max_size`가 있으면 bounded queue로 collector를 자연스럽게 대기시키고, 값이 없으면 기존 모델 계약대로 unbounded queue를 허용한다. 기본값 변경은 하지 않는다.

추천 사유: 이미 모델 기본값이 `None`입니다. 1차 구현에서는 계약을 바꾸지 않고, 장기/대량 Job은 사용자가 queue 크기를 지정하도록 두는 것이 가장 작습니다.

B) `queue_max_size`가 없어도 내부 기본값 `post_worker_count * 20`을 강제로 적용한다.

C) 항상 unbounded queue만 사용하고 `queue_max_size`는 무시한다.

X) 기타

[Answer]: A

### Question 3. Checkpoint Durability Trigger

checkpoint 저장 트리거의 비기능 기준은 어디까지 둘까요?

A) (권장) Functional Design의 10개 완료 단위 저장을 유지하고, manual stop, CAPTCHA/block, unrecoverable error, timeout, realtime 정상 종료, 일반 완료 시 final checkpoint 저장을 필수 gate로 둔다.

추천 사유: 저장소 write 성공 후 checkpoint를 미는 규칙과 맞고, 모든 종료 경로에서 resume 가능한 상태를 남길 수 있습니다.

B) 모든 게시글 처리 후 checkpoint를 저장한다.

C) checkpoint는 Job 종료 시에만 저장한다.

X) 기타

[Answer]: A

### Question 4. Stop And Cancellation Safety

수동 중단, cancellation, fatal stop 시 worker 종료 안전성은 어디까지 요구할까요?

A) (권장) collector는 즉시 새 candidate 투입을 멈추고, worker는 현재 candidate의 저장/실패 기록을 끝낸 뒤 종료한다. 이미 시작한 storage write를 강제 취소하지 않는 것을 테스트 기준으로 둔다.

추천 사유: JSONL/checkpoint 순서가 깨지는 가장 큰 원인은 저장 중 취소입니다. post 단위 마무리 후 정지하면 구현도 단순하고 resume도 안전합니다.

B) cancellation 발생 즉시 모든 task를 강제 취소한다.

C) stop/cancellation 처리는 OS process 종료에만 맡긴다.

X) 기타

[Answer]: A

### Question 5. Resume Queue Snapshot Policy

resume을 위한 `remaining_queue` 저장은 어느 수준으로 요구할까요?

A) (권장) cheap하게 snapshot 가능한 queue만 저장한다. snapshot이 없거나 불완전해도 `search_position`과 `completed_keys`로 재탐색하며 완료 key를 skip하는 것을 정상 resume 경로로 둔다.

추천 사유: queue 전체를 완벽히 직렬화하려고 하면 구현이 커집니다. 완료 key skip이 있으면 재탐색 비용은 있어도 데이터 중복 저장은 피할 수 있습니다.

B) 모든 stop 시점에 queue 전체를 반드시 완전 저장한다.

C) `remaining_queue`는 사용하지 않고 항상 처음부터 재탐색한다.

X) 기타

[Answer]: A

### Question 6. Safe Observability

JobRunner logging/reporting의 관측성 범위는 어디까지 둘까요?

A) (권장) job start/end, collector cycle, candidate queued/skipped, worker success/failure, checkpoint save, stop reason, realtime termination을 safe structured event로 남긴다. proxy credential, cookie, raw header, raw HTML/body는 남기지 않는다.

추천 사유: 운영 중 진행률과 중단 원인은 필요하지만, 민감값과 대용량 원문은 JobRunner가 보관할 이유가 없습니다.

B) 디버깅 편의를 위해 요청 URL, header, raw failure body를 모두 로그에 남긴다.

C) UOW-005에서는 logging을 하지 않는다.

X) 기타

[Answer]: A

### Question 7. Error Isolation Policy

개별 게시글 실패와 Job 전체 실패의 경계는 어떻게 검증할까요?

A) (권장) CAPTCHA/block/storage failure 같은 Job-level 위험은 Job을 멈추고 final checkpoint를 저장한다. 개별 fetch/parse 실패는 failure record 저장 후 계속 진행한다. 이 경계를 unit test로 검증한다.

추천 사유: 차단 위험은 fail-closed가 맞고, 개별 게시글 오류는 전체 Job을 멈추면 수집 효율이 떨어집니다.

B) 어떤 게시글 실패든 전체 Job을 멈춘다.

C) CAPTCHA/block도 failure record만 쓰고 계속 진행한다.

X) 기타

[Answer]: A

### Question 8. Test Strategy

UOW-005 테스트는 어떤 범위를 기본 gate로 둘까요?

A) (권장) fake collector, fake post detail service, fake output store, fake checkpoint store로 async unit test를 구성한다. live DCinside 요청과 실제 Garage/PostgreSQL 연동은 기본 gate에서 제외한다.

추천 사유: JobRunner의 핵심은 orchestration 순서입니다. 외부 네트워크와 실제 저장소를 붙이면 테스트가 느리고 불안정해집니다.

B) 모든 테스트에서 실제 DCinside와 실제 파일/S3 저장소를 사용한다.

C) 테스트는 smoke 수준으로만 둔다.

X) 기타

[Answer]: A

### Question 9. Property-Based Test Targets

Property-Based Test는 어디에 적용할까요?

A) (권장) checkpoint advancement invariant, completed-key skip/idempotence, report counter consistency, stop reason mapping, realtime termination condition에 적용한다. 실제 async task scheduling 랜덤화는 example test로 제한한다.

추천 사유: PBT는 순수 상태 전이와 카운터 불변식에 잘 맞습니다. 실제 task scheduling을 랜덤으로 흔들면 flaky test가 되기 쉽습니다.

B) async task scheduling과 cancellation 타이밍까지 전부 PBT로 랜덤 생성한다.

C) UOW-005에서는 PBT를 생략한다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-005 NFR Requirements 산출물 2개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-005 NFR Design으로 넘어가지 않습니다.

## 검토 결과

- Q1은 B로 확정되었습니다.
- Q2-Q9는 A로 확정되었습니다.
- Q1과 Q2는 `anyio`가 task group/cancellation을 담당하고, candidate queue 계약은 `asyncio.Queue[PostCandidate]`로 유지하는 방식으로 해석합니다.
- 답변 간 충돌은 없습니다.
- follow-up 질문은 필요하지 않습니다.
- 산출물 생성 후 UOW-005 NFR Requirements Review 단계에서 사용자 승인을 대기합니다.
