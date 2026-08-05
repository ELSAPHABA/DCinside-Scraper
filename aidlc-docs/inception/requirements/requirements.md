# 요구사항

## 의도 분석

- **사용자 요청**: `docs\Function_Specification.md`를 기반으로 디시인사이드 스크래퍼를 AI-DLC 절차에 따라 구현한다.
- **요청 유형**: 신규 프로젝트
- **프로젝트 유형**: Greenfield
- **주요 요구사항 출처**: `docs\Function_Specification.md`
- **범위 추정**: 시스템 전체
- **복잡도 추정**: 복잡함
- **주요 사용 사례**: 통합 커뮤니티 스크래핑 시스템에서 디시인사이드 전용 워커로 사용
- **1차 구현 목표**: CLI, Python 라이브러리 API, 비동기 멀티 워커 수집, 워커 컨테이너, MCP 도구

## 기능 요구사항

### FR-001. 지원 실행 방식

시스템은 다음 실행 방식을 지원해야 합니다.

- 터미널 기반 CLI
- Python 라이브러리 import API
- 비동기 멀티 워커 스크래퍼 런타임
- 향후 통합 커뮤니티 스크래핑 시스템용 워커 컨테이너
- MCP 도구 인터페이스

1차 UI는 터미널 기반이어야 합니다. GUI 또는 Web UI는 향후 범위입니다.

### FR-002. 공개 콘텐츠 수집 범위

스크래퍼는 공개된 디시인사이드 게시글과 댓글만 수집해야 합니다.

1차 구현에서 제외하는 범위:

- 로그인이 필요한 페이지
- 성인 인증 페이지
- 삭제되었거나 접근할 수 없는 게시글
- CAPTCHA 우회 또는 자동 CAPTCHA 풀이

### FR-003. 수집 진입점

스크래퍼는 다음 1차 수집 진입점을 모두 지원해야 합니다.

- 게시글 URL 직접 입력
- 갤러리 내 검색 결과 기반 수집
- 통합 검색 결과 기반 수집
- 심층검색 기반 수집
- 노키워드 기간 및 글번호 범위 수집
- 실시간 키워드 수집
- 실시간 전체 수집

### FR-004. HTTP 및 파싱 런타임

스크래퍼는 다음을 사용해야 합니다.

- 비동기 HTTP 요청과 멀티 워커 수집을 위한 `httpx`와 `asyncio`
- HTML 파싱을 위한 BeautifulSoup
- JSON/JSONL 저장을 위한 표준 `json` 지원

스크래퍼 런타임은 Playwright에 의존하면 안 됩니다.

### FR-005. 갤러리 내 검색 수집

갤러리 내 검색 페이지에서 스크래퍼는 다음을 수행해야 합니다.

- 일반 갤러리는 `/board/lists/`, 마이너 갤러리는 `/mgallery/board/lists/` 요청
- `id`, `s_type`, `s_keyword`, `page`, 선택적 `search_pos` 사용
- 최초 요청은 `search_pos`를 생략하거나 빈 값으로 시작
- `a.search_next[href]`와 `a.search_prev[href]`를 그대로 따라감
- 최신 글번호에서 `search_pos`를 직접 계산하지 않음
- `.gall_listwrap.list tbody tr.ub-content.us-post`로 게시글 행 파싱
- `.gall_num`이 `-`이거나 `us-post`가 없는 광고/공지 행 제외

### FR-006. 통합 검색 수집

통합 검색에서 스크래퍼는 다음을 수행해야 합니다.

- 최신순 및 정확도순 URL 형식 지원
- 키워드는 UTF-8 percent encoding 후 `%`를 `.`로 치환
- `a.page_end[href]` 또는 페이징 링크에서 페이지 번호 추출
- `.integrate_cont.sch_result.result_all ul.sch_result_list > li`에서 결과 항목 파싱
- 상세 URL에서 제목 링크, 미리보기, 갤러리명/링크, 날짜, 갤러리 ID, 글번호, 갤러리 타입 추출

### FR-007. 링크 수집 워커

링크 수집 워커는 다음을 수행해야 합니다.

