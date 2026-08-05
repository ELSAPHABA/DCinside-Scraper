# Application Components

## Package Boundary

1차 구현은 단일 Python 패키지 `dcinside_scraper` 안에서 하위 모듈을 나눕니다.

| Module | Responsibility |
|---|---|
| `core` | public API, 설정 검증, 공통 예외, ports |
| `models` | Pydantic request/result/checkpoint models |
| `parsers` | BeautifulSoup 기반 HTML/API 응답 파싱 |
| `http` | 요청 속도, retry, timeout, User-Agent, Proxy 적용 |
| `jobs` | Job validation, link collection, worker queue orchestration |
| `outputs` | JSONL, media, failure report, checkpoint storage |
| `adapters` | CLI, worker container, MCP adapter |

## Core Components

### PublicApi

- **Purpose**: Python import 사용자를 위한 async API 진입점
- **Responsibilities**: `search_gallery`, `search_integrated`, `fetch_post`, `fetch_comments`, `run_job`, `resume_job` 노출
- **Interface**: async functions returning Pydantic models or async iterables

### JobConfigValidator

- **Purpose**: CLI, container, MCP, library 입력을 같은 기준으로 검증
- **Responsibilities**: Job type, URL, gallery ID, keyword, date range, post number range, realtime env, worker count, storage config validation
- **Interface**: `validate_job_config(raw) -> JobConfig`

### Ports

- **Purpose**: strict ports/adapters 경계
- **Responsibilities**: HTTP, output, media, checkpoint, clock, logger 같은 외부 의존성 protocol 정의
- **Interface**: protocol classes used by services

## Model Components

### ScrapeModels

- **Purpose**: 수집 결과 JSONL 스키마 정의
- **Responsibilities**: `PostResult`, `RepostInfo`, `AuthorInfo`, `ContentBlock`, `MediaItem`, `Comment`, `DcconItem`, `FailureRecord`, `JobReport`
- **Interface**: Pydantic `BaseModel`, `model_dump(mode="json")`

### JobModels

- **Purpose**: Job 실행 입력과 상태 모델 정의
- **Responsibilities**: `JobConfig`, `ScrapeOptions`, `RangeFilter`, `RealtimeOptions`, `StorageConfig`, `WorkerConfig`
- **Interface**: Pydantic validation models

### CheckpointModels

- **Purpose**: 공통 checkpoint/status schema 정의
- **Responsibilities**: `Checkpoint`, `CheckpointStatus`, `StopReason`, 완료 key 집합, 검색 위치, 가능한 queue snapshot
- **Interface**: Pydantic model with JSON round trip support

## Parser Components

### GallerySearchParser

- **Purpose**: 갤러리 목록/검색 HTML에서 게시글 후보 추출
- **Responsibilities**: 게시글 행 파싱, 공지/광고 제외, `(펌)` 목록 판정, `search_next`/`search_prev` 링크 추출, 말머리 탭 파싱
- **Interface**: `parse(html, base_url) -> GallerySearchPage`

### IntegratedSearchParser

- **Purpose**: 통합 검색 HTML에서 게시글 후보와 갤러리 후보 추출
- **Responsibilities**: 검색 결과 item, 페이지 끝, 갤러리 ID/type/name/url, post number 추출
- **Interface**: `parse(html, base_url) -> IntegratedSearchPage`

### PostParser

- **Purpose**: 게시글 상세 HTML에서 표준 게시글 결과의 기본 필드 추출
- **Responsibilities**: title normalization, writer metadata, stats, body text, body links, content blocks, media URL extraction trigger
- **Interface**: `parse(html, url) -> ParsedPost`

### RepostParser

- **Purpose**: `(펌)` 게시글 판정과 원 게시글 카드 파싱
- **Responsibilities**: AJAX form data 추출, AJAX 응답 HTML에서 repost metadata/media/body preview 파싱
- **Interface**: `detect(html) -> RepostRequest | None`, `parse_card(html) -> RepostInfo`

