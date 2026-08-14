# 커뮤니티 스크래퍼 표준 구조/기능 계승 가이드

이 문서는 후속 커뮤니티 스크래퍼를 만들 때 공통 기반으로 삼을 표준 구조와 기능 기준을 정의합니다.

목표는 특정 커뮤니티 스크래퍼를 다른 특정 커뮤니티로 옮기는 것이 아닙니다. 모든 커뮤니티 스크래퍼가 같은 실행 구조, 저장 구조, 운영 방식, 데이터 처리 방식을 공유하고, 커뮤니티마다 달라지는 URL, API query, HTML 구조, 사용자 용어, 차단 패턴만 site-specific 구현으로 분리하는 것이 목표입니다.

## 핵심 기준

모든 후속 스크래퍼는 같은 8개 Unit of Work 구조를 따릅니다.

공유할 것:

- 모델 계약
- Job 설정과 실행 생명주기
- HTTP runtime 정책
- User-Agent 교체
- Proxy 설정
- 요청 속도 조절
- 링크 수집기 1개 + 게시글 상세 워커 N개 구조
- 체크포인트와 resume
- CAPTCHA/차단 감지 시 fail-closed 정책
- 로컬 JSONL 출력
- S3 호환 저장소 출력
- PostgreSQL 체크포인트
- CLI 구조
- 터미널 마법사 구조
- 컨테이너 워커 구조
- MCP 도구 구조
- 테스트 계층
- Polars 기반 정규화 전략

커뮤니티별로 분리할 것:

- 게시판/검색 URL 생성 규칙
- 커뮤니티 API endpoint
- 커뮤니티 API query parameter
- pagination, cursor, offset, page token 규칙
- 게시판/탭/카테고리/말머리/분류 체계
- HTML selector와 DOM parser
- 댓글/답글 구조
- 첨부 이미지/동영상/임베드 구조
- 로그인 필요 여부
- 쿠키 필요 여부
- CAPTCHA/차단/점검 페이지 감지 패턴
- 커뮤니티 고유 콘텐츠와 고유 메타데이터

## 문서의 사용 범위

이 문서는 아래 상황에서 사용합니다.

- 새 커뮤니티 스크래퍼의 기능 명세서를 작성할 때
- 기존 스크래퍼의 구조를 후속 스크래퍼 표준으로 정리할 때
- 여러 커뮤니티 스크래퍼를 같은 운영 시스템에 넣으려 할 때
- 커뮤니티별 JSONL을 공통 분석 스키마로 정규화하려 할 때
- 공통 core 패키지 분리 여부를 판단할 때
- CLI, 컨테이너, MCP, 저장소, 체크포인트 구조를 통일하려 할 때

이 문서는 특정 커뮤니티의 API query나 HTML selector를 기록하는 문서가 아닙니다. 그런 내용은 각 커뮤니티 스크래퍼의 기능 명세서 또는 조사 문서에 따로 기록합니다.

## 용어

| 용어 | 의미 |
| --- | --- |
| Community Scraper | 특정 커뮤니티 하나를 대상으로 하는 스크래퍼 |
| Base Scraper Standard | 후속 스크래퍼가 공유해야 할 구조와 기능 표준 |
| Shared Core | 커뮤니티와 무관하게 공유 가능한 모델, 런타임, 저장소, Job 실행기 |
| Site Adapter | 커뮤니티별 URL, query, parser, source builder, 차단 감지 규칙 |
| Source | 수집 시작 방식. 예: 직접 게시글, 게시판 검색, 통합 검색, 심층 검색 |
| Candidate | 상세 수집 전 단계의 게시글 후보 링크 |
| Post Detail | 게시글 상세 HTML/API 응답을 파싱해 최종 게시글 모델로 만드는 단계 |
| Checkpoint | 중단과 재개를 위한 작업 상태 snapshot |
| Normalization | 커뮤니티별 원본 JSON을 공통 분석 스키마로 변환하는 과정 |
| Site-Specific Field | 특정 커뮤니티에서만 의미가 있는 필드 |

## 계승 원칙

### 1. 기능 표면은 동일하게 유지한다

후속 커뮤니티 스크래퍼는 가능한 한 같은 기능 표면을 가져야 합니다.

필수 기능:

- 게시글 URL 직접 수집
- 게시판 내 검색 수집
- 사이트 통합 검색 수집
- 심층 검색
- 노키워드 기간/글번호 범위 수집
- 실시간 키워드 수집
- 실시간 전체 수집
- 댓글과 답글 수집
- 본문 텍스트 수집
- 이미지 수집
- 동영상 또는 임베드 영상 수집
- 외부 동영상 임베드 수집
- 외부 링크 수집
- 시리즈/게시글 모음류 수집
- 재게시/공유/인용/펌 성격의 게시글 메타데이터 수집
- 커뮤니티 고유 이모티콘/스티커/콘텐츠 메타데이터 수집
- User-Agent 교체
- Proxy 사용
- 요청 속도 조절
- 멀티 워커 상세 수집
- 중단점 저장과 resume
- CAPTCHA/차단 감지 시 중단
- 로컬 JSONL 저장
- S3 호환 저장
- PostgreSQL 체크포인트
- CLI 실행
- 터미널 마법사
- 컨테이너 워커 실행
- MCP 도구 제공
- Polars 가공 가능 JSONL 출력

특정 커뮤니티에 기능이 존재하지 않으면 기능 항목을 삭제하지 않습니다. 공통 스키마의 해당 slot을 `null`, 빈 list, 또는 site-specific metadata의 미지원 상태로 표현합니다.

예:

- 커뮤니티 고유 이모티콘이 없으면 관련 list는 빈 list로 둡니다.
- 재게시/공유/인용 기능이 없으면 `is_repost=false`, `repost=null`로 둡니다.
- 게시판 분류가 없으면 `board_category=null`로 둡니다.
- 글번호 개념이 없으면 `post_number=null`로 두고 안정적인 `post_id`를 사용합니다.

### 2. 커뮤니티 API query는 공유하지 않는다

각 커뮤니티 스크래퍼는 해당 커뮤니티에 맞는 API endpoint와 query parameter 구조를 따로 가집니다.

공유하지 않는 항목:

- 검색 API endpoint
- 게시판 목록 endpoint
- 게시글 상세 endpoint
- 댓글 endpoint
- 검색어 parameter 이름
- 게시판 identifier parameter 이름
- pagination parameter 이름
- cursor parameter 이름
- 정렬 parameter 이름
- 카테고리/탭/분류 parameter 이름
- 날짜 이동 또는 기간 검색 parameter 이름
- 글번호 범위 parameter 이름
- API 응답 JSON 구조
- HTML fallback selector