- Job마다 단일 순차 워커로 실행
- 갤러리 내 검색은 `page`와 `search_pos` 순서로 탐색
- 통합 검색은 페이지와 정렬 URL 순서로 탐색
- 심층검색은 통합 검색으로 갤러리 후보를 먼저 찾은 뒤 갤러리별 키워드 검색을 순차 탐색
- 설정된 글번호 범위와 작성일 범위로 링크 필터링
- 설정된 종료 조건 중 먼저 도달한 조건에서 중단
- `(gallery_id, post_no)` 기준으로 중복 제거
- 조건에 맞는 게시글 링크를 게시글 워커용 Queue에 추가

### FR-008. 게시글 수집 워커

게시글 수집 워커는 다음을 수행해야 합니다.

- `asyncio.Queue`를 사용해 병렬 실행
- 게시글 상세 페이지 fetch
- 게시글 메타데이터, 본문, 이미지 URL, 댓글, 덧글, `(펌)` 메타데이터 수집
- 실패한 게시글 요청은 설정된 횟수까지 재시도
- 재시도 한도 초과 시 `(gallery_id, post_number, url, reason)` 형식으로 실패 기록

### FR-009. 게시글 메타데이터 수집

각 게시글에 대해 다음을 수집해야 합니다.

- 갤러리 ID
- 글번호
- `(펌)` 여부
- 제목
- 작성자
- 닉네임 유형
- 작성일
- 조회수
- 추천수
- 비추천수
- 댓글 수
- 본문 텍스트
- 본문 링크
- 이미지 URL
- 댓글과 덧글

### FR-010. `(펌)` 게시글 판정

스크래퍼는 디시인사이드 `(펌)` 게시글을 지원해야 합니다.

목록 페이지 기준:

- `.gall_tit > b.font_blue009` 텍스트가 `(펌)`이면 `is_repost=true`
- `.gall_tit span.mark`는 검색어 하이라이트일 수 있으므로 단독으로 `(펌)` 판정에 사용하지 않음

상세 페이지 기준:

- `h3.title > b.font_blue009` 텍스트가 `(펌)`이면 `is_repost=true`
- `.writing_view_box .write_div script`에 `/ajax/pum_ajax/get_contents`가 있으면 `is_repost=true`

### FR-011. `(펌)` 제목 정규화

게시글이 `(펌)`이면 JSON의 `title` 필드에 `(펌)` 표시를 저장하지 않아야 합니다.

예시:

- 원본 제목: `(펌) 이거 뭐냐?`
- 저장 제목: `이거 뭐냐?`

### FR-012. `(펌)` 원 게시글 메타데이터

`(펌)` 게시글의 JSON에는 다음이 포함되어야 합니다.

- `"is_repost": true`
- 원 게시글 메타데이터를 담은 `"repost"` 객체

`repost` 객체에는 다음이 포함되어야 합니다.

- 원 게시글 갤러리 ID
- 원 게시글 갤러리명
- 원 게시글 글번호
- 원 게시글 작성자
- 원 게시글 닉네임 유형
- 원 게시글 조회수
- 원 게시글 추천수

원 게시글 댓글 수는 `repost` 객체에 포함하지 않습니다.

### FR-013. `(펌)` 원 게시글 카드 요청

BeautifulSoup은 JavaScript를 실행하지 않으므로, 스크래퍼는 raw HTML에 렌더링된 `#pum_container`가 있을 것이라고 기대하면 안 됩니다.

`(펌)` 게시글에서 스크래퍼는 다음을 수행해야 합니다.

- `.writing_view_box .write_div script` 검사
- `/ajax/pum_ajax/get_contents` 요청 데이터 추출
- `https://gall.dcinside.com/ajax/pum_ajax/get_contents`로 POST 요청
- 반환된 HTML을 BeautifulSoup으로 파싱

POST form data에는 다음이 포함되어야 합니다.

- `ci_t`
- `_GALLTYPE_`
- `id`
- `no`

요청 헤더에는 다음이 포함되어야 합니다.

- `X-Requested-With: XMLHttpRequest`
- `Content-Type: application/x-www-form-urlencoded; charset=UTF-8`

### FR-014. `(펌)` 원 게시글 카드 파싱

`(펌)` AJAX 응답 HTML에서 다음을 파싱해야 합니다.

