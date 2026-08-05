# Application Design

## Summary

이 설계는 디시인사이드 스크래퍼를 단일 Python 패키지 `dcinside_scraper`로 구현하되, strict ports/adapters 경계를 둡니다.

확정된 주요 결정:

- 모델은 Pydantic을 사용한다.
- public API는 async를 기본으로 한다.
- `JobRunner`가 link collector와 post worker queue를 조율한다.
- HTTP 요청 정책은 단일 `HttpClient`가 담당한다.
- 저장소는 ports/adapters 구조로 분리한다.
- 컨테이너 JSONL/media 출력은 Garage 기반 S3 호환 오브젝트 스토리지를 기본으로 한다.
- MCP는 검색/단건 fetch뿐 아니라 Job 실행과 checkpoint resume도 제공한다.

## Components

자세한 컴포넌트 정의는 `components.md`를 기준으로 합니다.

핵심 컴포넌트:

- `PublicApi`
- `JobConfigValidator`
- `ScrapeModels`, `JobModels`, `CheckpointModels`
- `GallerySearchParser`, `IntegratedSearchParser`, `PostParser`, `RepostParser`, `CommentParser`, `MediaParser`
- `HttpClient`, `UserAgentProvider`, `ProxyProvider`
- `JobRunner`, `LinkCollector`, `PostWorkerPool`
- `OutputStore`, `MediaStore`, `CheckpointStore`
- `CliAdapter`, `ContainerAdapter`, `McpAdapter`

## Services

자세한 service orchestration은 `services.md`를 기준으로 합니다.

핵심 서비스:

- `ScraperFacade`: CLI, library, container, MCP 공통 facade
- `JobRunner`: Job lifecycle orchestration
- `LinkCollectorService`: 검색/범위/실시간/심층검색 링크 수집
- `PostScrapeService`: 게시글 상세 수집
- `RepostService`: `(펌)` AJAX 카드 수집
- `CommentService`: 댓글/덧글 계층화
- `MediaService`: media metadata와 선택적 다운로드
- `StorageService`: JSONL, media, checkpoint 저장 흐름
- `RuntimePolicyService`: request delay, User-Agent, Proxy 정책
- `CliRuntimeService`, `ContainerRuntimeService`, `McpRuntimeService`

## Method Contracts

자세한 method signature는 `component-methods.md`를 기준으로 합니다.

public API 최소 contract:

| Method | Purpose |
|---|---|
| `search_gallery(request)` | 갤러리 검색 결과 한 구간 조회 |
| `search_integrated(request)` | 통합 검색 결과 한 페이지 조회 |
| `fetch_post(request)` | 게시글 상세 수집 |
| `fetch_comments(request)` | 댓글/덧글 수집 |
| `run_job(config)` | Job 전체 실행 |
| `resume_job(request)` | checkpoint 기반 재개 |

## Dependencies

자세한 의존 관계는 `component-dependency.md`를 기준으로 합니다.

핵심 규칙:

- adapter는 core service를 호출만 한다.
- parser는 network나 storage에 의존하지 않는다.
- 모든 network 요청은 `HttpClient`를 통과한다.
- 모든 output/checkpoint/media 저장은 port를 통과한다.
- post result 저장 성공 후 checkpoint를 갱신한다.

## Implementation Notes For Later Stages

- Functional Design에서 selector별 파싱 규칙, 실패 분류, retry 조건, checkpoint edge case를 확정한다.
- Units Generation에서는 이 설계를 구현 가능한 작업 단위로 나눈다.
- NFR 단계에서는 Security Baseline, Resiliency Baseline, PBT 범위를 구체화한다.