공유하는 항목:

- 기능명
- source model의 역할
- URL/query builder의 책임
- parser가 반환해야 하는 결과 모델
- collector가 `PostCandidate`를 만들어 queue에 넣는 계약
- range filter와 dedupe 정책
- 실패 시 failure record를 남기는 정책

표준 설명:

```text
공통 기능: board-search
각 커뮤니티 구현: 해당 커뮤니티의 게시판 검색 URL/API/query
공유 결과: list[PostCandidate]
```

중요한 점은 query parameter 이름을 공통화하지 않는 것입니다. 어느 커뮤니티는 page 기반일 수 있고, 어느 커뮤니티는 cursor 기반일 수 있으며, 어느 커뮤니티는 검색 결과를 HTML로만 제공할 수 있습니다. 이 차이는 site adapter 안에 가둡니다.

### 3. parser는 커뮤니티별로 분리한다

HTML parser와 API response parser는 공유하지 않습니다.

공유하면 안 되는 것:

- CSS selector
- DOM depth 가정
- 제목 위치
- 작성자 위치
- 조회수/추천수 위치
- 날짜 문자열 형식
- 본문 container 구조
- 이미지 lazy loading 구조
- 동영상 embed 구조
- 댓글/답글 DOM 구조
- 삭제/블라인드/관리자 삭제 표시
- 모바일/PC 페이지 차이
- 커뮤니티별 오류 페이지 selector

공유해도 되는 것:

- 파싱 결과 모델
- 파싱 실패 error type
- 안전한 failure record 생성 규칙
- content block order validation
- 일반적인 숫자 정규화 helper
- 일반적인 날짜 정규화 helper
- 일반적인 URL normalization helper

규칙:

- parser는 순수 파서로 유지합니다.
- parser는 네트워크 요청을 직접 하지 않습니다.
- parser는 파일을 쓰지 않습니다.
- parser는 입력 HTML/API 응답과 site-specific parser config만 받아 결과 모델을 반환합니다.

### 4. 저장 구조는 공유한다

커뮤니티가 달라도 저장 레이아웃은 동일해야 합니다.

여러 스크래퍼가 같은 S3 호환 저장소와 PostgreSQL을 공유하는 세부 규약은 `docs/Shared_Storage_Contract.md`를 따릅니다. 이 문서에서는 공통 구조만 요약합니다.

로컬:

```text
outputs/
└── <job_id>/
    └── <run_id>/
        ├── posts.jsonl
        ├── failures.jsonl
        ├── report.json
        └── media/
```

S3 호환 저장소:

```text
outputs/<job_id>/<run_id>/posts.jsonl
outputs/<job_id>/<run_id>/failures.jsonl
outputs/<job_id>/<run_id>/report.json
outputs/<job_id>/<run_id>/media/...
```

이 구조를 유지하면 운영 시스템과 분석 파이프라인이 커뮤니티 종류와 무관하게 결과를 찾을 수 있습니다.

### 5. 원본 스키마와 공통 스키마를 분리한다

각 커뮤니티 스크래퍼는 커뮤니티별 원본 JSON 스키마를 유지합니다.

예:

```text
<site_id>.post.v1
```

분석 단계에서는 별도 normalizer가 원본 JSONL을 공통 스키마로 변환합니다.

예:

```text
<site_id>.post.v1 -> community_common.posts.v1
```

장점:

- 커뮤니티 고유 데이터를 잃지 않습니다.
- 공통 분석에는 동일한 테이블을 사용할 수 있습니다.
- 새 커뮤니티가 추가되어도 기존 JSONL을 깨지 않습니다.
- parser 변경과 분석 스키마 변경을 분리할 수 있습니다.

## 권장 아키텍처

### 단기 구조

후속 스크래퍼를 처음 만들 때는 기존에 검증된 구조를 템플릿으로 사용합니다. 다만 site-specific 코드를 그대로 복사하지 않고, 커뮤니티별 조사 결과에 맞춰 새로 작성합니다.

예시:

```text
ExampleCommunity-Scraper/
├── pyproject.toml
├── README.md
├── docs/
│   ├── Function_Specification.md
│   ├── Deployment_Operations.md
│   └── Cross_Community_Scraper_Inheritance_Guide.md
├── src/
│   └── example_community_scraper/
│       ├── adapters/
│       ├── core/
│       ├── collect/
│       ├── http/
│       ├── models/
│       ├── outputs/
│       ├── parse/
│       ├── runner/
│       └── retry/
└── tests/
```

단기 단계에서는 공통 core 패키지를 성급히 만들지 않습니다. 두 개 이상의 실제 커뮤니티 구현에서 중복과 차이가 확인된 뒤 분리합니다.

### 중기 구조

여러 커뮤니티 스크래퍼가 안정화되면 공유 가능한 부분을 별도 패키지로 분리합니다.

```text
community-scraper-core/
├── src/community_scraper_core/
│   ├── core/
│   ├── http/
│   ├── models/
│   ├── outputs/
│   ├── runner/
│   └── adapters_base/
└── tests/

community-a-scraper/
└── src/community_a_scraper/
    ├── site/
    ├── collect/
    └── parse/

community-b-scraper/
└── src/community_b_scraper/
    ├── site/
    ├── collect/
    └── parse/
```

공통 패키지 후보:

- 에러 타입
- 포트 프로토콜
- 공통 모델 base
- HTTP runtime
- User-Agent provider
- Proxy provider
- rate limiter
- retry/backoff
- JobRunner
- checkpoint coordinator
- LocalOutputStore
- S3OutputStore
- PostgresCheckpointStore
- report/failure 모델
- CLI base builder 일부
- container base entrypoint 일부
- MCP handler base 일부

커뮤니티별 패키지에 남길 항목:

- URL builder
- query builder
- pagination/cursor parser
- search parser
- detail parser
- comment parser
- media parser
- board/category parser
- site-specific response classifier
- fixture HTML/API response
- live smoke URL

### 장기 구조

커뮤니티 스크래퍼가 3개 이상이 되면 monorepo 또는 plugin형 구조를 검토합니다.

```text
community-scrapers/
├── packages/
│   ├── community_scraper_core/
│   ├── community_a_scraper/
│   ├── community_b_scraper/
│   └── community_c_scraper/
├── docker/
├── docs/
└── pipelines/
```

장기 단계에서 도입할 수 있는 것:

- 공통 Job 큐
- 공통 운영 UI
- 공통 스케줄러
- 공통 정규화 파이프라인
- 공통 분석 DB
- 커뮤니티별 worker container
- 공통 MCP gateway

