# Component Methods

상세 business rule은 Functional Design에서 고정합니다. 여기서는 컴포넌트 경계와 method contract만 정의합니다.

## Core

### PublicApi

| Method | Input | Output | Purpose |
|---|---|---|---|
| `search_gallery` | `GallerySearchRequest` | `GallerySearchPage` | 갤러리 검색 결과 한 구간을 조회 |
| `search_integrated` | `IntegratedSearchRequest` | `IntegratedSearchPage` | 통합 검색 결과 한 페이지를 조회 |
| `fetch_post` | `PostRequest` | `PostResult` | 게시글 상세를 표준 JSON 모델로 수집 |
| `fetch_comments` | `CommentRequest` | `list[Comment]` | 댓글/덧글만 수집 |
| `run_job` | `JobConfig` | `JobReport` | Job 전체 실행 |
| `resume_job` | `job_id: str | None` | `JobReport` | checkpoint에서 Job 재개 |

### JobConfigValidator

| Method | Input | Output | Purpose |
|---|---|---|---|
| `validate_job_config` | `Mapping[str, Any]` | `JobConfig` | 모든 adapter 입력을 공통 Job 설정으로 변환 |
| `validate_realtime_options` | `Mapping[str, str]` | `RealtimeOptions` | realtime env 조합 검증 |
| `validate_storage_config` | `Mapping[str, str]` | `StorageConfig` | local, PostgreSQL, S3-compatible 설정 검증 |
| `validate_resume_request` | `job_id: str | None` | `ResumeRequest` | 재개 요청 검증 |

## Models

### Pydantic Result Models

| Model | Key Fields | Purpose |
|---|---|---|
| `PostResult` | `scrap_timestamp`, `gallery_id`, `post_number`, `title`, `content`, `images`, `comments`, `is_repost`, `repost` | JSONL 한 줄 |
| `RepostInfo` | `gallery_id`, `gallery_name`, `post_number`, `author`, `nickname_type`, `views`, `recommendations` | `(펌)` 원 게시글 metadata |
| `ContentBlock` | `type`, `text`, `url`, `metadata` | 본문 텍스트/이미지/동영상/YouTube/link/series 순서 보존 |
| `Comment` | `comment_id`, `parent_id`, `depth`, `author`, `memo_text`, `dccons` | 댓글/덧글 구조 |
| `Checkpoint` | `job_id`, `status`, `reason`, `search_position`, `completed_keys`, `updated_at` | 중단점 저장/재개 |

## Parsers

### GallerySearchParser

| Method | Input | Output | Purpose |
|---|---|---|---|
| `parse` | `html: str, base_url: str` | `GallerySearchPage` | 목록 HTML 파싱 |
| `parse_rows` | `soup: BeautifulSoup` | `list[PostCandidate]` | 게시글 후보 행 추출 |
| `parse_paging` | `soup: BeautifulSoup` | `SearchPaging` | `search_next`, `search_prev`, page links 추출 |
| `parse_head_tabs` | `html: str` | `list[HeadTab]` | 마이너 갤러리 말머리 탭 추출 |

### IntegratedSearchParser

| Method | Input | Output | Purpose |
|---|---|---|---|
| `parse` | `html: str, base_url: str` | `IntegratedSearchPage` | 통합 검색 page 파싱 |
| `parse_results` | `soup: BeautifulSoup` | `list[PostCandidate]` | 결과 게시글 후보 추출 |
| `parse_last_page` | `soup: BeautifulSoup` | `int | None` | 마지막 페이지 번호 추출 |
| `extract_gallery_candidate` | `PostCandidate` | `GalleryCandidate | None` | 심층검색용 갤러리 후보 생성 |

### PostParser

| Method | Input | Output | Purpose |
|---|---|---|---|
| `parse` | `html: str, url: str` | `ParsedPost` | 상세 HTML 기본 파싱 |
| `parse_metadata` | `soup: BeautifulSoup` | `PostMetadata` | 제목, 작성자, 날짜, stats 추출 |
| `normalize_title` | `title: str, is_repost: bool` | `str` | `(펌)` 표시 제거 |
| `parse_body` | `soup: BeautifulSoup` | `BodyParseResult` | 본문 텍스트, 링크, content blocks 추출 |
| `classify_unavailable` | `html: str, status_code: int` | `UnavailableReason | None` | 삭제/로그인/성인/CAPTCHA 분류 |

### RepostParser

| Method | Input | Output | Purpose |
|---|---|---|---|
| `detect_repost` | `html: str` | `bool` | 상세 HTML 기준 `(펌)` 판정 |
| `extract_ajax_request` | `html: str` | `RepostAjaxRequest | None` | `/ajax/pum_ajax/get_contents` form data 추출 |
| `parse_card` | `html: str` | `RepostInfo` | AJAX 응답 카드 metadata 파싱 |
| `parse_card_media` | `html: str` | `list[MediaItem]` | 원글 카드 이미지 추출 |

### CommentParser

| Method | Input | Output | Purpose |
|---|---|---|---|
| `parse_comment_payload` | `payload: Mapping[str, Any]` | `list[Comment]` | 댓글 API JSON 파싱 |
| `parse_memo` | `memo_html: str` | `MemoContent` | 텍스트, 디시콘, media 분리 |
| `link_replies` | `comments: list[Comment]` | `list[Comment]` | `c_no` 기반 parent mapping |

### MediaParser

| Method | Input | Output | Purpose |
|---|---|---|---|
| `parse_content_blocks` | `write_div: Tag` | `list[ContentBlock]` | 본문 순서 보존 content 추출 |
| `extract_images` | `write_div: Tag` | `list[MediaItem]` | 이미지 URL 후보 추출 |
| `extract_dc_video` | `write_div: Tag` | `list[MediaItem]` | DC 동영상과 설명 추출 |
| `extract_links` | `write_div: Tag` | `list[ContentLink]` | 본문 링크 추출 |
| `extract_series` | `write_div: Tag` | `list[SeriesItem]` | 시리즈/게시글 모음 링크 추출 |

