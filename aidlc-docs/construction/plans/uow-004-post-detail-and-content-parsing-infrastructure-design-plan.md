# Infrastructure Design 계획 - UOW-004 Post Detail And Content Parsing

이 계획은 `UOW-004 Post Detail And Content Parsing`의 논리 컴포넌트를 실제 실행/검증 인프라 접점에 어떻게 매핑할지 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-004 Post Detail And Content Parsing
- **Functional Design**: 승인됨
- **NFR Requirements**: 승인됨
- **NFR Design**: 승인됨
- **Scope**: import 가능한 게시글 상세/댓글 파싱 라이브러리, UOW-002 `HttpClient` 사용, BeautifulSoup parser, local/CI fixture/PBT 검증, optional live smoke test
- **Likely Infrastructure Scope**: standalone deployment 없음, local/CI 검증 인프라와 HTTP/runtime dependency boundary만 해당
- **Out Of Scope**: JSONL/Garage/PostgreSQL adapter, media file download/storage, queue lifecycle, checkpoint persistence, CLI prompt UX, container/MCP hosting

## Infrastructure Design 작업 체크리스트

- [x] UOW-004 Functional Design 승인 확인
- [x] UOW-004 NFR Design 승인 확인
- [x] Functional/NFR 산출물 확인
- [x] logical components의 인프라 필요 여부 분석
- [x] Infrastructure Design 질문 생성
- [x] Infrastructure Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-004-post-detail-and-content-parsing/infrastructure-design/infrastructure-design.md` 생성
- [x] `aidlc-docs/construction/uow-004-post-detail-and-content-parsing/infrastructure-design/deployment-architecture.md` 생성
- [x] shared infrastructure 산출물 필요 여부 확인

## Infrastructure Design Questions

### Question 1. Deployment Environment

UOW-004 자체를 배포 가능한 런타임으로 볼까요?

A) (권장) 아니요. UOW-004는 import 가능한 게시글 상세/댓글 파싱 라이브러리이며, 독립 서비스/컨테이너 배포는 N/A로 문서화한다.

추천 사유: 이 unit은 `PostResult` 생성까지만 담당합니다. CLI, worker container, MCP hosting은 후속 실행/어댑터 unit에서 다루는 편이 책임이 작습니다.

B) local 개발/검증용 Python 실행 환경만 Infrastructure Design에 포함한다.

C) scraper worker/container 배포 환경까지 UOW-004에서 미리 정의한다.

X) 기타

[Answer]: A

### Question 2. Compute And Parallelism Boundary

UOW-004의 compute/parallelism 인프라는 어디까지 정의할까요?

A) (권장) persistent compute와 worker pool은 없음. 한 `PostRequest` 단위의 상세/하위 AJAX 파싱만 수행하고, 멀티 워커/queue 병렬화는 UOW-005 이후 책임으로 둔다.

추천 사유: 게시글별 병렬 실행은 JobRunner와 checkpoint 설계가 있어야 안전합니다. UOW-004에서 worker pool을 만들 필요는 없습니다.

B) 댓글 페이지 병렬 fetch 옵션만 UOW-004 인프라로 정의한다.

C) 멀티 워커 container sizing과 scale-out 정책까지 정의한다.

X) 기타

[Answer]: A

### Question 3. HTTP Client And Network Boundary

네트워크 인프라와 `HttpClient` 사용 경계는 어떻게 둘까요?

A) (권장) UOW-004는 UOW-002 `HttpClient`를 주입받아 사용하고, proxy/User-Agent/rate limit/cookie lifecycle/retry를 직접 구성하지 않는다. 게시글 상세, `(펌)` AJAX, DC video iframe, 댓글 AJAX 모두 같은 client 경계를 사용한다.

추천 사유: HTTP 정책은 이미 UOW-002 책임입니다. UOW-004는 파싱과 `PostResult` 조립만 소유하면 됩니다.

B) UOW-004 service가 자체 `httpx.AsyncClient`를 생성한다.

C) UOW-004에서 proxy/User-Agent/rate limit 설정까지 다시 노출한다.

X) 기타

[Answer]: A

### Question 4. Runtime Configuration Boundary

환경변수, 파일, CLI 입력 같은 runtime config는 UOW-004에서 어디까지 다룰까요?

A) (권장) UOW-004는 UOW-001에서 검증된 `PostRequest`, `CommentRequest`, `ScrapeOptions`와 호출자가 넘긴 in-memory 옵션만 소비한다. `.env`, `user-agents.txt`, terminal prompt, live smoke env parsing은 직접 다루지 않는다.

추천 사유: import side effect를 막고, 실행 환경별 입력 방식은 CLI/container/JobRunner unit에서 처리할 수 있습니다.

B) UOW-004가 live smoke와 댓글 상한 관련 env var만 직접 읽는다.

C) UOW-004가 `.env`, `user-agents.txt`, CLI 옵션을 모두 직접 읽는다.

X) 기타

[Answer]: A

### Question 5. Fixture And Test Data Infrastructure

parser fixture와 테스트 데이터는 어떻게 관리할까요?

A) (권장) `tests/fixtures/post_detail/`에 정적 sanitized HTML/JSON fixture를 저장하고, 테스트 실행 중 외부 사이트에서 fixture를 다운로드하지 않는다.

추천 사유: DOM/AJAX parser 테스트는 재현성이 중요합니다. live 사이트 상태에 의존하면 기본 테스트가 flaky해집니다.

B) 테스트 실행 시 DCinside 페이지를 다운로드해 fixture를 갱신한다.

C) fixture 없이 live smoke test만 사용한다.

X) 기타

[Answer]: A

### Question 6. Live Smoke Test Infrastructure

DCinside live smoke test는 인프라 관점에서 어떻게 둘까요?

A) (권장) 기본 CI와 unit test에서는 제외하고, `DCINSIDE_LIVE_SMOKE_ENABLED=true`일 때만 별도 marker로 게시글 1개와 댓글 1페이지 테스트를 실행한다고 문서화한다.

추천 사유: 외부 사이트 상태와 차단 정책에 따른 flaky test를 기본 검증 경로에서 분리할 수 있습니다.

B) 모든 CI에서 live smoke test를 필수로 실행한다.

C) live smoke test 경로를 아예 문서화하지 않는다.

X) 기타

[Answer]: A

### Question 7. Output And Media Infrastructure

UOW-004에서 JSONL, Garage, media storage 같은 출력 인프라를 확정할까요?

A) (권장) 확정하지 않는다. UOW-004는 URL/metadata/content block/comment가 포함된 `PostResult`만 반환하고, JSONL/Garage/media file download는 UOW-006에서 매핑한다.

추천 사유: 이 unit에 저장소를 넣으면 파서 테스트와 저장소 테스트가 섞입니다. 파일 저장은 별도 unit이 맡는 편이 작고 안전합니다.

B) metadata-only JSONL 파일 위치만 UOW-004에서 정한다.

C) Garage object key, media path, JSONL append 정책까지 지금 설계한다.

X) 기타

[Answer]: A

### Question 8. Monitoring And Shared Infrastructure

관측성 및 shared infrastructure는 어디까지 정의할까요?

A) (권장) 외부 monitoring stack, Garage, PostgreSQL, queue는 N/A로 둔다. UOW-001 `LoggerPort`로 safe structured detail event를 내보내는 계약만 문서화한다.

추천 사유: 아직 실행 중인 worker service가 없습니다. Prometheus/OpenTelemetry, PostgreSQL, Garage, queue는 실제 runtime/storage 배포 unit에서 붙이면 충분합니다.

B) local JSON log 파일 위치만 정한다.

C) Prometheus/OpenTelemetry, Garage, PostgreSQL, queue까지 지금 정의한다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-004 Infrastructure Design 산출물 2개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 Code Generation으로 넘어가지 않습니다.

## 검토 결과

- 모든 답변은 A로 확정되었습니다.
- 답변 간 충돌은 없습니다.
- follow-up 질문은 필요하지 않습니다.
- shared infrastructure 산출물은 필요하지 않습니다.
- 산출물 생성 후 UOW-004 Infrastructure Design Review 단계에서 사용자 승인을 대기합니다.