## UOW 표준

### UOW-001. Core Models and Config

역할:

- Pydantic 모델 정의
- Job 설정 정의
- source 모델 정의
- request/result schema 정의
- checkpoint 모델 정의
- report/failure 모델 정의
- 공통 enum 정의
- port protocol 정의
- validation 정책 정의

공유해야 할 모델:

- `JobConfig`
- `ScrapeOptions`
- `WorkerConfig`
- `StorageConfig`
- `RangeFilter`
- `RealtimeOptions`
- `PostCandidate`
- `PostResult` 계열 기본 구조
- `Comment`
- `ContentBlock`
- `MediaItem`
- `Checkpoint`
- `JobReport`
- `FailureRecord`

커뮤니티별로 달라지는 모델:

- `site_id`
- board identifier
- board type enum
- site-specific source model
- site-specific metadata model
- 원본 schema version

표준 필드:

```text
schema_version
scrap_timestamp
site_id
board_id
post_id
post_number
title
author
nickname_type
date
views
recommendations
comment_count
is_repost
repost
content
images
comments
links
metadata
```

규칙:

- 공통 분석에 필요한 필드는 가능한 한 최상위에 둡니다.
- 커뮤니티 고유 필드는 `metadata` 또는 site-specific nested model에 둡니다.
- 존재하지 않는 값은 임의로 만들지 않고 `null`로 둡니다.
- 숫자/날짜는 가능한 한 정규화합니다.
- 정규화가 불확실하면 원본 문자열도 metadata에 보존합니다.

### UOW-002. HTTP Runtime Policy

역할:

- `httpx.AsyncClient` 기반 HTTP 요청
- 요청 간격 적용
- retry/backoff
- timeout
- User-Agent 파일 로드
- User-Agent 교체
- Proxy 설정
- `.env` fallback
- 안전한 로그 이벤트
- CAPTCHA/차단/점검 응답 classification

공유 기능:

- HTTP client 생명주기
- 전역 request delay
- retry policy
- timeout policy
- User-Agent rotation
- Proxy 우선순위
- 안전 로그 redaction

커뮤니티별로 달라지는 것:

- 차단 페이지 문구
- CAPTCHA HTML/API 패턴
- 로그인 필요 응답 패턴
- 점검 페이지 패턴
- rate limit 응답 패턴
- referer/origin header 필요 여부
- 쿠키가 필요한 AJAX 흐름

규칙:

- 모든 네트워크 I/O는 HTTP port를 통합니다.
- parser는 네트워크 요청을 하지 않습니다.
- CAPTCHA 자동 우회는 구현하지 않습니다.
- 쿠키가 필요하면 생명주기와 저장 정책을 문서화합니다.

### UOW-003. Search and Link Collection

역할:

- 직접 URL normalization
- 게시판 검색 수집
- 통합 검색 수집
- 심층 검색
- 노키워드 범위 수집
- 실시간 키워드 수집
- 실시간 전체 수집
- dedupe
- range filter
- traversal guard
- `PostCandidate` queue 적재

공유 계약:

```text
Source config
  -> URL/query builder
  -> HTTP port
  -> search/list parser
  -> list[PostCandidate]
  -> queue
```

커뮤니티별 구현:

- board search URL/query builder
- integrated search URL/query builder
- board/list parser
- search result parser
- pagination parser
- cursor parser
- board discovery parser
- no-keyword range strategy
- realtime latest strategy

조사해야 할 항목:

- 게시판 목록 URL/API
- 게시글 URL 형식
- 게시판 ID 또는 slug 의미
- 게시판 이름 추출 방법
- 게시판 목록 pagination
- 게시판 내 검색 query
- 통합 검색 URL/API
- 검색 정렬 옵션
- 검색 페이지 최대 범위
- 다음 페이지 cursor 또는 page number 규칙
- 기간 검색 지원 여부
- 글번호 범위 검색 지원 여부
- 카테고리/탭/말머리 구조
- 공지/인기글/광고/삭제글 제외 기준

기능 parity 기준:

| 공통 기능 | 후속 스크래퍼 계약 | site-specific 구현 |
| --- | --- | --- |
| 직접 게시글 수집 | URL에서 `PostCandidate` 생성 | 게시글 URL parser |
| 게시판 검색 | 검색 결과에서 후보 링크 수집 | 게시판 검색 URL/API/query/parser |
| 통합 검색 | 사이트 전체 검색 후보 수집 | 통합 검색 URL/API/query/parser |
| 심층 검색 | 통합 검색으로 board discovery 후 board별 검색 | board discovery와 board search |
| 노키워드 범위 수집 | 키워드 없이 범위 기반 수집 | 커뮤니티가 지원하는 날짜/번호 범위 방식 |
| 실시간 전체 | 최신글 polling | 최신글 endpoint/parser |
| 실시간 키워드 | 최신 검색 결과 polling | 검색 최신순 endpoint/parser |

### UOW-004. Post Detail and Content Parsing

역할:

- 게시글 메타데이터 파싱
- 제목 파싱
- 작성자 파싱
- 작성일 파싱
- 조회수/추천수/댓글 수 파싱
- 본문 텍스트 파싱
- 이미지 파싱
- 동영상/임베드 파싱
- 외부 링크 파싱
- 시리즈/게시글 모음 파싱
- 재게시/공유/인용/펌 성격의 메타데이터 파싱
- 댓글/답글 파싱
- 삭제/블라인드/비정상 게시글 처리

공유할 것:

- 결과 모델
- content block 구조
- 댓글 flat list 구조
- 파싱 실패 error type
- block order validation
- failure record 생성 정책

커뮤니티별로 작성할 parser:

- post metadata parser
- author parser
- body parser
- content block parser
- media parser
- embedded video parser
- external link parser
- repost/share parser
- comment parser
- reply parser
- reaction parser

본문 block 표준:

| block type | 설명 |
| --- | --- |
| `text` | 일반 본문 텍스트 |
| `image` | 이미지 URL, 원본 URL, alt, 저장 경로 또는 object key |
| `site_video` | 커뮤니티 자체 동영상 또는 첨부 영상 |
| `external_video` | 외부 동영상 임베드 |
| `link` | 일반 링크 URL, 텍스트, 제목 |
| `series` | 시리즈/게시글 모음 |
| `community_embed` | 커뮤니티 고유 임베드 |
| `unknown_embed` | 아직 분류하지 못한 임베드 |

댓글 표준:

- 댓글은 flat list로 저장합니다.
- 루트 댓글은 `depth=0`입니다.
- 답글은 `depth=1` 이상입니다.
- 답글은 `parent_comment_id` 또는 이에 준하는 부모 key를 가집니다.
- 댓글 원본 구조가 중첩이어도 저장 모델은 동일하게 유지합니다.

조사해야 할 항목:

- 제목 selector/API field
- 제목 container 안에 말머리, repost marker, 모바일/앱 작성 표시, 접근성용 hidden/blind 텍스트가 섞이는지 여부
- 작성자 selector/API field
- 작성자 고유 ID 존재 여부
- 닉네임 유형 구분 가능 여부
- 작성일 selector/API field와 format
- 조회수 위치
- 추천/비추천/점수 위치
- 댓글 수 위치
- 본문 container
- 본문 텍스트 순서 보존 방식
- 이미지 원본 URL 구조
- 이미지 URL query 값이 안정적인 파일 ID인지, 일회성 서명 토큰인지 여부
- 첨부파일 구조
- 동영상 embed 구조
- 외부 동영상 embed 구조
- 외부 링크 구조
- 시리즈/관련글/게시글 모음 기능 여부
- 재게시/공유/인용/펌 기능 여부
- 댓글 endpoint가 HTML인지 API인지
- 댓글 pagination 방식
- 루트 댓글 selector
- 답글 selector
- 댓글 ID 추출 방법
- 부모 댓글 연결 방법
- 삭제 댓글 표시
- 블라인드 댓글 표시
- 댓글 추천/비추천 존재 여부

Smoke test에서 반드시 확인할 parser 방어 규칙:

- 제목은 실제 제목 field만 저장하고 기기 표시, 접근성용 blind 텍스트, 말머리, repost marker를 제목으로 오인하지 않습니다.
- 이미지 query 값이 긴 서명 토큰이면 `media_id`로 저장하지 않고 URL에만 보존합니다.
- parser-stage 실패는 원본 실패 기록을 보존한 채 실패 게시글만 재처리할 수 있어야 합니다.
- 재처리는 전체 검색 Job 재실행이 아니라 기존 `failures.jsonl`에서 parser-stage 게시글 실패만 선택해 direct-post 경로로 실행합니다.

### UOW-005. Job Runner and Checkpoint

역할:

- JobRunner
- queue orchestration
- worker pool lifecycle
- cancellation
- graceful stop
- resume
- checkpoint update ordering
- final report 생성

공유해야 할 것:

- 한 Job당 링크 수집기 1개
- 게시글 상세 워커 N개
- `asyncio.Queue[PostCandidate]`
- Ctrl+C 1회 graceful stop, 2회 강제 중단
- output 저장 성공 후 checkpoint advance
- resume 시 completed key skip
- remaining queue 복원
- checkpoint snapshot 저장

커뮤니티별로 달라지는 것:

- dedupe key를 구성하는 board/post identifier
- range filter에서 날짜/글번호를 해석하는 방식
- collector가 search position을 표현하는 방식

dedupe key 표준:

```text
(site_id, board_id, post_id)
```

글번호가 안정적이면 `post_number`를 보조 key로 사용할 수 있습니다. 글번호가 없거나 URL slug만 안정적이면 `post_id`를 canonical key로 사용합니다.

### UOW-006. Output and Storage

역할:

- 로컬 JSONL 출력
- 실패 기록 출력
- Job report 출력
- media 저장
- 로컬 checkpoint
- S3 호환 object store
- PostgreSQL checkpoint store
- safe failure sanitization

공유해야 할 것:

- `posts.jsonl`
- `failures.jsonl`
- `report.json`
- `media/`
- `Checkpoint.json`
- S3 호환 저장소 key 구조
- PostgreSQL checkpoint table 계약
- credential-free object reference

커뮤니티별로 달라지는 것:

- `schema_version`
- `site_id`
- site-specific metadata

규칙:

- JSONL은 한 줄에 게시글 하나입니다.
- 실패 기록은 민감정보를 제거한 safe record만 저장합니다.
- checkpoint는 output 저장 성공 후 advance합니다.
- resume은 checkpoint를 기준으로 수행합니다.

### UOW-007. CLI Adapter

역할:

- 터미널 명령 제공
- source별 옵션 parsing
- 공통 runtime 옵션 parsing
- `JobConfig` 생성
- resume 요청 생성
- User-Agent import
- Proxy 설정
- 터미널 마법사

공유 명령:

```text
run
resume
retry-failures
import-user-agents
configure-proxy
wizard
```

공통 옵션:

```text
--job-id
--output-path
--image-mode
--include-comments
--no-comments
--request-interval-seconds
--post-worker-count
--media-worker-count
--queue-max-size
--max-comment-pages
--user-agent-file
--user-agent-rotate-every
--proxy-host
--proxy-id
--proxy-pw
--date-from
--date-to
--min-post-number
--max-post-number
```

재처리 명령 옵션:

```text
--failure-file
--failure-ref
--existing-posts
--existing-posts-root
--from-report
--from-checkpoint
```

`--existing-posts-root`는 로컬 파일시스템 전용 편의 옵션입니다. S3 호환 저장소에서는 명시 object ref만 표준으로 둡니다.

`--from-report`와 `--from-checkpoint`는 복원 helper로 둘 수 있지만 동시에 허용하지 않습니다. 복원 로직이 없는 초기 구현에서는 명시적인 `--failure-file` 또는 `--failure-ref`를 필수로 둡니다.

커뮤니티별 source 옵션:

```text
--board-id
--board-name
--category
--keyword
--sort-mode
--page-start
--page-end
--cursor
```

위 option명은 예시입니다. 실제 후속 스크래퍼는 해당 커뮤니티의 용어와 query 구조를 조사한 뒤 확정합니다.

규칙:

- CLI는 source 모델을 만들 뿐 scraping logic을 갖지 않습니다.
- CLI option 이름은 커뮤니티 사용자 용어에 맞춥니다.
- 공통 runtime 옵션은 모든 스크래퍼에서 같은 이름을 유지합니다.
- 마법사는 커뮤니티별 질문 문구만 바꾸고 흐름은 공유합니다.

### UOW-008. Container, MCP, and Test Harness

역할:

- one-shot worker container
- 환경 변수 기반 runtime 구성
- S3 호환 저장소 연결
- PostgreSQL checkpoint 연결
- MCP 도구 핸들러
- fixture test
- optional smoke test

공유 컨테이너 환경 변수:

```text
DATABASE_URL
S3_ENDPOINT_URL
S3_BUCKET
S3_ACCESS_KEY_ID
S3_SECRET_ACCESS_KEY
S3_REGION
S3_FORCE_PATH_STYLE
RESUME
JOB_ID
```

