# Services Design

## Service Layer Overview

Application Design 단계의 service는 orchestration 경계만 정의합니다. URL selector, HTML 파싱 세부, retry 조건, checkpoint edge case는 Functional Design에서 확정합니다.

## ScraperFacade

- **Responsibility**: library, CLI, container, MCP가 공유하는 최상위 API
- **Collaborators**: `JobConfigValidator`, `JobRunner`, `LinkCollector`, `PostWorkerPool`
- **Interactions**:
  - 단건 API는 관련 parser/http/output 없이 필요한 서비스만 호출한다.
  - Job API는 `JobRunner`에 위임한다.

## JobRunner

- **Responsibility**: Job lifecycle orchestration
- **Collaborators**: `LinkCollector`, `PostWorkerPool`, `OutputStorePort`, `CheckpointStorePort`, `LoggerPort`
- **Flow**:
  1. `JobConfig` 검증
  2. checkpoint 생성 또는 resume checkpoint 로드
  3. 링크 수집 worker 시작
  4. 게시글 worker pool 시작
  5. 게시글 저장 성공 후 completed key와 checkpoint 갱신
  6. CAPTCHA/오류/수동 중단 시 `status="stopped"` checkpoint 저장
  7. 정상 완료 시 `status="completed"` checkpoint와 Job report 저장

## LinkCollectorService

- **Responsibility**: 게시글 후보 URL을 순차적으로 수집해 worker queue에 넣음
- **Collaborators**: `HttpClient`, `GallerySearchParser`, `IntegratedSearchParser`, `JobConfig`, `Checkpoint`
- **Supported Modes**:
  - direct post URL
  - gallery search
  - integrated search
  - deep search
  - no-keyword range search
  - realtime keyword search
  - realtime all search
- **Rules**:
  - Job당 한 collector만 실행한다.
  - 후보는 `(gallery_id, post_number)` 기준으로 dedupe한다.
  - 조건 범위 밖이면 mode별 종료 정책을 적용한다.

## PostScrapeService

- **Responsibility**: 게시글 상세 1건을 표준 `PostResult`로 수집
- **Collaborators**: `HttpClient`, `PostParser`, `RepostService`, `CommentService`, `MediaService`
- **Flow**:
  1. 상세 HTML fetch
  2. 접근 불가/CAPTCHA/삭제/성인/로그인 필요 분류
  3. metadata와 body parsing
  4. `(펌)`이면 repost AJAX fetch와 card parsing
  5. 댓글 수집 옵션이 켜져 있으면 댓글 API 호출
  6. media 다운로드 옵션에 따라 URL only 또는 file save 처리
  7. `PostResult` 반환

## RepostService

- **Responsibility**: `(펌)` 게시글의 원 게시글 카드 수집
- **Collaborators**: `RepostParser`, `HttpClient`, `MediaParser`
- **Rules**:
  - raw HTML의 `#pum_container` 존재를 전제하지 않는다.
  - `.write_div script`에서 AJAX request data를 추출한다.
  - 원 게시글 댓글 수는 `repost`에 저장하지 않는다.

## CommentService

- **Responsibility**: 댓글/덧글 API 호출과 계층화
- **Collaborators**: `HttpClient`, `CommentParser`, `PostParser`
- **Rules**:
  - `depth == 0`은 댓글, `depth == 1`은 덧글이다.
  - 덧글 parent는 `c_no`로 연결한다.
  - `memo`는 text와 dccon/media로 분리한다.

## MediaService

- **Responsibility**: 본문 media metadata 추출과 선택적 다운로드
- **Collaborators**: `MediaParser`, `HttpClient`, `MediaStorePort`
- **Rules**:
  - 기본은 URL metadata 저장이다.
  - 다운로드 실패는 게시글 실패가 아니라 media failure로 기록한다.
  - 컨테이너에서는 Garage 기반 S3 호환 store를 사용한다.

## StorageService

- **Responsibility**: 결과, 실패 기록, checkpoint 저장 흐름 조정
- **Collaborators**: `OutputStorePort`, `MediaStorePort`, `CheckpointStorePort`
- **Implementations**:
  - local JSONL and local media
  - local `Checkpoint.json`
  - PostgreSQL checkpoint
  - S3-compatible object storage, Garage as default
- **Rules**:
  - JSONL 결과 저장이 성공한 뒤 checkpoint completed key를 갱신한다.
  - resume Job은 기존 JSONL에 append하지 않고 새 JSONL을 만든다.

## RuntimePolicyService

- **Responsibility**: HTTP runtime policy 구성
- **Collaborators**: `UserAgentProvider`, `ProxyProvider`, `HttpClient`
- **Rules**:
  - global request interval 기본값은 1초다.
  - User-Agent 기본 교체 주기는 요청 10회마다 1회다.
  - Proxy option이 `.env`보다 우선한다.
  - secret은 log에 남기지 않는다.

## CliRuntimeService

- **Responsibility**: 터미널 실행을 core Job으로 변환
- **Collaborators**: `JobConfigValidator`, `ScraperFacade`
- **Rules**:
  - terminal prompt는 adapter 내부에만 둔다.
  - core package import 시 prompt나 network side effect가 없어야 한다.

## ContainerRuntimeService

- **Responsibility**: one-shot worker container 실행 계약 처리
- **Collaborators**: `JobConfigValidator`, `ScraperFacade`, `StorageService`
- **Rules**:
  - env/config로 Job 또는 resume request를 받는다.
  - `RESUME=true`와 `JOB_ID`를 지원한다.
  - S3-compatible env를 사용하고 Garage 전용 API에 묶이지 않는다.

## McpRuntimeService

- **Responsibility**: MCP tool을 core API로 위임
- **Collaborators**: `ScraperFacade`, `JobConfigValidator`
- **Tools**:
  - `search_gallery`
  - `search_integrated`
  - `fetch_post`
  - `fetch_comments`
  - `run_job`
  - `resume_job`
- **Rules**:
  - MCP는 별도 scraper logic을 가지지 않는다.
  - 오류 응답은 secret, raw credential, internal stack trace를 숨긴다.