- `header.gallview_head a[href*="/board/lists"]`에서 원 게시글 갤러리명/링크
- 갤러리 링크 또는 원 게시글 링크의 `id` 쿼리에서 원 게시글 갤러리 ID
- `.cloned_card_body > a[href*="/board/view"]`의 `no` 쿼리에서 원 게시글 글번호
- `header.gallview_head .gall_writer .nickname`에서 원 게시글 작성자
- `.nickname .ip`가 있으면 `floating`, 없으면 `fixed`
- `header.gallview_head .gall_count`에서 원 게시글 조회수
- `header.gallview_head .gall_reply_num`에서 원 게시글 추천수

### FR-015. 본문 텍스트 수집

일반 게시글의 본문 텍스트는 비본문 요소를 제거한 `.writing_view_box .write_div`에서 추출해야 합니다.

`(펌)` 게시글에서는 원글 카드의 갤러리명/조회수/추천수가 본문에 섞이지 않도록 해야 합니다. `.cloned_card_body p`가 있으면 이를 `(펌)` 본문 미리보기/본문 소스로 우선 사용해야 합니다.

### FR-016. 이미지 수집

1차 구현은 기본적으로 이미지 URL을 수집해야 합니다.

각 Job 실행 전에 터미널 UI에서 사용자가 다음 중 하나를 선택할 수 있어야 합니다.

- 이미지 URL만 저장
- `images/<gallery_id>/<post_no>/` 아래에 이미지 파일 다운로드

일반 게시글의 이미지 수집은 다음을 사용해야 합니다.

- `.write_div img[data-fileno]`
- URL 우선순위: `data-original`, `src`, `onclick`의 `imgPop(...)`

`(펌)` 카드 이미지 수집에는 다음도 포함해야 합니다.

- `#pum_container.cloned_card .cloned_media img[src]`
- AJAX 응답의 `.cloned_media img[src]`

`(펌)` 카드 이미지는 `data-fileno`가 없을 수 있으므로, 해당 이미지는 `src` URL 기준으로 식별해야 합니다.

### FR-017. 댓글 및 덧글 수집

댓글과 덧글 수집은 기본 활성화되어야 합니다.

스크래퍼는 다음을 수행해야 합니다.

- `POST https://gall.dcinside.com/board/comment/`로 댓글 요청
- 댓글 요청 전에 게시글 HTML에서 필요한 hidden 값을 추출
- JSON `comments` 파싱
- `depth == 0`은 댓글로 처리
- `depth == 1`은 덧글로 처리
- 덧글의 부모 댓글 번호는 `c_no` 사용
- `memo`에서 텍스트와 디시콘 콘텐츠 파싱

### FR-018. 디시콘 처리

각 Job 실행 전에 터미널 UI에서 사용자가 다음 중 하나를 선택할 수 있어야 합니다.

- 디시콘 이미지/영상 URL과 메타데이터만 저장
- 디시콘 파일 다운로드

디시콘 메타데이터에는 가능한 경우 `src`, `alt`, `title`, `conalt` 값을 포함해야 합니다.

### FR-019. JSONL Job 출력

기본 결과 저장 방식은 Job당 하나의 JSONL 파일이어야 합니다.

수집된 게시글 하나는 JSON 객체 한 줄로 append되어야 합니다.

JSONL 결과 검증과 가공의 기본 DataFrame 라이브러리는 Polars여야 합니다.

로컬 환경에서는 Job JSONL 파일을 실행 파일과 같은 위치에 저장해야 합니다.

단일 컨테이너 환경에서는 Job JSONL 파일과 다운로드 미디어를 Garage 기반 S3 호환 오브젝트 스토리지에 저장해야 합니다.

향후 통합 플랫폼/클라우드 환경에서는 Job JSONL 파일과 미디어 저장소를 S3 호환 저장소로 확장할 수 있어야 합니다.

SeaweedFS는 대량 미디어/소파일 저장, FUSE, Iceberg 요구가 생길 때 대체 저장소로 검토할 수 있어야 합니다.

체크포인트에서 재개한 Job은 기존 JSONL 파일에 이어 쓰지 않고 새 JSONL 파일을 생성하여 중단점 이후부터 기록해야 합니다.