커뮤니티별 prefix를 둘 수 있는 환경 변수:

```text
<SITE_PREFIX>_USER_AGENT_FILE
<SITE_PREFIX>_USER_AGENT_ROTATE_EVERY
<SITE_PREFIX>_PROXY_HOST
<SITE_PREFIX>_PROXY_ID
<SITE_PREFIX>_PROXY_PW
<SITE_PREFIX>_REALTIME_ENABLED
<SITE_PREFIX>_REALTIME_MODE
<SITE_PREFIX>_REALTIME_KEYWORD
<SITE_PREFIX>_REALTIME_DURATION_SECONDS
<SITE_PREFIX>_REALTIME_END_AT
<SITE_PREFIX>_REALTIME_POLL_INTERVAL_SECONDS
```

공유 MCP 도구:

```text
search_board
search_integrated
fetch_post
fetch_comments
run_job
resume_job
```

MCP 응답 envelope:

```json
{
  "ok": true,
  "data": {}
}
```

오류 응답:

```json
{
  "ok": false,
  "error": {
    "code": "validation_failure",
    "message": "...",
    "details": {}
  }
}
```

### UOW-009. Parser Failure Retry Reprocessor

역할:

- parser-stage 게시글 실패 선별
- 원본 `failures.jsonl` 보존
- 기존 성공 `posts.jsonl` 기반 중복 제외
- 실패 URL direct-post 재수집 Job 생성
- 재처리 결과 report metadata 기록

공유해야 할 것:

- failure JSONL line reader
- parser-stage 실패 allowlist/exclusion 규칙
- `(site_id, board_id, post_id)` 기준 dedupe
- 기존 성공 게시글 skip index
- `retry-failures` CLI 명령
- 컨테이너 entrypoint의 `retry-failures` 명령 전달
- `report.metadata.parser_failure_retry` 요약 구조

커뮤니티별로 달라지는 것:

- 게시글 URL 파서
- canonical direct-post URL 생성 규칙
- parser-stage failure reason 이름
- board/post identity field 이름

표준 제외 대상:

- CAPTCHA
- 차단
- 네트워크 실패
- 저장소 실패
- 체크포인트 실패
- 수동 중단 또는 취소

S3 호환 저장소 규칙:

- `failures.jsonl`과 `posts.jsonl` 입력은 `s3://bucket/key` 명시 object ref를 사용합니다.
- prefix listing 자동 탐색은 공통 표준에 넣지 않습니다.
- 로컬 directory scan은 로컬 CLI 편의 기능으로만 둡니다.

### UOW-010. AWS CDK Infrastructure

역할:

- AWS 기반 one-shot worker 배포
- S3 output bucket
- RDS PostgreSQL checkpoint store
- ECS Fargate task definition
- worker task/execution role
- CloudWatch Logs
- EventBridge 실패 감지와 선택적 schedule

공유해야 할 것:

- `infra/cdk` 프로젝트 구조
- environment별 YAML config 방식
- SharedInfraStack와 WorkerStack 분리
- worker image URI/tag 참조 방식
- Secrets Manager 이름 또는 ARN 참조 방식
- `docs/Shared_Storage_Contract.md`의 namespace, object key, checkpoint key 규약
- `cdk synth`와 template test

커뮤니티별로 달라지는 것:

- worker image
- `site_id`
- 커뮤니티별 환경 변수 prefix
- 기본 Job/source option
- schedule 필요 여부

표준 제외 대상:

- 커뮤니티 API query
- HTML/API parser
- Docker image build/push
- 중앙 Job Queue
- 통합 운영 UI
- EKS 배포

## 기능 계승 매트릭스

| 기능 | 표준 상태 | 후속 스크래퍼 기준 | site-specific 필요 여부 |
| --- | --- | --- | --- |
| 직접 게시글 수집 | 필수 | 게시글 URL에서 후보 생성 | URL parser 필요 |
| 게시판 검색 | 필수 | 게시판 검색 결과 수집 | URL/API/query/parser 필요 |
| 통합 검색 | 필수 | 사이트 전체 검색 결과 수집 | URL/API/query/parser 필요 |
| 심층 검색 | 필수 | 통합 검색으로 board discovery 후 board별 검색 | discovery parser 필요 |
| 노키워드 범위 수집 | 필수 | 키워드 없이 범위 기반 수집 | 지원 방식 조사 필요 |
| 실시간 키워드 | 필수 | 최신 검색 결과 polling | 최신순 endpoint/parser 필요 |
| 실시간 전체 | 필수 | 게시판 최신글 polling | 최신글 endpoint/parser 필요 |
| 댓글/답글 | 필수 | flat comment list로 저장 | 댓글 parser 필요 |
| 본문 텍스트 | 필수 | 순서 보존 | body parser 필요 |
| 이미지 | 필수 | URL와 metadata 저장 | media parser 필요 |
| 동영상/임베드 | 필수 | site video/external video 저장 | embed parser 필요 |
| 외부 링크 | 필수 | URL/text/title 저장 | link parser 필요 |
| 시리즈/게시글 모음 | 가능하면 지원 | 있으면 block으로 저장 | 기능 조사 필요 |
| 재게시/공유/인용 | 가능하면 지원 | 있으면 `repost`/share metadata 저장 | 기능 조사 필요 |
| 고유 이모티콘/스티커 | 가능하면 지원 | metadata 또는 media로 저장 | 기능 조사 필요 |
| User-Agent 교체 | 필수 | 동일 기능 제공 | 공유 |
| Proxy | 필수 | 동일 기능 제공 | 공유 |
| 요청 속도 조절 | 필수 | 동일 기능 제공 | 공유 |
| 멀티 워커 | 필수 | 동일 기능 제공 | 공유 |
| 체크포인트/resume | 필수 | 동일 기능 제공 | 공유 |
| Parser-stage 실패 재처리 | 필수 | 원본 failure 보존 후 실패 게시글만 재수집 | URL parser와 failure reason mapper 필요 |
| 로컬 JSONL | 필수 | 동일 구조 유지 | 공유 |
| S3 호환 저장 | 필수 | 동일 구조 유지 | 공유 |
| PostgreSQL checkpoint | 필수 | 동일 구조 유지 | 공유 |
| CLI | 필수 | 공통 명령 유지 | source option만 site-specific |
| 마법사 | 필수 | 공통 흐름 유지 | 질문 문구 site-specific |
| 컨테이너 | 필수 | one-shot worker 유지 | env prefix site-specific |
| AWS CDK/IaC | 필수 | Fargate worker와 공유 저장소 계약 유지 | image/env/schedule site-specific |
| MCP | 필수 | 공통 도구 유지 | tool naming 일부 site-specific |
| Polars 정규화 | 필수 | 공통 스키마로 변환 | mapper site-specific |