## HTTP

### HttpClient

| Method | Input | Output | Purpose |
|---|---|---|---|
| `get` | `url: str, headers: dict | None` | `HttpResponse` | GET 요청 |
| `post` | `url: str, data: Mapping, headers: dict | None` | `HttpResponse` | POST 요청 |
| `download` | `url: str` | `bytes` | media 다운로드 |
| `classify_response` | `HttpResponse` | `ResponseKind` | 정상/CAPTCHA/차단/오류 분류 |
| `close` | None | `None` | httpx client 종료 |

### UserAgentProvider

| Method | Input | Output | Purpose |
|---|---|---|---|
| `load` | `path: Path` | `UserAgentProvider` | `user-agents.txt` 로드 |
| `next_user_agent` | None | `str` | 요청 카운터 기반 User-Agent 선택 |

### ProxyProvider

| Method | Input | Output | Purpose |
|---|---|---|---|
| `load_from_cli_or_env` | `cli_proxy: ProxyConfig | None, env_path: Path` | `ProxyConfig | None` | Proxy 우선순위 적용 |
| `to_httpx_config` | `ProxyConfig` | `dict` | httpx proxy 설정 변환 |

## Jobs

### JobRunner

| Method | Input | Output | Purpose |
|---|---|---|---|
| `run` | `JobConfig` | `JobReport` | Job 신규 실행 |
| `resume` | `ResumeRequest` | `JobReport` | checkpoint 기반 재개 |
| `stop` | `StopReason` | `Checkpoint` | 최종 checkpoint 저장 후 중단 |
| `record_success` | `PostResult` | `None` | 결과 저장 후 completed key/checkpoint 갱신 |
| `record_failure` | `FailureRecord` | `None` | 실패 기록 |

### LinkCollector

| Method | Input | Output | Purpose |
|---|---|---|---|
| `collect` | `JobConfig, Queue[PostCandidate]` | `CollectorSummary` | Job type별 링크 수집 |
| `collect_gallery_search` | `GallerySearchConfig, Queue` | `CollectorSummary` | 갤러리 내 검색 |
| `collect_integrated_search` | `IntegratedSearchConfig, Queue` | `CollectorSummary` | 통합 검색 |
| `collect_deep_search` | `DeepSearchConfig, Queue` | `CollectorSummary` | 통합 검색 후보 갤러리별 재검색 |
| `collect_no_keyword_range` | `NoKeywordRangeConfig, Queue` | `CollectorSummary` | 작성일 이동 기반 노키워드 범위 수집 |
| `collect_realtime` | `RealtimeConfig, Queue` | `CollectorSummary` | 실시간 keyword/all 반복 수집 |

### PostWorkerPool

| Method | Input | Output | Purpose |
|---|---|---|---|
| `run` | `Queue[PostCandidate], worker_count: int` | `WorkerSummary` | 게시글 worker 병렬 실행 |
| `fetch_one` | `PostCandidate` | `PostResult` | 게시글 상세 1건 수집 |
| `handle_failure` | `PostCandidate, Exception` | `FailureRecord` | 실패 분류와 기록 생성 |

## Outputs

### OutputStorePort

| Method | Input | Output | Purpose |
|---|---|---|---|
| `append_post` | `PostResult` | `StoredObjectRef` | JSONL에 게시글 한 줄 저장 |
| `write_failure` | `FailureRecord` | `StoredObjectRef` | 실패 기록 저장 |
| `finalize` | `JobReport` | `StoredObjectRef` | Job report와 remote upload 완료 |

### MediaStorePort

| Method | Input | Output | Purpose |
|---|---|---|---|
| `save_media` | `MediaItem, bytes` | `MediaSaveResult` | media 파일 저장 |
| `save_metadata_only` | `MediaItem` | `MediaSaveResult` | URL/meta만 기록 |

### CheckpointStorePort

| Method | Input | Output | Purpose |
|---|---|---|---|
| `save` | `Checkpoint` | `None` | 원자적 checkpoint 저장 |
| `load` | `job_id: str` | `Checkpoint` | 특정 checkpoint 로드 |
| `load_latest` | None | `Checkpoint | None` | 최신 checkpoint 로드 |

## Adapters

### CliAdapter

| Method | Input | Output | Purpose |
|---|---|---|---|
| `main` | `argv: list[str]` | `int` | CLI 실행 |
| `build_job_config` | `argparse.Namespace` | `JobConfig` | CLI args를 JobConfig로 변환 |

### ContainerAdapter

| Method | Input | Output | Purpose |
|---|---|---|---|
| `main` | `env: Mapping[str, str]` | `int` | one-shot container 실행 |
| `load_runtime_config` | `env: Mapping[str, str]` | `JobConfig | ResumeRequest` | env 기반 실행 계약 파싱 |

### McpAdapter

| Tool | Input | Output | Purpose |
|---|---|---|---|
| `search_gallery` | `GallerySearchRequest` | `GallerySearchPage` | 갤러리 검색 tool |
| `search_integrated` | `IntegratedSearchRequest` | `IntegratedSearchPage` | 통합 검색 tool |
| `fetch_post` | `PostRequest` | `PostResult` | 게시글 fetch tool |
| `fetch_comments` | `CommentRequest` | `list[Comment]` | 댓글 fetch tool |
| `run_job` | `JobConfig` | `JobReport` | Job 전체 실행 tool |
| `resume_job` | `ResumeRequest` | `JobReport` | checkpoint 재개 tool |