### FR-020. 중단점 저장

스크래퍼는 작업 상태와 체크포인트를 모든 커뮤니티 스크래퍼가 공유할 수 있는 공통 JSON 스키마로 저장해야 합니다.

공통 상태 스키마에는 최소한 다음 필드가 포함되어야 합니다.

- `job_id`
- `site_id`
- `board_id`
- `last_completed_post_id`
- `last_completed_url`
- `scraping_processed_count`
- `worker_id`
- `lease_until`
- `status`
- `updated_at`

`status` 값은 `running`, `stopped`, `completed` 중 하나여야 합니다.

스크래퍼는 정상 진행 중 `status="running"`을 기록해야 합니다.

스크래퍼는 다음 상황에서 체크포인트를 저장해야 합니다.

- 게시글 10개 처리 완료마다
- 사용자가 Job을 중단한 경우
- 복구 불가능한 오류가 발생한 경우
- CAPTCHA 또는 차단 의심 응답이 감지된 경우
- 정상 완료된 경우

사용자가 중단한 경우 프로세스 종료 전에 반드시 최종 중단점을 저장해야 합니다.

수동 중단, 오류, CAPTCHA, timeout, lease 만료로 중단되는 경우 `status="stopped"`를 저장해야 합니다.

중단 사유 `reason`은 `captcha`, `manual_stop`, `error`, `timeout`, `lease_expired` 중 하나여야 합니다.

CAPTCHA 감지 시 재시도 가능 시간이 있으면 `retry_after`에 UTC ISO-8601 값으로 저장하고, 없으면 `null`이어야 합니다.

체크포인트 저장은 원자적으로 처리되어야 합니다.

게시글 결과 저장이 성공한 후에만 체크포인트의 마지막 완료 위치를 갱신해야 합니다.

### FR-021. 재개 처리

스크래퍼는 로컬 환경에서 `Checkpoint.json`을 사용해 수집을 재개할 수 있어야 합니다.

중단점에는 재개에 필요한 다음 정보를 충분히 포함해야 합니다.

- Job 유형
- 검색 조건
- 수집 옵션
- 해당 시 현재 `search_pos`
- 현재 페이지
- 마지막으로 처리한 글번호
- 가능한 경우 Queue 또는 남은 링크 상태

로컬 환경에서는 터미널 옵션으로 체크포인트 `job_id`를 입력받아 재개할 수 있어야 합니다.

컨테이너 환경에서는 `docker run` 환경변수 `RESUME=true`, `JOB_ID=<checkpoint job_id>`로 재개할 수 있어야 합니다.

재개 요청에서 `JOB_ID`가 없으면 가장 최근 체크포인트를 자동으로 선택해야 합니다.

이미 저장된 게시글은 `(site_id, board_id, post_id)` 또는 커뮤니티별 고유 key로 중복 저장되지 않아야 합니다.

### FR-022. CAPTCHA 및 차단 감지

CAPTCHA 또는 차단 의심 응답이 감지되면 스크래퍼는 다음을 수행해야 합니다.

- 현재 Job 즉시 중단
- `status="stopped"`로 변경
- 최종 체크포인트 저장
- 저장한 체크포인트 `job_id`를 터미널과 로그에 출력
- 터미널에 재개 명령 안내 출력

스크래퍼는 CAPTCHA 우회를 구현하면 안 됩니다.

### FR-023. 요청 속도 조절

기본 요청 간격은 전역 1초여야 합니다.

터미널 옵션에서 사용자가 전역 요청 간격을 변경할 수 있어야 합니다.

요청 지연은 다음 요청에 일관되게 적용되어야 합니다.

- 갤러리 목록 요청
- 통합 검색 요청
- 게시글 상세 요청
- `(펌)` AJAX 요청
- 댓글 API 요청
- 이미지/디시콘 다운로드 요청

### FR-024. User-Agent Mixer

실행 파일 옆에 `user-agents.txt`가 있으면 스크래퍼는 이를 자동 사용해야 합니다.

`user-agents.txt`가 없거나 유효한 항목이 없으면 기본 User-Agent를 사용해야 합니다.

터미널 옵션에서 파일 선택 창을 열어 User-Agent 목록을 `user-agents.txt`로 가져올 수 있어야 합니다.