## 공통 데이터 모델 방향

### 원본 게시글 모델

커뮤니티별 원본 모델은 아래 공통 shape를 유지합니다.

```text
schema_version
scrap_timestamp
site_id
board_id
post_id
post_number
title
author
nickname_type
date
views
recommendations
comment_count
is_repost
repost
content
images
comments
links
metadata
```

설계 규칙:

- `site_id`는 커뮤니티 식별자입니다.
- `board_id`는 게시판, 채널, 포럼 등에 대응하는 공통 식별자입니다.
- 커뮤니티 원본 용어가 무엇이든 공통 분석 단계에서는 `board_id`로 매핑합니다.
- `post_id`는 canonical 게시글 식별자입니다.
- `post_number`가 없으면 `null`로 둡니다.
- `metadata`에는 커뮤니티 고유 원본 정보를 보존합니다.

### 콘텐츠 block

공통 block type:

```text
text
image
site_video
external_video
link
series
community_embed
unknown_embed
```

규칙:

- block은 본문 표시 순서를 보존합니다.
- `order`는 중복되지 않아야 합니다.
- 미분류 임베드는 버리지 않고 `unknown_embed`로 저장합니다.
- 커뮤니티 고유 콘텐츠는 `community_embed` 또는 site-specific metadata로 보존합니다.

### 댓글 모델

공통 댓글 모델:

```text
comment_id
comment_number
parent_comment_id
parent_comment_number
depth
author
body
created_at
recommendations
metadata
```

규칙:

- 댓글은 원본 JSON에서는 게시글 하위에 저장할 수 있습니다.
- 분석 정규화 단계에서는 게시글 테이블과 댓글 테이블로 분리합니다.
- 답글 구조가 여러 단계여도 `depth`와 parent key를 유지합니다.
- 삭제/블라인드 댓글은 가능한 한 상태를 metadata에 보존합니다.

### 추천/반응 모델

커뮤니티마다 추천, 비추천, 좋아요, 싫어요, 인기 점수의 의미가 다릅니다.

공통 모델:

```text
up
down
score
raw
metadata
```

규칙:

- 의미가 명확한 값은 `up`, `down`, `score`로 정규화합니다.
- 의미가 애매한 값은 `raw`와 metadata에 보존합니다.
- 억지로 추천/비추천에 끼워 맞추지 않습니다.

## 정규화 전략

각 스크래퍼는 원본 JSONL을 저장하고, 별도 normalizer가 공통 분석 테이블로 변환합니다.

권장 테이블:

```text
community_posts
community_comments
community_content_blocks
community_media
community_links
community_authors
community_jobs
community_failures
```

정규화 흐름:

```text
<site_id>.post.v1 JSONL
  -> <site_id> normalizer
  -> community_common tables
```

Polars 처리 예:

```python
import polars as pl

raw = pl.read_ndjson("outputs/example-job/run/posts.jsonl")

posts = raw.select(
    pl.col("site_id"),
    pl.col("board_id"),
    pl.col("post_id"),
    pl.col("title"),
    pl.col("date").alias("created_at"),
    pl.col("views"),
    pl.col("comment_count"),
)
```

정규화 규칙:

- 원본 JSONL은 수정하지 않습니다.
- 공통 스키마에는 분석에 필요한 필드를 둡니다.
- 커뮤니티 고유 필드는 `source_metadata`로 보존합니다.
- 댓글은 게시글과 분리합니다.
- 콘텐츠 block은 order를 유지합니다.
- media는 content block과 연결 가능한 key를 둡니다.
- LLM/RAG 입력용 원본 JSONL과 분석용 normalized table을 모두 유지할 수 있게 합니다.

## CLI 표준

후속 스크래퍼 CLI는 아래 구조를 유지합니다.

```powershell
example-scraper run --source direct-post --url "..."
example-scraper run --source board-search --board-id "..." --keyword "..."
example-scraper run --source integrated-search --keyword "..."
example-scraper run --source deep-search --keyword "..." --date-from "..." --date-to "..."
example-scraper run --source no-keyword-range --board-id "..." --date-from "..." --date-to "..."
example-scraper resume --job-id "..."
example-scraper retry-failures --failure-file ".\outputs\job-a\run-1\failures.jsonl"
example-scraper import-user-agents ".\user-agents.txt"
example-scraper configure-proxy --host "http://proxy.example:8080"
example-scraper wizard
```

공통 옵션은 모든 커뮤니티에서 같은 이름을 유지합니다.

```powershell
--job-id
--output-path
--include-comments
--no-comments
--request-interval-seconds
--post-worker-count
--queue-max-size
--max-comment-pages
--user-agent-file
--user-agent-rotate-every
--proxy-host
--proxy-id
--proxy-pw
```

재처리 전용 옵션은 모든 후속 스크래퍼에서 같은 이름을 유지합니다.

```powershell
--failure-file
--failure-ref
--existing-posts
--existing-posts-root
--from-report
--from-checkpoint
```

`--from-report`와 `--from-checkpoint`는 동시에 지정할 수 없으며, 복원 로직이 연결되지 않은 스크래퍼에서는 명시 failure input이 필요합니다.

site-specific source option은 커뮤니티 조사 후 정합니다.

예시:

```powershell
--board-id
--category
--cursor
--sort-mode
```

중요:

- 기존 커뮤니티의 사용자-facing option명을 후속 스크래퍼에 그대로 강요하지 않습니다.
- 후속 스크래퍼는 해당 커뮤니티 사용자가 이해하기 쉬운 용어를 사용합니다.
- 내부 공통 모델로 넘길 때만 `board_id`, `post_id`, `cursor` 같은 표준 용어로 매핑합니다.

## 컨테이너 표준

컨테이너 기본 구조:

```powershell
docker build -t example-scraper-worker .
```

실행 예:

```powershell
docker run --rm `
  --env-file .\.env.container `
  -e JOB_ID=example-board-20260809120000 `
  example-scraper-worker `
  run `
  --source board-search `
  --board-id "example-board" `
  --keyword "검색어"
```

필수 환경 변수:

```text
DATABASE_URL
S3_ENDPOINT_URL
S3_BUCKET
S3_ACCESS_KEY_ID
S3_SECRET_ACCESS_KEY
```

resume:

```powershell
docker run --rm `
  --env-file .\.env.container `
  -e RESUME=true `
  -e JOB_ID=example-board-20260809120000 `
  example-scraper-worker
