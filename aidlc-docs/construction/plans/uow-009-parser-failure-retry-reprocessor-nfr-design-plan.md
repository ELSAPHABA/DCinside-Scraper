# NFR Design 계획 - UOW-009 Parser Failure Retry Reprocessor

이 계획은 `UOW-009 Parser Failure Retry Reprocessor`의 NFR 요구사항을 구현 패턴과 논리 컴포넌트로 구체화하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-009 Parser Failure Retry Reprocessor
- **NFR Requirements**: 승인됨
- **Depends On**: UOW-001 Core Models And Config, UOW-004 Post Detail And Content Parsing, UOW-005 Job Runner And Checkpoint, UOW-006 Output And Storage, UOW-007 CLI Adapter, UOW-008 Container, MCP, And Test Harness
- **Scope**: retry service layout, input ref resolution, streaming JSONL selection, fakeable S3/Garage reads, direct-post retry assembly, option restoration, report metadata, safe CLI summary, default tests and PBT
- **Out Of Scope**: distributed DLQ, background scheduler, CAPTCHA bypass, parser selector changes, new S3 SDK, SQLite staging, production infrastructure changes

## NFR Design 작업 체크리스트

- [x] UOW-009 NFR Requirements 승인 확인
- [x] NFR Requirements 산출물 확인
- [x] NFR Design 질문 생성
- [x] NFR Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-009-parser-failure-retry-reprocessor/nfr-design/nfr-design-patterns.md` 생성
- [x] `aidlc-docs/construction/uow-009-parser-failure-retry-reprocessor/nfr-design/logical-components.md` 생성
- [x] Security/Resiliency/PBT compliance 확인

## 검토 결과

- Q1-Q10은 모두 A로 확정되었습니다.
- 답변 간 충돌은 없습니다.
- follow-up 질문은 필요하지 않습니다.
- 산출물 생성 후 UOW-009 NFR Design Review 단계에서 사용자 승인을 대기합니다.

## NFR Design Questions

### Question 1. Module Layout

UOW-009 구현 파일은 어떻게 나눌까요?

A) (권장) `src/dcinside_scraper/retry/parser_failures.py`에 service/selector/input reader를 두고, CLI는 기존 `adapters/cli.py`에 `retry-failures` subcommand만 추가한다. 테스트는 `tests/test_parser_failure_retry.py`와 property test 파일 정도로 둔다.

추천 사유: 기능이 작고 기존 CLI adapter를 재사용합니다. 하위 패키지를 여러 개 만들면 현재 범위보다 구조가 커집니다.

B) `src/dcinside_scraper/retry/` 하위에 `service.py`, `selector.py`, `readers.py`, `reports.py`, `cli.py`를 모두 분리한다.

C) 기존 `runner/core.py` 안에 retry selector까지 넣는다.

X) 기타

[Answer]: A

### Question 2. Input Reader Boundary

local/S3 failure input reader는 어떤 경계로 만들까요?

A) (권장) `FailureInputReader` 프로토콜과 `LocalFailureInputReader`, `S3FailureInputReader`의 작은 구현을 둔다. service는 line iterator만 받아 selection을 수행한다.

추천 사유: S3는 optional extra라 fake로 대체하기 쉬워야 합니다. service를 파일/S3 구현에서 분리하면 테스트가 작아집니다.

B) service 안에서 path/URI 종류를 직접 분기해 파일과 S3를 모두 읽는다.

C) S3 input은 CLI에서 임시 파일로 다운로드한 뒤 service에는 local path만 넘긴다.

X) 기타

[Answer]: A

### Question 3. Streaming Selector Pattern

failure selection은 어떤 구현 패턴으로 둘까요?

A) (권장) line iterator를 받아 `RetrySelectionSummary`와 deduped `RetryCandidate` list를 반환하는 순수 함수/작은 클래스로 둔다. invalid/ineligible raw line은 보관하지 않고 카운터만 올린다.

추천 사유: 핵심 로직이 I/O 없이 테스트 가능해지고, PBT 적용이 쉽습니다.

B) selection 중간 결과를 모두 dataclass list로 보관한 뒤 마지막에 필터링한다.

C) selection과 Job 실행을 한 함수에서 처리한다.

X) 기타

[Answer]: A

### Question 4. Existing Success Index Pattern

기존 성공 `posts.jsonl` skip index는 어떻게 만들까요?

A) (권장) 성공 JSONL도 streaming으로 읽고 `(site_id, gallery_id, post_id)` set만 유지한다. invalid post line은 카운터만 올리고 skip index에는 넣지 않는다.

추천 사유: 전체 post body를 메모리에 둘 필요가 없습니다. skip에는 key만 필요합니다.

B) 기존 posts 전체를 Pydantic `PostResult` list로 모두 로드한다.

C) 기존 성공 skip은 CLI adapter에서만 처리하고 service에서는 모르게 한다.

X) 기타

[Answer]: A

### Question 5. Option Restoration Pattern

`--from-report`/`--from-checkpoint` 옵션 복원은 어디에서 처리할까요?

A) (권장) CLI/API request builder 단계에서 allowlist된 설정만 복원해 `ParserFailureRetryRequest`를 완성한다. service는 이미 확정된 request만 받는다.

추천 사유: 복원은 입력 편의 기능입니다. service 내부는 재처리 로직에 집중하는 편이 작고 명확합니다.

B) service가 report/checkpoint ref를 직접 읽어 복원한다.

C) 복원 옵션마다 별도 service class를 만든다.

X) 기타

[Answer]: A

### Question 6. Report Metadata Pattern

retry counters를 기존 `JobReport`에 어떻게 담을까요?

A) (권장) `JobReport`에 `metadata: dict[str, Any] = Field(default_factory=dict)` 같은 optional field를 추가하고, retry counters는 `metadata["parser_failure_retry"]` 아래에 넣는다.

추천 사유: 기존 report 필드 의미를 바꾸지 않고, 향후 다른 adapter metadata도 같은 구조를 쓸 수 있습니다. 별도 report 파일은 필요 없습니다.

B) `RetryJobReport(JobReport)` 상속 모델을 새로 만든다.

C) counters는 stdout에만 출력하고 report에는 남기지 않는다.

X) 기타

[Answer]: A

### Question 7. DirectPost Job Assembly Pattern

retry batch를 `JobRunner`로 넘기는 방식은 어떻게 할까요?

A) (권장) deduped candidate URL list로 `DirectPostSource`를 만들고, 기존 `JobConfig` + `run_job` 경로를 그대로 사용한다. fake runner 주입 지점을 둬 테스트한다.

추천 사유: 기존 worker/checkpoint/output/HTTP 정책을 재사용하면서 테스트도 단순해집니다.

B) `PostDetailService.fetch_post()`를 service에서 직접 반복 호출한다.

C) retry 전용 worker queue를 새로 구현한다.

X) 기타

[Answer]: A

### Question 8. CLI Summary Pattern

`retry-failures` 터미널 출력은 어떻게 구성할까요?

A) (권장) 완료 후 한 줄 또는 짧은 블록으로 `selected`, `skipped_existing`, `success`, `remaining_failure`, `report` 경로만 출력한다. invalid line 원문이나 raw exception은 출력하지 않는다.

추천 사유: 운영자는 복구 결과 숫자와 report 위치가 필요합니다. 상세 원문 출력은 보안/가독성 모두에 불리합니다.

B) 선택/제외된 모든 failure record를 stdout에 출력한다.

C) 아무 출력 없이 exit code만 반환한다.

X) 기타

[Answer]: A

### Question 9. Property-Based Test Pattern

PBT는 어떤 단위에 적용할까요?

A) (권장) I/O 없는 selector 함수에 집중한다. dedupe last-wins, allowlist filtering, existing success skip, explicit option precedence를 검증한다.

추천 사유: PBT는 순수 로직에서 가장 효과적입니다. 파일/S3/runner까지 섞으면 느리고 불안정해집니다.

B) S3 fake reader와 runner orchestration까지 PBT로 모두 생성한다.

C) UOW-009는 example test만 두고 PBT는 생략한다.

X) 기타

[Answer]: A

### Question 10. Optional Smoke Pattern

UOW-009 optional smoke는 어디까지 둘까요?

A) (권장) local fixture retry smoke는 기본 테스트에 포함하고, S3/Garage input read와 live post retry smoke는 env/marker gated optional로 둔다.

추천 사유: 기본 gate는 안정적으로 유지하면서 실제 저장소/라이브 사이트 확인은 필요할 때만 실행할 수 있습니다.

B) live post retry smoke를 기본 테스트에 포함한다.

C) optional smoke는 만들지 않는다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-009 NFR Design 산출물 2개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 Infrastructure Design 또는 Code Generation으로 넘어가지 않습니다.
