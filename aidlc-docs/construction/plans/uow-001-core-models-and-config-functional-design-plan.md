# Functional Design 계획 - UOW-001 Core Models And Config

이 계획은 `UOW-001 Core Models And Config`의 기능 설계를 위한 질문지입니다. 답변이 확정되기 전에는 Functional Design 산출물을 생성하지 않습니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-001 Core Models And Config
- **Primary Story**: US-017 Python 라이브러리 API를 제공한다
- **Supporting Stories**: US-001, US-012, US-019
- **Scope**: Pydantic 모델, Job 설정, validation, public API request/result schema, port protocol
- **Out Of Scope**: HTTP retry 구현, HTML selector별 파싱, JobRunner queue 알고리즘, 실제 storage adapter 구현

## Functional Design 작업 체크리스트

- [x] Unit of Work 산출물 확인
- [x] 관련 user stories 확인
- [x] Application Design 컴포넌트와 method contract 확인
- [x] 기능 설계 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 불필요 확인
- [x] `aidlc-docs/construction/uow-001-core-models-and-config/functional-design/business-logic-model.md` 생성
- [x] `aidlc-docs/construction/uow-001-core-models-and-config/functional-design/business-rules.md` 생성
- [x] `aidlc-docs/construction/uow-001-core-models-and-config/functional-design/domain-entities.md` 생성
- [x] 설계 완전성과 일관성 검증

## Functional Design 질문

### Question 1. Pydantic 버전

Pydantic 모델은 어떤 버전을 기준으로 설계할까요?

A) (권장) Pydantic v2를 기준으로 설계한다.

추천 사유: Application Design에서 `model_dump(mode="json")`을 이미 전제로 두었고, 신규 프로젝트라 v1 호환 비용을 들일 이유가 작습니다.

B) Pydantic v1을 기준으로 설계한다.

C) v1/v2 양쪽 호환을 목표로 설계한다.

X) 기타

[Answer]: A

### Question 2. 모델 extra field 정책

수집 결과 모델에서 문서화되지 않은 필드는 어떻게 처리할까요?

A) (권장) public input/config 모델은 `extra="forbid"`, scrape result 모델은 `extra="forbid"`로 시작하되 확장 필드는 `metadata` dict에만 넣는다.

추천 사유: CLI/MCP/container 입력은 엄격해야 하고, JSONL 분석 스키마도 예측 가능해야 합니다. 향후 커뮤니티별 확장은 아무 필드나 허용하기보다 `metadata` 같은 명시적 확장 필드로 받는 편이 안전합니다.

B) 모든 모델에서 `extra="forbid"`를 사용한다.

C) 결과 모델은 `extra="allow"`로 두고 입력/config만 `extra="forbid"`로 둔다.

X) 기타

[Answer]: A

### Question 3. JobConfig 구조

수집 진입점별 Job 설정은 어떻게 모델링할까요?

A) (권장) 공통 `JobConfig`에 `job_type`을 두고, `source` 필드를 discriminated union으로 둔다.

추천 사유: direct URL, gallery search, integrated search, deep search, no-keyword, realtime은 source별 필수 값이 다릅니다. discriminated union이면 validation 오류가 명확하고 adapter 입력도 단순합니다.

B) `DirectUrlJobConfig`, `GallerySearchJobConfig`처럼 Job type별 최상위 모델을 따로 둔다.

C) 하나의 `JobConfig`에 모든 optional 필드를 넣고 validator로 조합을 검사한다.

X) 기타

[Answer]: A

### Question 4. ContentBlock 구조

본문의 텍스트, 이미지, 동영상, YouTube, 링크, 시리즈는 어떻게 표현할까요?

A) (권장) `ContentBlock`을 discriminated union으로 두고 `type` 값별 전용 payload 모델을 둔다.

추천 사유: 순서는 보존해야 하지만 block마다 필요한 필드가 다릅니다. type별 payload가 있으면 Polars 가공 전 JSONL 검증과 parser 테스트가 쉬워집니다.

B) 단일 `ContentBlock` 모델에 optional 필드를 많이 둔다.

C) top-level `content_text`, `images`, `videos`, `links`, `series` 배열로만 분리하고 순서 보존 block은 두지 않는다.

X) 기타

[Answer]: A

### Question 5. 식별자 타입

글번호, 댓글 번호, 갤러리 ID 같은 식별자는 어떤 타입으로 저장할까요?

A) (권장) DCinside 원본 식별자는 문자열로 저장하고, 숫자 비교가 필요한 글번호/댓글번호는 별도 normalized int 필드를 둔다.

추천 사유: 갤러리 ID는 문자열이고, 외부 시스템 통합 시 원본 ID를 그대로 보존하는 편이 안전합니다. 범위 비교에는 int가 필요하므로 비교용 필드를 분리합니다.

B) 숫자로 보이는 모든 ID는 int로 저장한다.

C) 모든 식별자를 문자열로만 저장하고 비교 시점에 변환한다.

X) 기타

[Answer]: A

### Question 6. Public API 오류 모델

library, CLI, MCP가 공유할 오류는 어떻게 표현할까요?

A) (권장) 내부 예외는 typed exception으로 두고, adapter로 나갈 때 `ErrorResult(code, message, details)` 모델로 변환한다.

추천 사유: core 내부에서는 예외가 흐름 제어에 편하고, MCP/CLI/container 경계에서는 secret이 제거된 구조화 오류가 필요합니다.

B) 모든 core API가 예외를 던지지 않고 `Result[T, ErrorResult]` 형태로 반환한다.

C) Python 기본 예외와 문자열 메시지만 사용한다.

X) 기타

[Answer]: A

### Question 7. Schema versioning

JSONL과 checkpoint schema version은 어떻게 관리할까요?

A) (권장) 모든 top-level `PostResult`, `Checkpoint`, `JobReport`에 `schema_version`을 넣고, 1차 값은 `"dcinside.v1"` 또는 `"checkpoint.v1"`로 둔다.

추천 사유: 향후 공통 분석 schema와 다른 커뮤니티 scraper가 추가됩니다. 지금 version 필드를 넣어두면 migration과 normalizer가 단순해집니다.

B) JSONL에는 version을 넣고 checkpoint에는 넣지 않는다.

C) 1차 구현에서는 version field를 생략한다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-001 Functional Design 산출물 3개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 다음 unit 또는 NFR 단계로 넘어가지 않습니다.