```

공유 저장소 정책:

- S3 호환 API만 사용합니다.
- object key 구조는 모든 스크래퍼가 동일하게 유지합니다.
- PostgreSQL checkpoint를 사용합니다.
- Job당 독립 run output을 생성합니다.
- 특정 object storage 제품의 전용 API에 종속되지 않습니다.

## MCP 표준

MCP tool name은 가능한 한 공통 기능명을 유지합니다.

권장 tools:

```text
search_board
search_integrated
fetch_post
fetch_comments
run_job
resume_job
```

응답 envelope은 동일하게 유지합니다.

```json
{
  "ok": true,
  "data": {}
}
```

오류:

```json
{
  "ok": false,
  "error": {
    "code": "validation_failure",
    "message": "...",
    "details": {}
  }
}
```

운영 규칙:

- MCP handler는 core API를 호출합니다.
- MCP handler 안에 parser logic을 넣지 않습니다.
- 장시간 대량 수집은 컨테이너 Job과 checkpoint/resume을 우선합니다.

## 테스트 표준

필수 테스트:

- 모델 validation test
- import side-effect test
- URL builder test
- query builder test
- search parser fixture test
- post detail parser fixture test
- content block parser fixture test
- comment/reply parser fixture test
- block order validation test
- repost/share parser test
- range filter test
- dedupe test
- JobRunner checkpoint test
- resume test
- LocalOutputStore test
- S3OutputStore contract test
- PostgresCheckpointStore contract test
- CLI parser validation test
- wizard command generation test
- container env validation test
- MCP handler test
- optional live smoke test

Fixture 구조:

```text
tests/
└── fixtures/
    └── site/
        ├── board_search_page.html
        ├── integrated_search_page.html
        ├── post_detail_basic.html
        ├── post_detail_images.html
        ├── post_detail_embeds.html
        ├── comments_nested.html
        ├── blocked_page.html
        └── captcha_page.html
