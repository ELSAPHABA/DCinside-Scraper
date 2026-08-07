# Functional Design 계획 - UOW-006 Output And Storage

이 계획은 `UOW-006 Output And Storage`의 기능 설계를 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-006 Output And Storage
- **Depends On**: UOW-001 Core Models And Config
- **Primary Stories**: US-012
- **Scope**: Job JSONL output, failure records, Job report files, local media storage, S3-compatible output/media port, Garage default object storage boundary, local checkpoint store
- **Out Of Scope**: link collection, post detail parsing, worker queue lifecycle, retry scheduling, CAPTCHA stop orchestration, CLI prompts, PostgreSQL checkpoint adapter, container/MCP hosting

## Functional Design 작업 체크리스트

- [x] UOW-004 Build and Test 승인 확인
- [x] UOW-006 범위 확인
- [x] `requirements.md`의 JSONL, Garage, checkpoint, failure record 요구사항 확인
- [x] Functional Design 질문 생성
- [x] Functional Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-006-output-and-storage/functional-design/business-logic-model.md` 생성
- [x] `aidlc-docs/construction/uow-006-output-and-storage/functional-design/business-rules.md` 생성
- [x] `aidlc-docs/construction/uow-006-output-and-storage/functional-design/domain-entities.md` 생성

## Functional Design Questions

### Question 1. Output Store Contract

UOW-006의 결과 저장 API는 어떤 형태로 둘까요?

A) (권장) `OutputStore`가 `PostResult`, `FailureRecord`, `JobReport` 저장 메서드를 제공하고, 저장 성공 시 `StoredObjectRef`를 반환한다. Job 실행 순서, retry, checkpoint commit 호출 시점은 UOW-005가 담당한다.

추천 사유: 저장소는 저장만 책임지고, 워커/체크포인트 순서는 JobRunner가 책임지는 경계가 가장 작고 명확합니다.

B) `OutputStore`가 JobRunner처럼 post 처리 순서와 checkpoint 갱신까지 직접 관리한다.

C) JSONL 파일 writer 함수만 만들고 failure/report/media는 후속 unit으로 미룬다.

X) 기타

[Answer]: A

### Question 2. JSONL File Naming And Resume

Job JSONL 파일 이름과 resume 시 파일 생성 규칙은 어떻게 둘까요?

A) (권장) `outputs/<job_id>/<run_id>/posts.jsonl`을 기본으로 만들고, resume은 같은 `job_id` 아래 새 `run_id` 디렉터리의 새 `posts.jsonl`에 기록한다.

추천 사유: "Job당 결과"와 "resume 시 기존 JSONL에 이어 쓰지 않음"을 동시에 만족합니다. 파일 충돌도 피할 수 있습니다.

B) 실행 파일 옆에 `<job_id>.jsonl` 하나만 만들고 resume 때도 같은 파일에 append한다.

C) 게시글마다 별도 JSON 파일을 만든다.

X) 기타

[Answer]: A

### Question 3. JSON Serialization Shape

`PostResult`를 JSONL 한 줄로 직렬화할 때 어떤 규칙을 적용할까요?

A) (권장) Pydantic `model_dump(mode="json")` 기반으로 top-level scalar와 nested `content`, `media`, `comments` 구조를 그대로 저장하고, 선택 필드는 `null`을 유지한다. Polars 가공용 공통 스키마 정규화는 후속 플랫폼 단계 참고사항으로 둔다.

추천 사유: 현재 스크래퍼는 원자료 보존이 우선입니다. Polars는 nested struct/list를 읽을 수 있고, 댓글 별도 테이블 분리는 후속 정규화 단계가 더 적절합니다.

B) 저장 시점에 게시글, 댓글, 미디어를 각각 별도 JSONL 파일로 분리한다.

C) 본문과 댓글을 문자열로 합쳐 flat JSON만 저장한다.

X) 기타

[Answer]: A

### Question 4. Media Storage Contract

이미지, 디시콘, DC video 등 미디어 파일 저장은 어디까지 UOW-006에서 담당할까요?

A) (권장) UOW-006은 이미 다운로드된 bytes 또는 stream을 받아 `media/<job_id>/<gallery_id>/<post_no>/<media_type>/<filename>`에 저장하고 `StoredMediaRef`를 반환한다. HTTP 다운로드 여부와 대상 선택은 UOW-005/adapter 옵션이 결정한다.

추천 사유: 저장소가 HTTP를 알면 UOW-002 정책과 책임이 섞입니다. 저장소는 bytes를 저장하는 쪽이 단순합니다.

B) UOW-006이 URL을 받아 직접 HTTP 다운로드까지 수행한다.

C) 1차 구현에서는 미디어 저장을 제외하고 URL만 JSONL에 남긴다.

X) 기타

[Answer]: A

### Question 5. Failure Records And Reports

실패 기록과 Job report는 어떻게 저장할까요?

A) (권장) 같은 `outputs/<job_id>/<run_id>/` 아래 `failures.jsonl`과 `report.json`을 둔다. 실패 기록은 safe reason만 포함하고 raw HTML, cookie, proxy credential, token은 저장하지 않는다.

추천 사유: 성공/실패/요약을 한 run 디렉터리에 두면 수집 결과 검토와 재시도가 쉽고, 보안 요구사항도 지킬 수 있습니다.

B) 실패 기록을 `posts.jsonl` 안에 성공 결과와 섞어 저장한다.

C) 실패 기록은 로그에만 남기고 파일로 저장하지 않는다.

X) 기타

[Answer]: A, 실패 기록에 proxy host, user-agent도 저장한다.

### Question 6. Local Checkpoint Store

로컬 `Checkpoint.json`은 어떤 구조로 저장할까요?

A) (권장) 실행 기준 디렉터리에 `Checkpoint.json` 하나를 두고, 내부에는 `checkpoints` 배열 또는 map으로 여러 `job_id`의 최신 checkpoint를 저장한다. 쓰기는 임시 파일 작성 후 atomic replace로 처리한다.

추천 사유: 요구사항의 `Checkpoint.json` 파일명을 유지하면서도 여러 Job과 "가장 최근 checkpoint" 조회를 지원할 수 있습니다.

B) Job마다 `Checkpoint-<job_id>.json` 파일을 만든다.

C) 항상 단일 checkpoint만 저장하고 이전 Job checkpoint는 덮어쓴다.

X) 기타

[Answer]: A

### Question 7. Garage/S3-Compatible Storage

Garage 기반 S3 호환 저장소는 어떤 경계로 구현할까요?

A) (권장) `S3ObjectStore`는 S3-compatible port 구현으로 두고, endpoint/bucket/credentials/region은 config로 받는다. Garage 전용 코드는 넣지 않고, boto3 계열 의존성은 S3 extra 또는 해당 unit의 명시 의존성으로 추가한다.

추천 사유: Garage와 SeaweedFS 모두 S3 호환 경계로 유지할 수 있습니다. S3 서명을 직접 구현하는 것은 유지보수 비용이 큽니다.

B) Garage HTTP API에 직접 맞춘 전용 클라이언트를 만든다.

C) UOW-006에서는 S3 port만 정의하고 구현은 UOW-008로 미룬다.

X) 기타

[Answer]: A

### Question 8. Idempotency Boundary

중복 저장 방지는 어디에서 처리할까요?

A) (권장) UOW-006은 append-only 저장소로 두고, `(site_id, board_id, post_id)` 중복 여부 판단은 UOW-005 checkpoint/completed key가 담당한다. 단, 저장된 JSONL record에는 중복 판정에 필요한 key를 항상 포함한다.

추천 사유: JSONL append 저장소가 파일 전체를 매번 스캔해 dedupe하면 느리고 복잡합니다. 중복 방지는 JobRunner 상태에서 처리하는 편이 작습니다.

B) `OutputStore`가 JSONL 파일을 읽어 이미 저장된 post key를 검사한 뒤 append한다.

C) 중복 저장은 허용하고 후처리에서 제거한다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-006 Functional Design 산출물 3개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-006 NFR Requirements로 넘어가지 않습니다.
