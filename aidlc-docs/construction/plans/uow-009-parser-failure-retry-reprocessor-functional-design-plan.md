# Functional Design 계획 - UOW-009 Parser Failure Retry Reprocessor

이 계획은 `UOW-009 Parser Failure Retry Reprocessor`의 기능 설계를 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-009 Parser Failure Retry Reprocessor
- **Depends On**: UOW-001 Core Models And Config, UOW-004 Post Detail And Content Parsing, UOW-005 Job Runner And Checkpoint, UOW-006 Output And Storage, UOW-007 CLI Adapter
- **Primary Story**: US-016A
- **Related Stories**: US-007, US-012, US-015, US-016
- **Scope**: `failures.jsonl` 입력, parser-stage post failure 선별, direct-post retry batch 생성, 기존 성공 결과 skip, 새 retry run/report 저장, CLI/API 진입점
- **Out Of Scope**: parser selector 수정, HTTP retry 정책 변경, CAPTCHA 우회, 네트워크/저장소 실패 자동 복구, 분산 DLQ/scheduler, 원본 failure file mutation

## Functional Design 작업 체크리스트

- [x] UOW-008 Build and Test 승인 확인
- [x] UOW-009 증분 추가 필요성 확인
- [x] UOW-001/UOW-004/UOW-005/UOW-006/UOW-007 계약 확인
- [x] Functional Design 질문 생성
- [x] Functional Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-009-parser-failure-retry-reprocessor/functional-design/business-logic-model.md` 생성
- [x] `aidlc-docs/construction/uow-009-parser-failure-retry-reprocessor/functional-design/business-rules.md` 생성
- [x] `aidlc-docs/construction/uow-009-parser-failure-retry-reprocessor/functional-design/domain-entities.md` 생성

## Answer Validation Notes

- Q1 selected B: retry reads both local `failures.jsonl` files and S3/Garage object URIs.
- Q2-Q5 and Q7-Q10 selected A.
- Q6 selected A plus `--from-report` and `--from-checkpoint` restoration helpers. Explicit retry options take precedence over restored options and normal `run` defaults.
- No follow-up question is required before Functional Design artifact review.

## Functional Design Questions

### Question 1. Retry Input Source

재처리 대상 실패 기록은 어디에서 읽을까요?

A) (권장) 하나 이상의 local `failures.jsonl` 파일 경로를 입력받는다. S3/Garage failure object 읽기는 후속 확장으로 둔다.

추천 사유: 현재 CLI smoke와 로컬 운영에서 바로 필요한 경로입니다. S3 목록/다운로드까지 넣으면 저장소 adapter 범위가 커집니다.

B) local 파일과 S3/Garage object URI를 모두 1차 구현에 포함한다.

C) 최근 Job의 output root를 입력받아 내부에서 `failures.jsonl`을 자동 탐색한다.

X) 기타

[Answer]: B

### Question 2. Retryable Failure Selection

어떤 failure record를 재처리 대상으로 볼까요?

A) (권장) `stage="post"`이면서 reason이 parser/metadata 계열인 allowlist만 포함한다. 예: `post title missing`, `post author missing`, `post identity missing`, content parse failure. CAPTCHA, block, network, storage, checkpoint 실패는 제외한다.

추천 사유: 이번 유닛의 목적은 parser 수정 이후 실패 게시글 회수입니다. 네트워크/저장소 계열을 섞으면 기존 HTTP retry와 checkpoint 책임이 흐려집니다.

B) `retryable=true`인 failure만 포함한다.

C) 사용자가 reason 목록을 CLI 옵션으로 전부 지정해야 한다.

X) 기타

[Answer]: A

### Question 3. Existing Success Skip

이미 다른 run에서 성공 저장된 게시글은 어떻게 처리할까요?

A) (권장) 선택적으로 기존 `posts.jsonl` 경로를 받아 `(site_id, gallery_id, post_id)` 기준으로 skip한다. 입력하지 않으면 failure 파일의 모든 재처리 대상에 대해 다시 시도한다.

추천 사유: 오늘 smoke처럼 재시도 run을 여러 번 나눠도 중복 수집을 피할 수 있습니다. 동시에 단순 사용자는 failure 파일만 넣어 실행할 수 있습니다.

B) 항상 같은 output root 아래의 모든 `posts.jsonl`을 자동 탐색해 skip한다.

C) skip 기능 없이 항상 모든 실패를 재시도한다.

X) 기타

[Answer]: A

### Question 4. Retry Output Semantics

재처리 결과는 어디에 저장할까요?

A) (권장) 원본 failure file은 수정하지 않고, 새 retry Job/run의 `posts.jsonl`, `failures.jsonl`, `report.json`으로 저장한다. report metadata에 원본 failure 파일 경로와 retry 대상 수를 기록한다.

추천 사유: 원본 증거를 보존하고, 재처리 결과를 감사하기 쉽습니다. JSONL을 수정하는 방식보다 구현과 복구가 단순합니다.

B) 성공한 항목은 원본 failure file에서 제거하고 별도 성공 파일을 만든다.

C) 원본 Job의 기존 `posts.jsonl`에 append한다.

X) 기타

[Answer]: A

### Question 5. Retry Execution Path

실제 재처리는 어떤 실행 경로를 사용할까요?

A) (권장) 실패 URL을 `DirectPostSource`로 변환해 기존 `JobRunner`와 `PostDetailService`를 그대로 호출한다.

추천 사유: 이미 검증된 worker, output, checkpoint, HTTP/User-Agent/Proxy 경로를 재사용할 수 있습니다. 별도 parser runner를 만들 필요가 없습니다.

B) `PostDetailService`를 직접 호출하는 전용 retry runner를 만든다.

C) HTML 원본을 저장해 두었다가 네트워크 요청 없이 재파싱한다.

X) 기타

[Answer]: A

### Question 6. Scrape Options For Retry

재처리 시 댓글, 이미지, 디시콘 옵션은 어떻게 정할까요?

A) (권장) CLI/API에서 `--no-comments`, `--image-mode`, `--dccon-mode`, request interval, worker count를 다시 받으며 기본값은 일반 `run`과 동일하게 둔다.

추천 사유: 현재 failure record만으로는 원 Job의 모든 옵션을 안정적으로 복원할 수 없습니다. 기존 CLI 옵션을 재사용하면 구현이 작고 명확합니다.

B) 같은 output root의 checkpoint 또는 report에서 원 Job 설정을 찾아 자동 복원한다.

C) retry는 항상 `--no-comments`, `metadata_only`, `dccon skip`으로 고정한다.

X) 기타

[Answer]: A + `--from-report`, `--from-checkpoint` 같은 자동 복원 옵션도 추가한다. 

### Question 7. Duplicate Failure Records

여러 failure 파일에 같은 게시글이 중복으로 들어 있으면 어떻게 할까요?

A) (권장) `(site_id, gallery_id, post_id)` 기준으로 retry batch 내부에서 dedupe한다. 같은 key의 URL이 여러 개면 가장 마지막 failure record의 URL을 사용한다.

추천 사유: 여러 차례 retry 결과를 합칠 때 같은 게시글이 반복될 수 있습니다. 한 번만 재시도하는 것이 요청 수와 결과 중복을 줄입니다.

B) failure record 줄 단위로 모두 재시도한다.

C) 중복이 발견되면 validation error로 전체 retry를 중단한다.

X) 기타

[Answer]: A

### Question 8. CLI And Library Boundary

사용자는 이 기능을 어떻게 호출할까요?

A) (권장) import 가능한 `ParserFailureRetryService`와 CLI `retry-failures` subcommand를 함께 제공한다. CLI는 service를 얇게 감싸는 adapter로 둔다.

추천 사유: 터미널 운영과 향후 통합 플랫폼/MCP 재사용을 동시에 만족하면서도 scraping 로직 중복을 피합니다.

B) CLI subcommand만 제공한다.

C) Python library API만 제공하고 CLI는 후속으로 둔다.

X) 기타

[Answer]: A

### Question 9. Remaining Failure Report

재처리 후에도 실패한 게시글은 어떻게 보고할까요?

A) (권장) 일반 Job failure와 같은 `failures.jsonl`에 남기고, retry report metadata에 `initial_failure_count`, `selected_retry_count`, `success_count`, `remaining_failure_count`, `skipped_existing_count`를 기록한다.

추천 사유: 기존 output contract를 유지하면서 retry 운영에 필요한 집계만 추가하면 됩니다.

B) retry 전용 `retry-summary.json`만 만들고 일반 `report.json`은 사용하지 않는다.

C) stdout에만 결과를 출력한다.

X) 기타

[Answer]: A

### Question 10. Stop Conditions

재처리 실행 중 CAPTCHA/차단/수동 중단이 발생하면 어떻게 처리할까요?

A) (권장) 기존 JobRunner stop/checkpoint 규칙을 그대로 따른다. CAPTCHA/차단은 즉시 중단하고 checkpoint를 저장하며, parser-stage 개별 실패만 계속 진행 가능한 실패로 기록한다.

추천 사유: 운영상 위험한 상태를 일반 parser retry와 섞지 않아야 합니다. 기존 중단점 저장 정책도 그대로 재사용할 수 있습니다.

B) CAPTCHA/차단도 failure로 기록하고 계속 진행한다.

C) retry unit에서는 checkpoint를 만들지 않고 실패 즉시 프로세스를 종료한다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-009 Functional Design 산출물 3개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-009 NFR Requirements로 넘어가지 않습니다.