`user-agents.txt`는 한 줄에 User-Agent 하나를 저장하며 빈 줄은 무시해야 합니다.

기본 User-Agent 교체 주기는 요청 10회마다 1회여야 하며, 터미널 옵션에서 요청 횟수 기준으로 변경할 수 있어야 합니다.

컨테이너 이미지에는 `user-agents.txt`를 포함해야 합니다.

### FR-025. Proxy Profile

Proxy 설정은 실행 파일 옆 `.env` 파일로 저장해야 합니다.

사용자가 터미널에서 Proxy 옵션을 켠 경우 해당 입력값을 최우선으로 사용해야 합니다.

사용자가 Proxy 옵션을 켜지 않았고 `.env`가 있으면 스크래퍼는 `.env`의 Proxy 변수를 자동 사용해야 합니다.

`.env`가 없거나 유효한 Proxy 변수가 없으면 Proxy 사용은 비활성화됩니다.

터미널에서 입력한 host, ID, PW는 `.env`에 평문 저장할 수 있습니다.

Proxy 변수명은 `DCINSIDE_PROXY_HOST`, `DCINSIDE_PROXY_ID`, `DCINSIDE_PROXY_PW`여야 합니다.

컨테이너는 `docker-entrypoint.sh`를 통해 `docker run` 환경변수를 내부 `.env` 파일로 생성할 수 있어야 합니다.

### FR-026. Python 라이브러리 API

패키지는 다음을 노출해야 합니다.

- `search_gallery`
- `search_integrated`
- `fetch_post`
- `fetch_comments`
- 설정 객체
- 결과 dataclass

패키지를 import하는 것만으로 스크래핑이 시작되면 안 됩니다.

### FR-027. 워커 컨테이너

1차 구현에는 워커 컨테이너 모드가 포함되어야 합니다.

워커 컨테이너는 향후 마스터 커뮤니티 스크래핑 시스템에 통합될 수 있는 독립 디시인사이드 수집 워커로 실행되어야 합니다.

컨테이너 환경에서는 체크포인트를 PostgreSQL 컨테이너에 저장해야 합니다.

컨테이너 환경에서는 Job JSONL 파일과 다운로드 미디어를 Garage 기반 S3 호환 오브젝트 스토리지에 저장해야 합니다.

컨테이너는 `RESUME`, `JOB_ID`, `DATABASE_URL`, S3 호환 접속 환경변수를 통해 실행 상태와 저장소를 주입받을 수 있어야 합니다.

### FR-028. MCP 도구 인터페이스

1차 구현에는 핵심 스크래퍼 작업을 호출하는 MCP 도구가 포함되어야 합니다.

MCP 도구는 CLI와 워커 컨테이너가 사용하는 것과 동일한 core library 함수를 감싸야 합니다.

### FR-029. 노키워드 기간 및 글번호 범위 수집

스크래퍼는 키워드 없이 특정 갤러리의 작성일 범위와 글번호 범위로 게시글을 수집할 수 있어야 합니다.

노키워드 갤러리 검색 초기 URL은 다음 파라미터를 사용해야 합니다.

- `s_type=search_subject_memo`
- `s_keyword=%20`

노키워드 기간 이동은 브라우저 자동화 없이 `/ajax/search_ajax/search_date/`를 직접 호출해야 합니다.

요청 form data는 다음을 포함해야 합니다.

- `ci_t=<ci_c 쿠키 값>`
- `date=<YYYY-MM-DD>`
- `id=<갤러리 ID>`
- `keyword=`
- `s_type=search_subject_memo`
- `_GALLTYPE_=<갤러리 타입>`

응답이 `{"result":"success","data":"<search_pos>"}`이면 `data`를 `search_pos`로 사용해야 합니다.

`date_to`가 있으면 `date_to`로 작성일 빠른 이동을 수행한 뒤 page와 `search_next`를 따라가야 합니다.

링크 수집은 `date_from <= 작성일 <= date_to`, `min_post_no <= 글번호 <= max_post_no`를 만족하는 게시글만 Queue에 추가해야 합니다.

게시글 작성일이 `date_from`보다 과거이거나 글번호가 `min_post_no`보다 작아지면 수집을 종료해야 합니다.

