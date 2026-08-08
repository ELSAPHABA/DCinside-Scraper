# Functional Design 계획 - UOW-005 Job Runner And Checkpoint

이 계획은 `UOW-005 Job Runner And Checkpoint`의 기능 설계를 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-005 Job Runner And Checkpoint
- **Depends On**: UOW-001 Core Models And Config, UOW-002 HTTP Runtime Policy, UOW-003 Search And Link Collection, UOW-004 Post Detail And Content Parsing, UOW-006 Output And Storage
- **Primary Stories**: US-014, US-015
- **Scope**: `JobRunner`, sequential link collector task, `asyncio.Queue`, post worker pool, lifecycle state, cancellation/stop handling, checkpoint save ordering, resume flow, realtime loop termination, failure handoff
- **Out Of Scope**: concrete local/S3 storage implementation, parser selector logic, HTTP retry policy internals, CLI prompts, container/PostgreSQL checkpoint adapter, MCP hosting

## Functional Design 작업 체크리스트

- [x] UOW-006 Build and Test 승인 확인
- [x] UOW-005 범위 확인
- [x] UOW-001/UOW-002/UOW-003/UOW-004/UOW-006 계약 확인
- [x] Functional Design 질문 생성
- [x] Functional Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-005-job-runner-and-checkpoint/functional-design/business-logic-model.md` 생성
- [x] `aidlc-docs/construction/uow-005-job-runner-and-checkpoint/functional-design/business-rules.md` 생성
- [x] `aidlc-docs/construction/uow-005-job-runner-and-checkpoint/functional-design/domain-entities.md` 생성

## Functional Design Questions

### Question 1. JobRunner Contract

UOW-005의 `JobRunner` 공개 계약은 어떤 형태로 둘까요?

A) (권장) `JobRunner`가 검증된 `JobConfig`와 주입된 UOW-002/003/004/006 포트 또는 서비스들을 받아 `JobReport`를 반환한다. CLI/container/MCP는 후속 unit에서 같은 `JobRunner`를 호출한다.

추천 사유: JobRunner는 orchestration만 책임지고, 입력 생성과 배포 방식은 adapter가 담당하는 경계가 가장 작습니다.

B) `JobRunner`가 CLI 입력, `.env`, storage config 생성까지 모두 처리한다.

C) `run_job` public API 안에 orchestration 로직을 직접 작성하고 `JobRunner` 클래스는 만들지 않는다.

X) 기타

[Answer]: A

### Question 2. Collector And Queue Topology

링크 수집과 게시글 worker queue는 어떻게 구성할까요?

A) (권장) Job마다 단일 sequential link collector task가 `PostCandidate`를 `asyncio.Queue`에 넣고, `WorkerConfig.post_worker_count`만큼 post worker가 queue를 소비한다. direct URL Job은 collector가 URL 목록을 candidate로 변환해 같은 queue에 넣는다.

추천 사유: 검색 탐색은 순서와 `search_pos`가 중요하고, 게시글 상세 수집만 병렬화하면 차단 위험과 복잡도가 낮습니다.

B) link collector도 여러 worker로 병렬화한다.

C) queue 없이 link collection 전체를 끝낸 뒤 list를 post worker에 넘긴다.

X) 기타

[Answer]: A

### Question 3. Checkpoint Commit Ordering

체크포인트의 `completed_keys`와 last completed 위치는 언제 갱신할까요?

A) (권장) `OutputStorePort.append_post` 또는 `write_failure`가 성공한 뒤에만 해당 post key와 last completed 위치를 checkpoint에 반영한다. 결과 저장 실패 시 checkpoint를 앞으로 밀지 않는다.

추천 사유: 저장되지 않은 게시글을 완료로 표시하면 resume 시 데이터 손실이 생깁니다.

B) 게시글 fetch가 성공하면 저장 전이라도 checkpoint를 갱신한다.

C) checkpoint는 Job 종료 시에만 한 번 저장한다.

X) 기타

[Answer]: A

### Question 4. Checkpoint Save Frequency

정상 진행 중 checkpoint 저장 주기는 어떻게 둘까요?

A) (권장) 성공/실패 포함 처리 완료 post 10개마다 저장하고, 수동 중단, 오류, CAPTCHA/block, timeout, realtime 정상 종료, 일반 정상 완료 시 즉시 최종 checkpoint를 저장한다.

추천 사유: 명세의 10개 단위 저장 요구사항을 만족하면서도 중단/오류에서는 손실 구간을 줄일 수 있습니다.

B) 모든 게시글마다 checkpoint를 저장한다.

C) Job 완료 시에만 checkpoint를 저장한다.

X) 기타

[Answer]: A

### Question 5. Stop And Cancellation Handling

수동 중단과 cancellation은 어떻게 처리할까요?

A) (권장) `JobRunner`가 cancellation 또는 stop 요청을 받으면 collector를 멈추고 queue에 더 이상 넣지 않으며, 진행 중 worker는 현재 post 처리/저장 후 멈춘다. 최종 checkpoint는 `status="stopped"`, `reason="manual_stop"`으로 저장한다.

추천 사유: 처리 중 저장을 강제로 끊으면 JSONL/checkpoint 순서가 깨질 수 있습니다. 현재 post 단위까지 마무리하는 것이 안전합니다.

B) cancellation 즉시 모든 worker task를 강제 취소하고 checkpoint 저장은 생략한다.

C) 수동 중단은 지원하지 않고 프로세스 종료에 맡긴다.

X) 기타

[Answer]: A

### Question 6. CAPTCHA/Block/Error Handling

CAPTCHA, 차단, 일반 오류는 JobRunner에서 어떻게 처리할까요?

A) (권장) UOW-002의 `CaptchaDetectedError`/`BlockedResponseError`는 즉시 Job stop으로 전파하고 `reason="captcha"` 또는 `reason="error"`의 final checkpoint를 저장한다. 개별 게시글 재시도 초과/parse failure는 failure record로 저장하고 Job은 계속 진행한다.

추천 사유: CAPTCHA/차단은 요청을 계속하면 위험하지만, 개별 게시글 실패는 전체 Job을 멈출 필요가 없습니다.

B) 모든 게시글 실패가 하나라도 있으면 Job 전체를 중단한다.

C) CAPTCHA/block도 failure record만 쓰고 계속 진행한다.

X) 기타

[Answer]: A

### Question 7. Resume Flow

resume 요청은 어떤 방식으로 복원할까요?

A) (권장) `CheckpointStorePort.load(job_id)` 또는 `load_latest()`로 checkpoint를 불러오고, 저장된 `job_config_snapshot`, `search_position`, `completed_keys`, 가능한 `remaining_queue`를 사용해 새 run을 시작한다. 이미 완료된 key는 queue 투입/worker 처리 전에 건너뛴다.

추천 사유: local/컨테이너 adapter가 같은 resume 계약을 쓸 수 있고, UOW-006의 새 run JSONL 규칙과도 맞습니다.

B) checkpoint의 last completed post number만 보고 JobConfig는 사용자가 다시 입력한다.

C) resume은 후속 unit으로 미루고 UOW-005에서는 시작만 지원한다.

X) 기타

[Answer]: A

### Question 8. Realtime Termination

실시간 수집 Job의 timer/end-at 종료는 어디에서 처리할까요?

A) (권장) UOW-003은 한 cycle의 latest 후보 수집만 제공하고, UOW-005 `JobRunner`가 poll loop, `duration_seconds` 또는 `end_at` 종료 조건, dedupe, final `status="completed"` checkpoint를 처리한다.

추천 사유: 실시간 종료 조건은 lifecycle/checkpoint와 강하게 묶여 있으므로 JobRunner가 처리하는 편이 자연스럽습니다.

B) UOW-003 realtime collector가 무한 loop와 checkpoint까지 모두 처리한다.

C) 실시간 Job은 UOW-007 CLI에서만 loop로 처리한다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-005 Functional Design 산출물 3개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-005 NFR Requirements로 넘어가지 않습니다.

## 검토 결과

- 모든 답변은 A로 확정되었습니다.
- 답변 간 충돌은 없습니다.
- Q2는 Job 자체가 아니라 `PostCandidate`/게시글 링크가 queue item이라는 의미로 해석합니다.
- follow-up 질문은 필요하지 않습니다.
- 산출물 생성 후 UOW-005 Functional Design Review 단계에서 사용자 승인을 대기합니다.
