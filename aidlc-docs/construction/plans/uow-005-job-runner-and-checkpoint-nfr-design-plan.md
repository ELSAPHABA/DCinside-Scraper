# NFR Design 계획 - UOW-005 Job Runner And Checkpoint

이 계획은 `UOW-005 Job Runner And Checkpoint`의 NFR 요구사항을 구현 패턴과 논리 컴포넌트로 구체화하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-005 Job Runner And Checkpoint
- **NFR Requirements**: 승인됨
- **Depends On**: UOW-001 Core Models And Config, UOW-002 HTTP Runtime Policy, UOW-003 Search And Link Collection, UOW-004 Post Detail And Content Parsing, UOW-006 Output And Storage
- **Scope**: `JobRunner`, `anyio` task lifecycle, `asyncio.Queue[PostCandidate]`, sequential collector, post worker pool, checkpoint coordinator, resume coordinator, realtime loop, safe structured events
- **Out Of Scope**: concrete local/S3 storage internals, parser selectors, HTTP retry policy internals, PostgreSQL checkpoint adapter, CLI prompt UX, container/MCP hosting

## NFR Design 작업 체크리스트

- [x] UOW-005 NFR Requirements 승인 확인
- [x] NFR Requirements 산출물 확인
- [x] NFR Design 질문 생성
- [x] NFR Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-005-job-runner-and-checkpoint/nfr-design/nfr-design-patterns.md` 생성
- [x] `aidlc-docs/construction/uow-005-job-runner-and-checkpoint/nfr-design/logical-components.md` 생성
- [x] Security/Resiliency/PBT compliance 확인

## NFR Design Questions

### Question 1. Runner Component Layout

UOW-005 구현 컴포넌트는 어떻게 배치할까요?

A) (권장) `runner` 패키지에 `JobRunner`, `JobRunContext`, `CheckpointCoordinator`, `StopController`, `RealtimeLoopController`를 두고, public `run_job`/`resume_job` API는 이 runner를 호출하게 한다.

추천 사유: Functional Design의 논리 컴포넌트와 직접 맞고, CLI/container/MCP adapter가 같은 runner를 재사용하기 쉽습니다.

B) `core.api` 안에 runner orchestration 로직을 모두 작성한다.

C) collector/worker/checkpoint/realtime을 각각 별도 최상위 패키지로 나눈다.

X) 기타

[Answer]: A

### Question 2. AnyIO Task Group Pattern

`anyio` task group은 어떤 범위로 사용할까요?

A) (권장) `JobRunner.run` 내부에서 하나의 task group을 열고 collector task와 worker tasks를 관리한다. cancellation/stop은 `StopController`와 task group cancel scope로 전달한다.

추천 사유: 한 Job의 task lifecycle을 한 곳에서 닫을 수 있어 task leak 테스트가 단순합니다.

B) collector와 worker마다 독립 task group을 만들고 상위에서 느슨하게 관리한다.

C) `anyio`는 timeout에만 쓰고 task 관리는 `asyncio.create_task`로 한다.

X) 기타

[Answer]: A

### Question 3. Queue Sentinel Pattern

collector 완료와 worker 종료 신호는 어떻게 전달할까요?

A) (권장) collector가 완료되면 worker 수만큼 private sentinel을 queue에 넣어 worker가 정상 종료하게 한다. stop 시에는 새 candidate 투입을 멈추고 필요한 sentinel만 넣는다.

추천 사유: queue item은 계속 `PostCandidate` 중심으로 유지하면서도 종료 경로가 명확합니다.

B) queue를 비운 뒤 worker task를 직접 cancel한다.

C) worker가 timeout polling으로 queue empty를 감지해 종료한다.

X) 기타

[Answer]: A

### Question 4. Checkpoint Coordinator Pattern

checkpoint 갱신과 저장은 어떤 컴포넌트가 담당할까요?

A) (권장) `CheckpointCoordinator`가 in-memory checkpoint draft, completed key set, 10개 단위 저장 카운터, final checkpoint 저장을 담당한다. worker는 저장 성공 이벤트만 coordinator에 알린다.

추천 사유: checkpoint-after-storage 규칙을 한 컴포넌트에서 검증할 수 있습니다.

B) 각 worker가 직접 checkpoint 객체를 수정하고 저장한다.

C) output store가 checkpoint 갱신까지 담당한다.

X) 기타

[Answer]: A

### Question 5. Resume Reconstruction Pattern

resume 시 candidate 재구성은 어떻게 처리할까요?

A) (권장) `ResumeCoordinator` 또는 `JobRunner.resume`이 checkpoint의 `job_config_snapshot`, `search_position`, `completed_keys`, 가능한 `remaining_queue`를 복원한다. queue snapshot이 없으면 collector를 다시 실행하고 completed key로 skip한다.

추천 사유: queue snapshot을 필수로 만들지 않아도 데이터 중복 저장을 막을 수 있습니다.

B) `remaining_queue`가 없으면 resume 실패로 처리한다.

C) checkpoint의 last completed post id만 사용하고 JobConfig는 사용자가 다시 입력한다.

X) 기타

[Answer]: A

### Question 6. Error Boundary Pattern

Job-level 오류와 per-post 오류는 어디에서 분기할까요?

A) (권장) worker가 UOW-002/UOW-004 오류를 분류해 CAPTCHA/block/storage failure는 Job-level stop으로 전달하고, final per-post fetch/parse failure는 `FailureRecord`로 저장 후 계속 진행한다.

추천 사유: 실패 경계를 worker 처리 흐름 가까이에 두되, stop 결정은 runner 상태로 일원화할 수 있습니다.

B) 모든 예외를 JobRunner 최상위에서 동일하게 처리한다.

C) 모든 오류를 failure record로만 저장하고 Job은 계속 진행한다.

X) 기타

[Answer]: A

### Question 7. Safe Event Pattern

safe structured event는 어떤 방식으로 만들까요?

A) (권장) 작은 `RunnerEvent`/safe dict builder를 두고 허용된 필드만 logger port로 전달한다. raw exception context dict는 그대로 넘기지 않는다.

추천 사유: 민감정보 차단은 call site마다 수동 처리하는 것보다 allow-list builder가 작고 안전합니다.

B) logger 호출마다 직접 dict를 작성하고 민감 필드를 빼기로 한다.

C) exception 객체를 그대로 logger에 전달한다.

X) 기타

[Answer]: A

### Question 8. Test Organization

UOW-005 테스트 파일은 어떻게 구성할까요?

A) (권장) 예제 async 테스트는 `tests/test_job_runner.py`, PBT는 `tests/test_job_runner_properties.py`, strategy는 `tests/strategies/job_runner.py`에 둔다. fake services는 테스트 파일 안의 작은 class로 둔다.

추천 사유: 테스트 수가 아직 크지 않으므로 별도 fixture 패키지를 만들 필요가 없습니다.

B) 모든 fake service를 `tests/fakes/` 패키지로 분리한다.

C) 모든 테스트를 하나의 큰 파일에 둔다.

X) 기타

[Answer]: A

### Question 9. Property State Model Pattern

PBT용 상태 모델은 어느 수준으로 둘까요?

A) (권장) 실제 async runner를 랜덤 실행하지 않고, checkpoint advancement, completed-key skip, report counter, stop reason mapping을 순수 함수/작은 state reducer로 검증한다.

추천 사유: PBT가 flaky async scheduling에 묶이지 않고 핵심 불변식만 빠르게 검증됩니다.

B) Hypothesis stateful testing으로 실제 async task scheduling까지 모델링한다.

C) PBT는 코드 생성 이후 필요하면 추가한다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-005 NFR Design 산출물 2개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 Infrastructure Design 또는 Code Generation으로 넘어가지 않습니다.

## 검토 결과

- 모든 답변은 A로 확정되었습니다.
- 답변 간 충돌은 없습니다.
- 별도 DLQ 컴포넌트는 UOW-005 범위에 추가하지 않고, `FailureRecord`/`failures.jsonl`을 향후 재시도 유닛의 입력으로 남기는 경계로 정리합니다.
- follow-up 질문은 필요하지 않습니다.
- 산출물 생성 후 UOW-005 NFR Design Review 단계에서 사용자 승인을 대기합니다.