```

Fixture 정책:

- 개인정보를 포함하지 않습니다.
- 로그인 쿠키를 포함하지 않습니다.
- 외부에서 재현 가능한 공개 페이지를 사용합니다.
- 커뮤니티별 fixture는 분리합니다.
- parser 변경 시 fixture 기반 regression test를 먼저 추가합니다.

Live smoke test:

```powershell
python -m pytest -q -m "not live"
python -m pytest -q -m live
```

live test는 안정적인 공개 게시글 1개와 작은 검색 페이지 1개만 대상으로 합니다.

Live smoke 후 확인할 항목:

- 저장된 제목에 모바일/앱 작성 표시나 hidden/blind 텍스트가 섞이지 않았는지 확인합니다.
- 이미지/동영상 URL이 긴 서명 토큰을 포함해도 저장 모델 validation을 깨지 않는지 확인합니다.
- `failure_count`가 발생하면 대표 실패 URL을 단건 재시도해 일시 실패인지 parser regression인지 분리합니다.
- 일시 parser-stage 실패는 전체 Job 재실행보다 실패 URL 재처리로 회수합니다.
- `retry-failures` smoke를 실행해 원본 `failures.jsonl`이 보존되고 새 run의 `report.metadata.parser_failure_retry`가 생성되는지 확인합니다.

## 커뮤니티 조사 체크리스트

후속 스크래퍼 구현 전 반드시 조사합니다.

### 게시판/검색

- [ ] 게시판 URL 형식
- [ ] 게시글 URL 형식
- [ ] 게시판 ID 또는 slug 의미
- [ ] 게시판 이름 추출 방법
- [ ] 게시판 목록 pagination
- [ ] 게시판 내 검색 endpoint
- [ ] 게시판 내 검색 query parameter
- [ ] 통합 검색 endpoint
- [ ] 통합 검색 query parameter
- [ ] 검색어 encoding 방식
- [ ] 검색 정렬 옵션
- [ ] 검색 페이지 최대 범위
- [ ] 다음 페이지 cursor 또는 page number 규칙
- [ ] 기간 검색 지원 여부
- [ ] 글번호 범위 검색 지원 여부
- [ ] 카테고리/탭/말머리 구조
- [ ] 공지/인기글/광고/삭제글 제외 기준

### 게시글 상세

- [ ] 제목 selector/API field
- [ ] 작성자 selector/API field
- [ ] 작성자 고유 ID 존재 여부
- [ ] 닉네임 유형 구분 가능 여부
- [ ] 작성일 selector/API field와 format
- [ ] 조회수 selector/API field
- [ ] 추천/비추천/점수 selector/API field
- [ ] 댓글 수 selector/API field
- [ ] 본문 container
- [ ] 본문 텍스트 순서 보존 방식
- [ ] 이미지 원본 URL
- [ ] 동영상/첨부파일 구조
- [ ] 외부 동영상 iframe 구조
- [ ] 외부 링크 구조
- [ ] 시리즈/관련글/게시글 모음 기능 여부
- [ ] 재게시/공유/인용/펌 성격 기능 여부

### 댓글

- [ ] 댓글 endpoint가 HTML인지 API인지
- [ ] 댓글 pagination 방식
- [ ] 루트 댓글 selector/API field
- [ ] 답글 selector/API field
- [ ] 댓글 ID 추출 방법
- [ ] 부모 댓글 연결 방법
- [ ] 삭제 댓글 표시
- [ ] 블라인드 댓글 표시
- [ ] 댓글 추천/비추천 존재 여부
- [ ] 댓글 이미지/이모티콘 존재 여부

### 운영/차단

- [ ] CAPTCHA 페이지 구조
- [ ] 차단 페이지 구조
- [ ] 로그인 필요 페이지 구조
- [ ] 점검 페이지 구조
- [ ] 과도한 요청 시 응답 코드
- [ ] User-Agent에 민감한지
- [ ] Proxy 사용 시 동작
- [ ] 쿠키 없이 API/AJAX 요청 가능한지
- [ ] referer/origin header 필요 여부

## 구현 시작 순서

후속 스크래퍼는 아래 순서로 시작합니다.

1. 이 표준 문서를 복사합니다.
2. 대상 커뮤니티의 URL/query/HTML 구조를 조사합니다.
3. 기능 명세서를 작성합니다.
4. UOW-001에서 `site_id`, `schema_version`, board/source 모델을 확정합니다.
5. UOW-002 HTTP runtime은 표준 구조를 가져옵니다.
6. UOW-003 URL/query builder와 search parser를 fixture 기반으로 작성합니다.
7. UOW-004 post/comment/content parser를 fixture 기반으로 작성합니다.
8. UOW-006 저장소를 연결합니다.
9. UOW-005 JobRunner와 통합합니다.
10. UOW-007 CLI와 wizard를 연결합니다.
11. UOW-008 container/MCP/test harness를 연결합니다.
12. UOW-009 parser-stage 실패 재처리 명령을 연결합니다.
13. Polars 정규화 mapper를 작성합니다.

저장소를 JobRunner보다 먼저 구현하면 output write와 checkpoint advance 순서를 테스트하기 쉽습니다.

## 복사하면 안 되는 것

기존 커뮤니티 스크래퍼에서 후속 스크래퍼로 그대로 복사하면 안 되는 항목입니다.

- 사용자-facing 게시판 용어
- 커뮤니티별 URL prefix
- 커뮤니티별 query parameter 이름
- 커뮤니티별 cursor 이름
- 커뮤니티별 정렬 옵션 이름
- 커뮤니티별 검색어 encoding 방식
- 커뮤니티별 댓글 payload
- 커뮤니티별 재게시/공유 parser
- 커뮤니티별 동영상 selector
- 커뮤니티별 이모티콘 selector
- 커뮤니티별 CAPTCHA selector
- 커뮤니티별 차단 페이지 selector

필요하면 내부 공통 모델에서 표준 용어로 매핑합니다.

예:

```text
커뮤니티 원본 용어 -> board_id
커뮤니티 원본 게시글 식별자 -> post_id
커뮤니티 원본 페이지/cursor -> collection_position
```

## 반드시 유지해야 하는 것

후속 스크래퍼에서도 유지해야 하는 항목입니다.

- Pydantic validation
- import side-effect 없음
- 네트워크 I/O는 HTTP port를 통해 수행
- parser는 순수 파서로 유지
- adapter는 scraping logic을 갖지 않음
- output 저장 성공 후 checkpoint advance
- CAPTCHA 감지 시 fail-closed
- JSONL one post per line
- failure record sanitization
- local/S3/PostgreSQL 저장소 계약
- CLI/Container/MCP가 같은 core API 호출
- 테스트 fixture 기반 parser 검증
- Polars에서 읽을 수 있는 JSONL 유지
- 원본 JSONL과 공통 정규화 스키마 분리

## 설계 결정 기록

### 결정 1. 처음부터 공통 core 패키지를 만들지 않는다

후속 스크래퍼가 충분히 쌓이기 전에는 공통화 경계가 추측에 가깝습니다.

권장:

- 새 스크래퍼는 표준 구조를 그대로 따릅니다.
- site-specific 구현은 각 스크래퍼 안에 둡니다.
- 중복이 실제로 확인된 뒤 `community_scraper_core`로 분리합니다.

이유:

- 처음부터 공통 패키지를 만들면 특정 커뮤니티 기준의 잘못된 추상화가 생길 수 있습니다.
- 새 커뮤니티 구현 중 실제 차이가 드러납니다.
- 두 개 이상의 구현이 있어야 공통화할 코드와 분리할 코드를 정확히 판단할 수 있습니다.

### 결정 2. 기능명은 공유하고 source option은 커뮤니티별로 둔다

예:

```text
공유 기능명: board-search
커뮤니티별 사용자 용어: 각 커뮤니티에 맞게 선택
공통 내부 의미: 게시판 범위 검색으로 PostCandidate 수집
```

기능명은 운영/분석 관점에서 유지하고, CLI 사용자-facing 용어는 커뮤니티에 맞춥니다.

### 결정 3. 공통 스키마는 원본 저장소가 아니라 정규화 단계에서 만든다

스크래퍼는 원본을 최대한 보존합니다.

분석 시스템은 normalizer가 공통 테이블로 변환합니다.

이유:

- 커뮤니티별 고유 필드를 잃지 않습니다.
- parser 변경과 분석 스키마 변경을 분리할 수 있습니다.
- LLM/RAG 입력용 원본 JSONL과 분석용 normalized table을 모두 유지할 수 있습니다.

## 후속 스크래퍼 초기 산출물 체크리스트

초기 문서:

- [ ] `docs/Function_Specification.md`
- [ ] `docs/Deployment_Operations.md`
- [ ] `docs/Cross_Community_Scraper_Inheritance_Guide.md`
- [ ] `docs/Shared_Storage_Contract.md`
- [ ] 대상 커뮤니티 URL/query 조사 문서
- [ ] 대상 커뮤니티 HTML/API 구조 분석 문서
- [ ] 대상 커뮤니티 JSON schema 초안

초기 코드:

- [ ] `pyproject.toml`
- [ ] `src/<site_scraper>/models/`
- [ ] `src/<site_scraper>/collect/`
- [ ] `src/<site_scraper>/http/`
- [ ] `src/<site_scraper>/parse/`
- [ ] `src/<site_scraper>/outputs/`
- [ ] `src/<site_scraper>/runner/`
- [ ] `src/<site_scraper>/retry/`
- [ ] `src/<site_scraper>/adapters/cli.py`
- [ ] `src/<site_scraper>/adapters/container.py`
- [ ] `src/<site_scraper>/adapters/mcp.py`

초기 테스트:

- [ ] import side-effect test
- [ ] model validation test
- [ ] URL builder test
- [ ] query builder test
- [ ] search parser fixture test
- [ ] post parser fixture test
- [ ] comment parser fixture test
- [ ] checkpoint/resume test
- [ ] CLI validation test
- [ ] container env validation test
- [ ] MCP handler test

운영:

- [ ] 로컬 `direct-post` smoke
- [ ] 로컬 `board-search` smoke
- [ ] resume smoke
- [ ] `retry-failures` smoke
- [ ] 컨테이너 direct-post smoke
- [ ] S3 호환 저장소 output smoke
- [ ] PostgreSQL checkpoint smoke
- [ ] CDK `synth`와 template test
- [ ] Polars JSONL read smoke

## 요약

후속 커뮤니티 스크래퍼는 이 표준 문서의 기능과 유닛 구조를 계승하되, 커뮤니티 API query와 HTML/API parser는 각 커뮤니티에 맞게 새로 작성합니다.

가장 중요한 경계는 아래입니다.

```text
공유:
모델 계약, HTTP runtime, JobRunner, 저장소, checkpoint, CLI 구조, 컨테이너 구조, MCP 구조, 테스트 구조

분리:
URL/query builder, pagination, search parser, post parser, comment parser, media parser, CAPTCHA/block 패턴
```

이 경계를 지키면 여러 커뮤니티 스크래퍼를 같은 운영 방식과 같은 분석 파이프라인 안에 넣을 수 있습니다.