### FR-030. 실시간 수집 옵션

스크래퍼는 환경변수 기반 실시간 수집을 지원해야 합니다.

실시간 수집 활성화 환경변수:

- `DCINSIDE_REALTIME_ENABLED=true`
- `DCINSIDE_REALTIME_MODE=keyword|all`
- `DCINSIDE_REALTIME_KEYWORD=<검색어>`
- `DCINSIDE_REALTIME_DURATION_SECONDS=<실행 초>`
- `DCINSIDE_REALTIME_END_AT=<UTC ISO-8601 종료 시각>`
- `DCINSIDE_REALTIME_POLL_INTERVAL_SECONDS=<반복 주기 초>`

`keyword` 모드에서는 `DCINSIDE_REALTIME_KEYWORD`가 필수입니다.

`DCINSIDE_REALTIME_DURATION_SECONDS`와 `DCINSIDE_REALTIME_END_AT` 중 정확히 하나만 입력해야 합니다.

두 종료 조건이 모두 있거나 둘 다 없으면 실시간 Job은 validation 오류로 시작 실패해야 합니다.

실시간 키워드 수집은 지정 키워드의 최신 검색 결과를 반복 확인하고 새 게시글만 수집해야 합니다.

실시간 전체 수집은 지정 갤러리의 최신 목록을 반복 확인하고 새 게시글만 수집해야 합니다.

이미 처리한 게시글은 `(gallery_id, post_number)` 기준으로 중복 수집하지 않아야 합니다.

타이머 또는 종료 시각에 도달하면 `status="completed"`로 최종 체크포인트를 저장해야 합니다.

수동 중단, 오류, CAPTCHA 감지 시에는 기존 중단 처리와 동일하게 `status="stopped"`로 최종 체크포인트를 저장해야 합니다.

### FR-031. 심층검색

스크래퍼는 통합 검색의 120페이지 제한을 보완하기 위한 심층검색 모드를 지원해야 합니다.

심층검색은 다음 순서로 수행되어야 합니다.

1. 키워드로 통합 검색을 수행한다.
2. 통합 검색 결과 게시글에서 갤러리 후보 목록을 만든다.
3. 후보 갤러리별로 같은 키워드의 갤러리 내 검색을 수행한다.
4. 조건에 맞는 게시글 링크를 게시글 수집 Queue에 추가한다.

심층검색 Job은 키워드가 필수입니다.

심층검색 Job은 글번호 범위 또는 기간 범위 중 하나 이상을 반드시 입력받아야 합니다.

글번호 범위와 기간 범위가 모두 없으면 Job은 validation 오류로 시작 실패해야 합니다.

통합 검색 기반 갤러리 후보 수집은 최대 120페이지까지만 수행해야 합니다.

갤러리 후보는 `(gallery_type, gallery_id)` 기준으로 중복 제거해야 합니다.

갤러리 후보에는 가능한 경우 `gallery_id`, `gallery_type`, `gallery_name`, `gallery_url`을 포함해야 합니다.

갤러리별 키워드 검색은 기존 갤러리 내 검색 API 규칙을 재사용해야 합니다.

기본 검색 옵션은 `s_type=search_subject_memo`이며, 사용자가 검색 필드를 지정하면 해당 `s_type`을 사용해야 합니다.

최종 게시글 후보는 `(gallery_id, post_number)` 기준으로 중복 제거해야 합니다.

후보 갤러리 중 일부가 실패해도 전체 Job을 즉시 실패시키지 않고 실패 목록에 `(gallery_id, gallery_type, reason)`을 기록해야 합니다.

Job metadata에는 심층검색 모드, 키워드, 범위 조건, 발견한 갤러리 후보 수를 기록해야 합니다.

## 비기능 요구사항

### NFR-001. 유지보수성

핵심 스크래핑 로직은 CLI, 라이브러리 API, 워커 컨테이너, MCP 인터페이스가 공유해야 합니다.

CLI, 컨테이너, MCP 계층은 core library 위의 얇은 adapter여야 합니다.

### NFR-002. 신뢰성

모든 외부 HTTP 및 파일 I/O 작업에는 명시적인 timeout과 오류 처리가 있어야 합니다.