### CommentParser

- **Purpose**: 댓글 API JSON과 `memo` HTML을 댓글/덧글 구조로 변환
- **Responsibilities**: `depth` 기반 계층화, `c_no` parent mapping, text/dccon/media 분리
- **Interface**: `parse(payload) -> list[Comment]`

### MediaParser

- **Purpose**: 본문 이미지, 동영상, YouTube, 링크, 시리즈, 디시콘 metadata 추출
- **Responsibilities**: ordered content block 생성, dc_video 설명 추출, file URL normalization
- **Interface**: `parse_content(write_div) -> list[ContentBlock]`

## HTTP Components

### HttpClient

- **Purpose**: 모든 외부 HTTP 요청 정책의 단일 적용 지점
- **Responsibilities**: global delay, timeout, retry, User-Agent rotation, Proxy, secret masking, CAPTCHA/block response classification
- **Interface**: `get`, `post`, `download`

### UserAgentProvider

- **Purpose**: `user-agents.txt` 로딩과 요청 10회 기본 교체
- **Responsibilities**: one-line parsing, blank skip, default fallback, request counter
- **Interface**: `next_user_agent() -> str`

### ProxyProvider

- **Purpose**: Proxy 설정 우선순위 적용
- **Responsibilities**: CLI option priority, `.env` auto-load, container entrypoint generated `.env`, plaintext warning
- **Interface**: `load_proxy() -> ProxyConfig | None`

## Job Components

### JobRunner

- **Purpose**: 전체 Job lifecycle 조율
- **Responsibilities**: config validation, collector start, worker queue, checkpoint, output commit, stop handling
- **Interface**: `run(config) -> JobReport`, `resume(job_id | None) -> JobReport`

### LinkCollector

- **Purpose**: Job당 단일 순차 링크 탐색
- **Responsibilities**: direct URL, gallery search, integrated search, deep search, no-keyword range, realtime polling, range filter, dedupe
- **Interface**: `collect(config, queue, checkpoint) -> CollectorSummary`

### PostWorkerPool

- **Purpose**: 게시글 상세 병렬 수집
- **Responsibilities**: `asyncio.Queue` 소비, post/comment/repost/media fetch orchestration, failure record, checkpoint tick
- **Interface**: `run(queue, worker_count) -> WorkerSummary`

## Output Components

### OutputStore

- **Purpose**: Job 결과 JSONL 저장 port와 구현체
- **Responsibilities**: local JSONL write, S3-compatible upload for Garage, idempotent post key handling
- **Interface**: `append_post`, `write_failure`, `finalize`

### MediaStore

- **Purpose**: 이미지/동영상/디시콘 다운로드 파일 저장 port와 구현체
- **Responsibilities**: local path storage, S3-compatible object storage, failed media record
- **Interface**: `save_media(url, target_key) -> MediaSaveResult`

### CheckpointStore

- **Purpose**: checkpoint 저장 port와 구현체
- **Responsibilities**: local `Checkpoint.json`, PostgreSQL checkpoint, latest checkpoint lookup, atomic write
- **Interface**: `save`, `load`, `load_latest`

## Adapter Components

### CliAdapter

- **Purpose**: 터미널 UI와 옵션 파싱
- **Responsibilities**: Job type selection, media/dccon option selection, request delay, Proxy/User-Agent import, resume command
- **Interface**: console command entrypoints

### ContainerAdapter

- **Purpose**: one-shot worker container runtime contract
- **Responsibilities**: env/config loading, `.env` proxy injection compatibility, Garage S3 env validation, stdout structured logs
- **Interface**: Docker entrypoint command

### McpAdapter

- **Purpose**: MCP tool 호출을 core API로 위임
- **Responsibilities**: `search_gallery`, `search_integrated`, `fetch_post`, `fetch_comments`, `run_job`, `resume_job`
- **Interface**: MCP tool schemas with masked errors