실패한 게시글 fetch는 설정된 횟수까지 재시도해야 합니다.

CAPTCHA/차단 조건은 fail closed 방식으로 중단점 저장 후 중단해야 합니다.

### NFR-003. 성능

시스템은 게시글 fetch를 비동기 멀티 워커로 처리할 수 있어야 합니다. 단, 페이지/링크 탐색은 Job당 순차 처리해야 합니다.

차단 위험을 줄이기 위해 전역 요청 간격 기본값은 1초입니다.

### NFR-004. 보안

Security Baseline을 적용합니다.

적용 요구사항:

- secret, proxy password, cookie, token, raw credential을 로그에 남기지 않음
- `.env`, `user-agents.txt`, `Checkpoint.json`, 출력 파일, 다운로드 미디어, 로컬 인증정보를 `.gitignore`에 포함
- 평문 Proxy credential을 가져오거나 감지하면 터미널에 경고 출력
- CLI, 라이브러리, 워커, MCP 입력값에 명시적 validation 적용
- 의존성은 정확한 버전 또는 lock file로 관리
- 사용하지 않는 의존성은 추가하지 않음
- 안전한 JSON 파싱 및 직렬화만 사용
- 예상치 못한 실패의 사용자 표시 오류 메시지는 내부 정보를 노출하지 않음

문서화된 보안 예외:

- `.env`는 사용자가 직접 편집할 수 있도록 Proxy credential을 평문 저장할 수 있으며, `.gitignore` 보호와 터미널 경고가 필수입니다.

### NFR-005. 회복성

Resiliency Baseline을 적용합니다.

1차 구현은 로컬 실행과 단일 컨테이너 실행을 대상으로 합니다.

RTO/RPO 및 배포 방침:

- DR 전략: 1차 구현에서는 해당 없음
- 지역 구성: 로컬/단일 컨테이너만 지원
- 향후 목표: 멀티 리전 active-passive는 이후 문서화 가능
- rollback 방식: 이전 Git tag 또는 이전 컨테이너 이미지 버전 재배포
- 배포 방식: 직접 배포 또는 컨테이너 재시작
- CI/CD: 기존 CI/CD 파이프라인 사용

상태 및 체크포인트 저장소:

- 로컬 환경: `Checkpoint.json`과 Job JSONL 파일을 실행 파일과 같은 위치에 저장
- 단일 컨테이너 환경: 체크포인트는 PostgreSQL 컨테이너, Job JSONL 파일과 다운로드 미디어는 Garage 기반 S3 호환 오브젝트 스토리지에 저장
- 향후 통합 플랫폼/클라우드 환경: 체크포인트는 RDS, Job JSONL 파일과 미디어는 S3 호환 저장소로 확장
- SeaweedFS는 대량 미디어/소파일 저장, FUSE, Iceberg 요구가 생길 때 대체 저장소로 검토

향후 SQS 기반 통합 플랫폼에서는 작업 lease 설정, 주기적 lease 갱신, lease 만료 시 `reason="lease_expired"` 중단 처리를 지원할 수 있어야 합니다.

향후 SQS 기반 처리 흐름은 다음 순서를 따라야 합니다.

1. Queue에서 작업 획득
2. 작업 lease 설정
3. 게시글 요청 및 파싱
4. 게시글 결과를 멱등하게 저장
5. 게시글 처리 완료 기록
6. 다음 작업으로 진행
7. 주기적으로 lease 갱신
- 변경 관리: 기존 조직 변경 관리 프로세스 사용
- 장애 대응: 기존 조직 incident response 프로세스 사용

### NFR-006. 테스트

테스트에는 다음이 포함되어야 합니다.

- fixture 기반 파서 테스트
- Hypothesis 기반 property-based test
- 선택적 DCinside live smoke test

Live smoke test는 선택적이어야 하며 일반 unit test 실행에 필수여서는 안 됩니다.

### NFR-007. Property-Based Testing

Property-Based Testing을 적용합니다.

Python 로직에는 Hypothesis를 사용해야 합니다.

PBT는 최소한 다음을 포함해야 합니다.

- URL/query 파싱 및 포맷팅 round trip
- 갤러리/검색 결과 파서 invariant
- 게시글 결과 JSON 직렬화 round trip
- `(펌)` 제목 정규화 idempotence
- `(gallery_id, post_no)` 기준 중복 제거
- 중단점 직렬화 round trip
- 상태 스키마 `status`/`reason` enum validation

### NFR-008. 관측성

스크래퍼는 structured logging을 사용해야 합니다.

로그에는 다음이 포함되어야 합니다.

- timestamp
- log level
- job ID
- stage 또는 worker name
- message

로그에는 다음이 포함되면 안 됩니다.

- Proxy password
- raw cookie
- secret token
- 전체 credential file

## 데이터 요구사항

### DR-001. 게시글 JSON 형태

JSONL의 각 줄은 수집된 게시글 하나를 나타내야 합니다.

필수 top-level 필드:

- `scrap_timestamp`
- `gallery_id`
- `post_number`
- `is_repost`
- `repost`
- `title`
- `author`
- `nickname_type`
- `date`
- `views`
- `recommendations`
- `content`
- `images`
- `comments`

### DR-002. `(펌)` JSON 형태

일반 게시글:

- `is_repost`는 `false`
- `repost`는 `null`

`(펌)` 게시글:

- `is_repost`는 `true`
- `repost`는 원 게시글 메타데이터를 포함

필수 `repost` 필드:

- `gallery_id`
- `gallery_name`
- `post_number`
- `author`
- `nickname_type`
- `views`
- `recommendations.upvotes`

원 게시글 댓글 수는 `repost` 아래에 저장하지 않습니다.

## 범위 제외

- CAPTCHA 우회
- 로그인 필요 페이지 스크래핑
- 성인 인증 페이지 스크래핑
- 삭제글 복구
- 1차 구현에서 MongoDB 구현
- 1차 구현에서 GUI/Web UI
- 1차 구현에서 전체 멀티 리전 배포
- Playwright 의존 스크래퍼 런타임

## 추적성

| 요구사항 영역 | 출처 |
|---|---|
| 실행 방식 | Q1, Q2, Q17, Q18 |
| 수집 진입점 | Q3 |
| 비동기 HTTP 런타임 | Q4 |
| 게시글 본문 및 이미지 | Q5, Q9 |
| 댓글 및 덧글 | Q6 |
| 디시콘 처리 | Q7, clarification Q1 |
| JSONL 출력 | Q8 |
| 중단점 및 CAPTCHA 처리 | Q10, Q11 |
| 요청 지연 | Q12 |
| User-Agent 및 Proxy | Q13, Q14, clarification Q3-Q4 |
| 중복 제거 및 종료 조건 | Q15, Q16 |
| 테스트 및 PBT | Q19, Q23, clarification Q5 |
| 공개 콘텐츠만 수집 | Q20 |
| 보안 및 회복성 | Q21, Q22, clarification Q6-Q12 |
| `(펌)` 지원 | 업데이트된 `docs\Function_Specification.md` |
| 작업 상태 및 체크포인트 개정 | 사용자 임시 메모 요약 반영, 원문 편입 안 함 |
| 노키워드/실시간 수집 옵션 | 업데이트된 `docs\Function_Specification.md` 및 agent-browser 분석 결과 |
| 심층검색 | 업데이트된 `docs\Function_Specification.md` |

## 준수 요약

### Security Baseline

- **상태**: 요구사항 단계 기준 준수
- **메모**: 입력 검증, 민감정보 로그 제한, 의존성 pinning, `.gitignore` 보호, 평문 `.env` Proxy 예외를 요구사항에 포함했습니다.

### Resiliency Baseline

- **상태**: 요구사항 단계 기준 준수
- **메모**: 사용자가 선택한 RTO/RPO, 지역 구성, rollback 방식, 배포 방식, CI/CD, 변경 관리, 장애 대응, 로컬/컨테이너/향후 클라우드 체크포인트 및 JSONL 저장소 결정을 문서화했습니다.

### Property-Based Testing

- **상태**: 요구사항 단계 기준 준수
- **메모**: Hypothesis를 선택했고, 파서, 직렬화, 중단점, 중복 제거, `(펌)` 제목 정규화 로직의 PBT 대상 속성을 식별했습니다.
