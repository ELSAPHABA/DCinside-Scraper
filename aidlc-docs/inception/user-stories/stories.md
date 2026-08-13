# 유저 스토리

## 작성 기준

- 구성 방식: 사용자 여정 기반
- 세분화 수준: 에픽 아래 중간 크기 스토리
- 범위: 1차 구현 중심, 향후 확장은 마지막 섹션에만 기록
- 인수조건 형식: 기본 체크리스트, 위험한 워크플로는 Given/When/Then 추가
- 테스트 반영: fixture 테스트, Hypothesis 기반 PBT, 선택적 live smoke test 검증 메모 포함

## 공통 원칙

- 모든 스토리는 공개 콘텐츠 수집만 다룹니다.
- CAPTCHA 우회, 로그인 필요 페이지, 성인 인증 페이지, 삭제글 복구는 제외합니다.
- 런타임 스크래핑은 `httpx`, `asyncio`, BeautifulSoup, 표준 `json` 기반입니다.
- Playwright는 조사 도구로만 사용할 수 있으며, 스크래퍼 런타임 의존성으로 포함하지 않습니다.
- CLI, 라이브러리, 워커 컨테이너, MCP는 같은 core library 함수를 공유합니다.

## 에픽 1. 작업 설정과 실행 준비

### US-001. CLI에서 수집 Job을 생성한다

**페르소나**: P-001 터미널 수집 사용자

**User Story**: 터미널 수집 사용자로서, 게시글 URL 직접 입력, 갤러리 내 검색, 통합 검색, 심층검색, 노키워드 범위 수집, 실시간 수집 중 하나를 선택해 Job을 만들고 싶다. 그래서 같은 도구로 여러 수집 방식을 실행할 수 있다.

**요구사항 추적**: FR-001, FR-003

**인수조건**

- [ ] CLI는 게시글 URL, 갤러리 내 검색, 통합 검색, 심층검색, 노키워드 범위 수집 진입점을 선택하게 한다.
- [ ] 실시간 키워드/전체 수집은 환경변수로 활성화할 수 있다.
- [ ] CLI는 Job ID와 출력 경로를 생성하거나 사용자가 지정한 값을 검증한다.
- [ ] CLI는 수집 범위, 이미지 처리, 디시콘 처리, 요청 간격, worker 수를 실행 전에 표시한다.
- [ ] import만으로 CLI가 실행되거나 네트워크 요청이 발생하지 않는다.

**검증 메모**

- fixture 없이 CLI argument/config validation 단위 테스트로 검증한다.
- 잘못된 URL, 빈 검색어, 잘못된 worker 수는 validation 오류를 반환해야 한다.

### US-002. User-Agent와 Proxy 설정을 불러온다

**페르소나**: P-001 터미널 수집 사용자, P-003 워커 컨테이너 운영자

**User Story**: 터미널 수집 사용자로서, 실행 파일 옆의 `user-agents.txt`와 `.env`를 자동으로 사용하고 싶다. 그래서 반복 실행 때 같은 네트워크 설정을 다시 입력하지 않아도 된다.

**요구사항 추적**: FR-024, FR-025, NFR-004

**인수조건**

- [ ] `user-agents.txt`가 있으면 한 줄당 User-Agent 하나로 읽고 빈 줄은 무시한다.
- [ ] `user-agents.txt`가 없으면 기본 User-Agent를 사용한다.
- [ ] 기본 User-Agent 교체 주기는 요청 10회마다 1회이며 터미널 옵션으로 변경할 수 있다.
- [ ] 사용자가 Proxy 옵션을 켠 경우 터미널 입력값을 최우선으로 사용하고 `.env`에 저장한다.
- [ ] Proxy 옵션을 켜지 않았고 `.env`가 있으면 `DCINSIDE_PROXY_HOST`, `DCINSIDE_PROXY_ID`, `DCINSIDE_PROXY_PW`를 읽어 proxy 설정에 반영한다.
- [ ] `.env`가 없거나 유효한 Proxy 변수가 없으면 proxy 사용을 비활성화한다.
- [ ] 평문 Proxy credential을 가져오거나 감지하면 터미널에 경고를 출력한다.
- [ ] 로그에는 Proxy password, raw `.env` 또는 credential file 내용이 남지 않는다.

**검증 메모**

- 보안 테스트는 로그 캡처에서 credential 문자열이 없는지 확인한다.
- 파일 파싱 테스트는 빈 줄, 주석, 잘못된 행을 포함한 fixture로 검증한다.

### US-003. 요청 속도와 worker 수를 조절한다

**페르소나**: P-001 터미널 수집 사용자, P-003 워커 컨테이너 운영자

**User Story**: 운영자로서, 요청 간격과 게시글 worker 수를 조절하고 싶다. 그래서 차단 위험과 처리량 사이의 균형을 Job마다 정할 수 있다.

**요구사항 추적**: FR-008, FR-023, NFR-003

**인수조건**

- [ ] 기본 전역 요청 간격은 1초다.
- [ ] 사용자는 CLI 옵션으로 전역 요청 간격을 변경할 수 있다.
- [ ] 요청 지연은 목록, 통합 검색, 게시글 상세, `(펌)` AJAX, 댓글 API, 이미지/디시콘 다운로드에 적용된다.
- [ ] 링크 수집은 Job마다 단일 순차 worker로 동작한다.
- [ ] 게시글 상세 수집은 `asyncio.Queue` 기반 멀티 worker로 동작한다.
- [ ] worker 수는 1 이상의 정수로 validation된다.

**검증 메모**

- 요청 scheduler는 단위 테스트에서 fake clock 또는 작은 interval로 검증한다.
- live smoke test는 기본 테스트에 포함하지 않고 수동/선택 옵션으로 둔다.

## 에픽 2. 검색 및 링크 수집

### US-004. 갤러리 내 검색 결과에서 링크를 수집한다

**페르소나**: P-001 터미널 수집 사용자, P-005 유지보수자

**User Story**: 터미널 수집 사용자로서, 갤러리 내 검색 URL 또는 조건을 입력해 결과 게시글 링크를 모으고 싶다. 그래서 수동으로 검색 페이지를 넘기지 않아도 된다.

**요구사항 추적**: FR-005, FR-007

**인수조건**

- [ ] 일반 갤러리는 `/board/lists/`, 마이너 갤러리는 `/mgallery/board/lists/`를 사용한다.
- [ ] `id`, `s_type`, `s_keyword`, `page`, 선택적 `search_pos`를 보존한다.
- [ ] 최초 요청은 `search_pos`를 생략하거나 빈 값으로 시작한다.
- [ ] 다음/이전 검색은 `a.search_next[href]`, `a.search_prev[href]` href를 그대로 따른다.
- [ ] 최신 글번호에서 `search_pos`를 직접 계산하지 않는다.
- [ ] `.gall_listwrap.list tbody tr.ub-content.us-post`만 게시글 후보로 파싱한다.
- [ ] `.gall_num`이 `-`인 공지/광고성 행은 제외한다.
- [ ] 목록의 `(펌)` 여부는 `.gall_tit > b.font_blue009` 텍스트로만 판정한다.

**검증 메모**

- 갤러리 검색 fixture로 행 파싱, 공지 제외, `(펌)` 판정을 테스트한다.
- PBT는 query 파라미터 보존과 URL round trip을 검증한다.
- 예시 URL live smoke test는 선택 실행으로만 둔다.

### US-005. 통합 검색 결과에서 링크를 수집한다

**페르소나**: P-001 터미널 수집 사용자, P-005 유지보수자

**User Story**: 터미널 수집 사용자로서, 통합 검색 키워드로 여러 갤러리의 게시글 후보를 수집하고 싶다. 그래서 갤러리 ID를 미리 몰라도 관련 게시글을 모을 수 있다.

**요구사항 추적**: FR-006, FR-007

**인수조건**

- [ ] 키워드는 UTF-8 percent encoding 후 `%`를 `.`로 치환한 통합 검색 URL을 만들 수 있다.
- [ ] 최신순과 정확도순 URL 형식을 지원한다.
- [ ] `a.page_end[href]` 또는 페이징 링크에서 마지막 페이지 번호를 추출한다.
- [ ] `.integrate_cont.sch_result.result_all ul.sch_result_list > li`에서 결과 항목을 파싱한다.
- [ ] 각 결과에서 상세 URL, 제목, 미리보기, 갤러리명, 갤러리 링크, 날짜를 추출한다.
- [ ] 상세 URL에서 gallery ID, post number, gallery type을 추출한다.

**검증 메모**

- 통합 검색 fixture로 URL/페이지/결과 파싱을 테스트한다.
- PBT는 키워드 encoding과 decoding 가능한 query 구성의 round trip을 검증한다.

### US-006. 수집 범위와 중복 제거를 적용한다

**페르소나**: P-001 터미널 수집 사용자, P-006 데이터 검토자

**User Story**: 데이터 검토자로서, 설정한 글번호나 날짜 범위에 맞는 게시글만 Job 결과에 포함되길 원한다. 그래서 결과 JSONL을 조건별로 신뢰하고 분석할 수 있다.

**요구사항 추적**: FR-007, NFR-007

**인수조건**

- [ ] 링크 수집 worker는 설정된 글번호 범위와 작성일 범위로 링크를 필터링한다.
- [ ] 설정된 종료 조건 중 먼저 도달한 조건에서 링크 탐색을 중단한다.
- [ ] `(gallery_id, post_no)` 기준으로 중복 링크를 제거한다.
- [ ] 통합 검색에서 같은 게시글이 여러 페이지에 나타나도 한 번만 queue에 넣는다.
- [ ] 필터링 및 중복 제거 결과는 structured log에 건수 중심으로 기록한다.

**Given/When/Then**

- Given 같은 `(gallery_id, post_no)`가 여러 검색 결과에서 발견됐을 때
- When 링크 수집 worker가 queue에 게시글을 추가하면
- Then 해당 게시글은 한 번만 enqueue되고 결과 JSONL에도 한 줄만 기록된다.

**검증 메모**

- PBT는 임의의 중복 입력 목록에서 결과 key 집합이 유일한지 검증한다.
- 날짜/글번호 경계값 fixture로 inclusive/exclusive 정책을 고정한다.

### US-006B. 심층검색으로 여러 갤러리의 키워드 게시글을 수집한다

**페르소나**: P-001 터미널 수집 사용자, P-006 데이터 검토자

**User Story**: 데이터 검토자로서, 통합 검색의 120페이지 제한을 넘어 키워드 관련 게시글을 더 넓게 수집하고 싶다. 그래서 통합 검색에서 발견된 갤러리별로 같은 키워드를 다시 검색해 결과 누락을 줄일 수 있다.

**요구사항 추적**: FR-031, FR-005, FR-006, FR-007

**인수조건**

- [ ] 심층검색은 키워드를 필수로 입력받는다.
- [ ] 심층검색은 글번호 범위와 기간 범위가 모두 없으면 validation 오류를 반환한다.
- [ ] 1단계에서는 기존 통합 검색으로 게시글 결과를 수집하고 갤러리 후보 목록을 만든다.
- [ ] 통합 검색 기반 갤러리 후보 수집은 최대 120페이지까지만 수행한다.
- [ ] 갤러리 후보는 `(gallery_type, gallery_id)` 기준으로 중복 제거한다.
- [ ] 후보 갤러리에는 가능한 경우 `gallery_id`, `gallery_type`, `gallery_name`, `gallery_url`을 저장한다.
- [ ] 2단계에서는 후보 갤러리마다 같은 키워드로 갤러리 내 검색을 수행한다.
- [ ] 기본 검색 필드는 `search_subject_memo`이며 사용자가 지정한 검색 필드가 있으면 이를 사용한다.
- [ ] 글번호 범위 또는 기간 범위를 벗어나면 해당 갤러리 검색을 종료한다.
- [ ] 최종 게시글 후보는 `(gallery_id, post_number)` 기준으로 중복 제거한다.
- [ ] 일부 후보 갤러리 검색 실패는 전체 Job 실패가 아니라 실패 목록에 기록한다.
- [ ] Job metadata에는 심층검색 모드, 키워드, 범위 조건, 발견한 갤러리 후보 수를 기록한다.

**Given/When/Then**

- Given 키워드와 기간 범위 또는 글번호 범위가 입력됐을 때
- When 심층검색 Job이 실행되면
- Then 통합 검색에서 갤러리 후보를 만들고 각 후보 갤러리에서 키워드 검색을 수행해 중복 없는 게시글 Queue를 만든다.

**검증 메모**

- 통합 검색 fixture에서 갤러리 후보 dedupe를 검증한다.
- 갤러리별 검색 fixture에서 범위 종료와 게시글 dedupe를 검증한다.
- 범위 조건이 없는 심층검색 입력은 validation 오류를 반환해야 한다.

### US-006A. 노키워드와 실시간 수집 옵션을 실행한다

**페르소나**: P-001 터미널 수집 사용자, P-003 워커 컨테이너 운영자

**User Story**: 터미널 수집 사용자로서, 키워드 없이 기간/글번호 범위로 수집하거나 실시간으로 새 글을 수집하고 싶다. 그래서 검색어가 없는 범위 수집과 장시간 모니터링 수집을 같은 런타임에서 처리할 수 있다.

**요구사항 추적**: FR-029, FR-030, FR-007, FR-020

**인수조건**

- [ ] 노키워드 범위 수집은 `s_type=search_subject_memo&s_keyword=%20` 초기 URL을 사용한다.
- [ ] 노키워드 작성일 이동은 브라우저 클릭 없이 `/ajax/search_ajax/search_date/` POST로 `search_pos`를 얻는다.
- [ ] 노키워드 작성일 이동 요청은 `keyword=` 빈 문자열과 `s_type=search_subject_memo`를 사용한다.
- [ ] 응답의 `data`를 `search_pos`로 사용해 기간 시작 위치를 만든다.
- [ ] 노키워드 범위 수집은 작성일 범위와 글번호 범위를 모두 만족하는 게시글만 Queue에 추가한다.
- [ ] 실시간 수집은 `DCINSIDE_REALTIME_ENABLED=true`일 때만 활성화된다.
- [ ] `DCINSIDE_REALTIME_MODE`는 `keyword` 또는 `all`만 허용한다.
- [ ] `keyword` 모드는 `DCINSIDE_REALTIME_KEYWORD`가 없으면 validation 오류를 반환한다.
- [ ] 실시간 수집은 `DCINSIDE_REALTIME_DURATION_SECONDS` 또는 `DCINSIDE_REALTIME_END_AT` 중 정확히 하나만 입력받는다.
- [ ] 두 종료 조건이 모두 있거나 둘 다 없으면 validation 오류를 반환한다.
- [ ] 실시간 반복은 이미 처리한 `(gallery_id, post_number)`를 다시 Queue에 넣지 않는다.
- [ ] 종료 조건 도달 시 `status="completed"` checkpoint를 저장한다.

**Given/When/Then**

- Given `DCINSIDE_REALTIME_ENABLED=true`이고 종료 조건이 설정됐을 때
- When 실시간 수집이 최신 목록 또는 최신 검색 결과를 반복 확인하면
- Then 새 게시글만 수집하고 종료 조건에 도달하면 completed checkpoint를 저장한다.

**검증 메모**

- 노키워드 `search_date` 응답 fixture로 `search_pos` 생성과 URL 구성 테스트를 추가한다.
- 실시간 옵션 validation은 환경변수 fixture로 검증한다.
- 실시간 dedupe는 같은 게시글이 여러 반복에서 발견되는 fixture로 검증한다.

## 에픽 3. 게시글 상세 수집

### US-007. 게시글 메타데이터와 본문을 수집한다

**페르소나**: P-002 Python 라이브러리 개발자, P-005 유지보수자

**User Story**: 라이브러리 개발자로서, 게시글 URL 하나에서 표준 메타데이터와 본문을 얻고 싶다. 그래서 검색 경로와 무관하게 같은 게시글 JSON을 만들 수 있다.

**요구사항 추적**: FR-008, FR-009, FR-015

**인수조건**

- [ ] 게시글 상세 페이지에서 gallery ID, 글번호, 제목, 작성자, 닉네임 유형, 작성일을 수집한다.
- [ ] 조회수, 추천수, 비추천수, 댓글 수를 수집한다.
- [ ] 일반 게시글 본문은 비본문 요소를 제거한 `.writing_view_box .write_div`에서 추출한다.
- [ ] 본문 링크를 별도 배열로 수집한다.
- [ ] 접근 불가, 삭제, 성인 인증, 로그인 필요 페이지는 실패 사유로 기록하고 스크래핑을 시도하지 않는다.

**검증 메모**

- 실제 HTML fixture로 메타데이터와 본문 추출을 테스트한다.
- 실패 fixture는 사용자에게 내부 정보를 노출하지 않는 오류 메시지를 확인한다.

### US-008. 게시글 이미지 URL과 파일을 처리한다

**페르소나**: P-001 터미널 수집 사용자, P-002 Python 라이브러리 개발자

**User Story**: 터미널 수집 사용자로서, 게시글 이미지 URL만 저장하거나 파일로 내려받고 싶다. 그래서 수집 목적에 맞춰 저장 비용을 조절할 수 있다.

**요구사항 추적**: FR-016, FR-023

**인수조건**

- [ ] Job 실행 전에 이미지 URL만 저장할지, 파일 다운로드까지 수행할지 선택할 수 있다.
- [ ] 일반 게시글 이미지는 `.write_div img[data-fileno]`에서 수집한다.
- [ ] 이미지 URL은 `data-original`, `src`, `onclick`의 `imgPop(...)` 순서로 찾는다.
- [ ] 파일 다운로드 선택 시 `images/<gallery_id>/<post_no>/` 아래에 저장한다.
- [ ] 이미지 다운로드에도 전역 요청 지연과 timeout을 적용한다.
- [ ] 이미지 다운로드 실패는 게시글 전체 실패가 아니라 이미지 실패 항목으로 기록한다.

**검증 메모**

- fixture로 `data-original`, `src`, `imgPop(...)` 우선순위를 테스트한다.
- URL만 저장 모드는 파일 시스템 write 없이 검증한다.

### US-009. `(펌)` 게시글을 일반 게시글과 같은 결과 구조로 수집한다

**페르소나**: P-002 Python 라이브러리 개발자, P-006 데이터 검토자

**User Story**: 데이터 검토자로서, `(펌)` 게시글도 일반 게시글과 같은 top-level 구조로 받고 싶다. 그래서 분석 코드가 게시글 종류마다 크게 갈라지지 않는다.

**요구사항 추적**: FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, DR-002

**인수조건**

- [ ] 목록에서는 `.gall_tit > b.font_blue009` 텍스트 `(펌)`으로 repost 후보를 판정한다.
- [ ] 상세에서는 `h3.title > b.font_blue009` 또는 `.write_div script`의 `/ajax/pum_ajax/get_contents`로 `is_repost=true`를 판정한다.
- [ ] JSON `title`에는 제목 앞의 `(펌)`을 저장하지 않는다.
- [ ] raw HTML에 `#pum_container`가 없으면 script에서 AJAX POST 데이터를 추출한다.
- [ ] `/ajax/pum_ajax/get_contents` 응답 HTML을 BeautifulSoup으로 파싱한다.
- [ ] `repost` 객체에는 원 게시글 gallery ID, gallery name, post number, author, nickname type, views, recommendations.upvotes를 저장한다.
- [ ] 원 게시글 댓글 수는 `repost` 객체에 저장하지 않는다.
- [ ] `(펌)` 본문은 `.cloned_card_body p`를 우선 사용해 갤러리명, 조회수, 추천수가 본문에 섞이지 않게 한다.
- [ ] `(펌)` 이미지는 `.cloned_media img[src]`도 수집한다.

**Given/When/Then**

- Given 제목이 `(펌) 이거 뭐냐?`이고 원 게시글 카드가 AJAX로 로드되는 상세 페이지가 있을 때
- When 스크래퍼가 게시글을 fetch하면
- Then JSON에는 `"is_repost": true`, `"title": "이거 뭐냐?"`, `"repost"` 원 게시글 메타데이터가 포함된다.

**검증 메모**

- `(펌)` 목록 fixture, 상세 raw HTML fixture, AJAX 응답 fixture를 분리해 테스트한다.
- PBT는 `(펌)` 제목 정규화가 idempotent인지 검증한다.
- live smoke test는 예시 게시글이 접근 가능할 때만 선택 실행한다.

## 에픽 4. 댓글, 덧글, 디시콘 수집

### US-010. 댓글과 덧글을 계층 구조로 수집한다

**페르소나**: P-002 Python 라이브러리 개발자, P-006 데이터 검토자

**User Story**: 라이브러리 개발자로서, 게시글의 댓글과 덧글을 안정적인 계층 구조로 받고 싶다. 그래서 분석자가 부모 댓글과 하위 덧글 관계를 유지할 수 있다.

**요구사항 추적**: FR-017, DR-001

**인수조건**

- [ ] 댓글 수집은 기본 활성화된다.
- [ ] 게시글 HTML에서 댓글 API 요청에 필요한 hidden 값을 추출한다.
- [ ] `POST https://gall.dcinside.com/board/comment/`로 댓글 JSON을 요청한다.
- [ ] `depth == 0`은 top-level 댓글로 처리한다.
- [ ] `depth == 1`은 덧글로 처리한다.
- [ ] 덧글의 부모 댓글 번호는 `c_no`를 사용해 연결한다.
- [ ] `memo`는 텍스트와 디시콘/미디어 요소를 분리해 파싱한다.

**검증 메모**

- 댓글 fixture에는 일반 댓글, 덧글, 삭제/빈 memo, 디시콘 memo를 포함한다.
- 계층화 테스트는 부모 없는 덧글을 실패 항목 또는 orphan 항목으로 처리하는 정책을 고정한다.

### US-011. 디시콘 URL과 파일을 처리한다

**페르소나**: P-001 터미널 수집 사용자, P-006 데이터 검토자

**User Story**: 터미널 수집 사용자로서, 디시콘을 메타데이터만 저장하거나 파일로 내려받고 싶다. 그래서 댓글 분석과 원본 보존 목적을 선택할 수 있다.

**요구사항 추적**: FR-018, FR-023

**인수조건**

- [ ] Job 실행 전에 디시콘 metadata-only 또는 file download 모드를 선택할 수 있다. 현재 file download는 후속 확장이다.
- [ ] 가능한 경우 `src`, `alt`, `title`, `conalt`를 저장한다.
- [ ] 디시콘 다운로드에도 전역 요청 지연과 timeout을 적용한다.
- [ ] 디시콘 다운로드 실패는 댓글 전체 실패가 아니라 디시콘 실패 항목으로 기록한다.

현재 구현 delta: 디시콘은 URL/메타데이터 저장까지만 지원한다. file download 모드는 댓글 하위 `DcconItem` 저장 경로와 실패 기록 정책을 확정한 뒤 후속 확장으로 처리한다.

**검증 메모**

- `memo` HTML fixture로 이미지형/영상형 디시콘 파싱을 테스트한다.
- 파일 다운로드 모드는 mock transport로 검증한다.

## 에픽 5. 결과 저장과 데이터 검증

### US-012. Job별 JSONL 결과를 저장한다

**페르소나**: P-006 데이터 검토자, P-002 Python 라이브러리 개발자

**User Story**: 데이터 검토자로서, Job 하나의 결과가 JSONL 파일 하나에 게시글 단위로 append되길 원한다. 그래서 Polars DataFrame으로 수집 결과를 쉽게 검증하고 분석할 수 있다.

**요구사항 추적**: FR-019, DR-001, DR-002, NFR-004, NFR-007

**인수조건**

- [ ] 기본 저장 방식은 Job당 JSONL 파일 하나다.
- [ ] 수집된 게시글 하나는 JSON 객체 한 줄로 append된다.
- [ ] 로컬 환경에서는 Job JSONL 파일을 실행 파일과 같은 위치에 저장한다.
- [ ] 컨테이너 환경에서는 Job JSONL 파일과 다운로드 미디어를 Garage 기반 S3 호환 오브젝트 스토리지에 저장한다.
- [ ] 향후 클라우드 환경에서는 Job JSONL 파일과 미디어 저장소를 S3 호환 저장소로 확장할 수 있다.
- [ ] SeaweedFS는 대량 미디어/소파일 저장, FUSE, Iceberg 요구가 생길 때 대체 저장소로 검토할 수 있다.
- [ ] 체크포인트에서 재개한 Job은 기존 JSONL에 이어 쓰지 않고 새 JSONL 파일을 생성한다.
- [ ] JSON 객체는 `scrap_timestamp`, `gallery_id`, `post_number`, `is_repost`, `repost`, `title`, `author`, `nickname_type`, `date`, `views`, `recommendations`, `content`, `images`, `comments`를 포함한다.
- [ ] 일반 게시글은 `"is_repost": false`, `"repost": null`로 저장한다.
- [ ] `(펌)` 게시글은 `"is_repost": true`와 필수 `repost` 필드를 포함한다.
- [ ] 실패 기록은 별도 실패 파일 또는 Job report에 `(gallery_id, post_number, url, reason)` 형식으로 남긴다.
- [ ] 출력 파일 경로는 `.gitignore` 대상이어야 한다.

**검증 메모**

- JSON serialization round trip PBT를 적용한다.
- JSONL fixture를 Polars DataFrame으로 읽었을 때 필수 컬럼이 유지되는지 확인한다.

### US-013. 수집 결과 품질을 검토한다

**페르소나**: P-006 데이터 검토자

**User Story**: 데이터 검토자로서, 수집 결과의 누락과 중복을 빠르게 확인하고 싶다. 그래서 다음 수집 조건을 조정하거나 파서 회귀를 발견할 수 있다.

**요구사항 추적**: DR-001, DR-002, NFR-008

**인수조건**

- [ ] Job report는 수집 성공 수, 실패 수, 중복 제거 수, 필터 제외 수를 포함한다.
- [ ] 데이터 검토자는 JSONL을 Polars DataFrame으로 불러와 필수 top-level 필드를 확인할 수 있다.
- [ ] `(펌)` 게시글의 `title`에는 `(펌)` 표시가 남지 않는다.
- [ ] 일반 게시글과 `(펌)` 게시글 모두 같은 top-level 컬럼 구조를 가진다.
- [ ] structured log는 timestamp, level, job ID, stage 또는 worker name, message를 포함한다.

**검증 메모**

- 작은 JSONL fixture로 필수 컬럼과 repost/null 구조를 확인한다.

## 에픽 6. 중단, 재개, 실패 처리

### US-014. CAPTCHA 또는 차단 감지 시 중단점을 저장하고 멈춘다

**페르소나**: P-001 터미널 수집 사용자, P-003 워커 컨테이너 운영자

**User Story**: 터미널 수집 사용자로서, CAPTCHA나 차단이 감지되면 자동 우회 대신 현재 상태가 저장되길 원한다. 그래서 수집 상태를 잃지 않고 나중에 재개할 수 있다.

**요구사항 추적**: FR-020, FR-021, FR-022, NFR-002, NFR-005

**인수조건**

- [ ] CAPTCHA 또는 차단 의심 응답이 감지되면 현재 Job을 즉시 중단한다.
- [ ] 정상 수집 중에는 공통 상태 스키마의 `status`를 `running`으로 기록한다.
- [ ] 게시글 10개 처리 완료마다 체크포인트를 저장한다.
- [ ] 중단 시 `status`를 `stopped`로 변경하고 최종 체크포인트를 저장한다.
- [ ] 중단 사유는 `captcha`, `manual_stop`, `error`, `timeout`, `lease_expired` 중 하나로 기록한다.
- [ ] CAPTCHA 감지 시 `retry_after`는 UTC ISO-8601 값 또는 `null`로 기록한다.
- [ ] 체크포인트 저장 후 터미널과 로그에 저장된 `job_id`를 출력한다.
- [ ] 터미널에는 재개 명령 예시를 출력한다.
- [ ] CAPTCHA 자동 우회 또는 자동 풀이를 시도하지 않는다.
- [ ] checkpoint에는 Job 유형, 검색 조건, 수집 옵션, `search_pos`, 현재 페이지, 마지막 처리 글번호, 가능한 queue 상태를 저장한다.
- [ ] checkpoint는 모든 커뮤니티 스크래퍼가 공유할 수 있는 공통 상태 스키마를 따른다.
- [ ] checkpoint 파일은 `.gitignore` 대상이어야 한다.

**Given/When/Then**

- Given 게시글 worker가 CAPTCHA 의심 HTML 또는 차단 응답을 받았을 때
- When scraper runtime이 응답을 분류하면
- Then Job은 fail closed로 멈추고 checkpoint 저장소와 재개 안내를 남긴다.

**검증 메모**

- CAPTCHA fixture와 차단 응답 fixture로 감지 및 중단 동작을 테스트한다.
- checkpoint 직렬화 round trip PBT를 적용한다.

### US-015. 사용자가 중단한 Job을 재개한다

**페르소나**: P-001 터미널 수집 사용자, P-003 워커 컨테이너 운영자

**User Story**: 터미널 수집 사용자로서, 중단한 Job을 로컬 `Checkpoint.json` 또는 컨테이너 checkpoint 저장소에서 재개하고 싶다. 그래서 긴 수집 작업을 처음부터 다시 시작하지 않아도 된다.

**요구사항 추적**: FR-020, FR-021, NFR-002, NFR-005

**인수조건**

- [ ] 사용자가 Job을 중단하면 프로세스 종료 전에 최종 checkpoint를 저장한다.
- [ ] 로컬 재개 명령은 터미널 옵션으로 checkpoint `job_id`를 받을 수 있다.
- [ ] 컨테이너 재개 명령은 `RESUME=true`, `JOB_ID=<checkpoint job_id>` 환경변수를 받을 수 있다.
- [ ] 재개 요청에 `JOB_ID`가 없으면 가장 최근 checkpoint를 자동 선택한다.
- [ ] 재개 명령은 기존 Job 유형, 검색 조건, 수집 옵션을 복원한다.
- [ ] 갤러리 검색 재개는 가능한 경우 현재 `search_pos`와 page를 사용한다.
- [ ] 재개 시 새 JSONL 파일을 만들고 중단점 이후부터 기록한다.
- [ ] 이미 성공 저장된 `(site_id, board_id, post_id)` 또는 커뮤니티별 고유 key는 재처리하지 않는다.
- [ ] checkpoint를 읽을 수 없거나 스키마가 맞지 않으면 명확한 validation 오류를 반환한다.

**검증 메모**

- checkpoint fixture로 저장/불러오기 round trip을 테스트한다.
- PBT는 임의의 queue 상태와 처리 완료 key 집합이 직렬화 후 유지되는지 검증한다.

### US-016. 실패한 게시글 요청을 재시도하고 실패 기록을 남긴다

**페르소나**: P-002 Python 라이브러리 개발자, P-005 유지보수자

**User Story**: 라이브러리 개발자로서, 일시적인 게시글 fetch 실패가 전체 Job을 망치지 않길 원한다. 그래서 수집 가능한 게시글은 계속 저장하고 실패는 나중에 검토할 수 있다.

**요구사항 추적**: FR-008, NFR-002

**인수조건**

- [ ] 게시글 상세 fetch 실패는 설정된 횟수까지 재시도한다.
- [ ] 재시도 한도를 초과하면 `(gallery_id, post_number, url, reason)` 형식으로 실패를 기록한다.
- [ ] 복구 불가능한 오류와 CAPTCHA/차단은 일반 재시도 실패와 구분한다.
- [ ] 사용자 표시 오류 메시지는 내부 credential이나 raw response body를 노출하지 않는다.

**검증 메모**

- mock transport로 timeout, 5xx, 404, 접근 제한 응답을 분리해 테스트한다.

### US-016A. 파싱 실패 게시글만 별도 재처리한다

**페르소나**: P-002 Python 라이브러리 개발자, P-005 유지보수자

**User Story**: 유지보수자로서, parser 수정 이후 전체 수집 Job을 다시 실행하지 않고 파싱 실패한 게시글만 재처리하고 싶다. 그래서 요청 수를 줄이고 이미 성공한 결과를 보존하면서 누락분을 회수할 수 있다.

**요구사항 추적**: FR-008, NFR-002

**인수조건**

- [ ] 하나 이상의 `failures.jsonl`에서 parser-stage 게시글 실패만 선별한다.
- [ ] CAPTCHA, 차단, 네트워크, 저장소, 체크포인트 실패는 이 재처리 유닛의 대상에서 제외한다.
- [ ] 실패 URL은 기존 직접 게시글 수집 경로로 재시도한다.
- [ ] 재처리 결과는 원본 실패 파일을 수정하지 않고 새 `posts.jsonl`, `failures.jsonl`, `report.json`으로 저장한다.
- [ ] 이미 성공 저장된 게시글을 입력받은 경우 중복 재처리를 건너뛸 수 있다.

**검증 메모**

- fixture failure 파일로 parser-stage allowlist, 제외 reason, 중복 제거, 기존 성공 skip, retry report 집계를 테스트한다.

## 에픽 7. 라이브러리, 컨테이너, MCP 통합

### US-017. Python 라이브러리 API를 제공한다

**페르소나**: P-002 Python 라이브러리 개발자, P-005 유지보수자

**User Story**: Python 라이브러리 개발자로서, core API를 import해 검색과 게시글 수집을 호출하고 싶다. 그래서 CLI 밖에서도 같은 스크래핑 기능을 재사용할 수 있다.

**요구사항 추적**: FR-026, NFR-001

**인수조건**

- [ ] 패키지는 `search_gallery`, `search_integrated`, `fetch_post`, `fetch_comments`를 노출한다.
- [ ] 설정 객체와 결과 dataclass를 노출한다.
- [ ] import에는 네트워크 요청, 파일 생성, CLI prompt 부작용이 없다.
- [ ] CLI, 컨테이너, MCP adapter는 같은 core 함수를 호출한다.
- [ ] 라이브러리 입력값은 CLI와 같은 기준으로 validation된다.

**검증 메모**

- import side effect 테스트를 둔다.
- public API smoke test는 mock transport 기반으로 실행한다.

### US-018. 워커 컨테이너 모드를 제공한다

**페르소나**: P-003 워커 컨테이너 운영자

**User Story**: 워커 컨테이너 운영자로서, 디시인사이드 수집 worker를 독립 컨테이너로 실행하고 싶다. 그래서 향후 통합 커뮤니티 스크래핑 시스템에 붙일 수 있다.

**요구사항 추적**: FR-027, NFR-001, NFR-004, NFR-005, NFR-008

**인수조건**

- [ ] 컨테이너 모드는 단일 Job 실행을 지원한다.
- [ ] 컨테이너는 core library를 호출하고 별도 파싱 로직을 가지지 않는다.
- [ ] 컨테이너 checkpoint는 PostgreSQL 컨테이너에 저장한다.
- [ ] 컨테이너 JSONL 결과와 다운로드 미디어는 Garage 기반 S3 호환 오브젝트 스토리지에 저장한다.
- [ ] 결과, 실패 기록, checkpoint, media 경로는 컨테이너 저장소 또는 볼륨으로 분리 가능하다.
- [ ] 컨테이너는 `RESUME`, `JOB_ID`, `DATABASE_URL`, S3 호환 접속 환경변수로 재개와 저장소를 설정할 수 있다.
- [ ] structured logging은 stdout/stderr로 출력된다.
- [ ] rollback은 이전 Git tag 또는 이전 컨테이너 이미지 재배포로 가능해야 한다.
- [ ] secret과 Proxy password는 로그에 남지 않는다.

**검증 메모**

- 컨테이너 smoke test는 mock 입력 또는 작은 fixture Job으로 수행한다.

### US-019. MCP tool 인터페이스를 제공한다

**페르소나**: P-004 MCP 클라이언트 사용자, P-005 유지보수자

**User Story**: MCP 클라이언트 사용자로서, MCP tool 호출로 검색과 게시글 수집을 실행하고 싶다. 그래서 AI agent나 외부 도구가 같은 스크래퍼 기능을 안전하게 사용할 수 있다.

**요구사항 추적**: FR-028, NFR-001, NFR-004

**인수조건**

- [ ] MCP tool은 갤러리 검색, 통합 검색, 게시글 fetch, 댓글 fetch를 호출할 수 있다.
- [ ] MCP tool은 CLI와 같은 core library 함수를 감싼다.
- [ ] MCP 입력 스키마는 URL, gallery ID, post number, 검색어, 수집 옵션을 validation한다.
- [ ] MCP 오류 응답은 내부 stack trace, Proxy password, raw credential을 노출하지 않는다.
- [ ] MCP 반환값은 JSON 직렬화 가능한 구조여야 한다.

**검증 메모**

- MCP adapter 테스트는 core function을 mock해 입력 validation과 오류 masking을 확인한다.

### US-020. AWS CDK로 배포 인프라를 정의한다

**페르소나**: P-003 워커 컨테이너 운영자, P-005 유지보수자

**User Story**: 운영자로서, 스크래퍼 워커와 저장소/체크포인트/로그 인프라를 AWS CDK로 재현 가능하게 정의하고 싶다. 그래서 로컬 smoke 이후 AWS 환경 배포를 코드로 관리할 수 있다.

**요구사항 추적**: NFR-004, NFR-005

**인수조건**

- [ ] AWS CDK app 또는 stack은 UOW-008 컨테이너 실행 계약과 환경변수 계약을 기준으로 인프라를 정의한다.
- [ ] 오브젝트 저장소, 체크포인트 저장소, secret, log, worker 실행 리소스의 AWS 리소스 선택은 UOW-010 설계 단계에서 확정한다.
- [ ] secret 값은 CDK source에 평문으로 저장하지 않는다.
- [ ] dev/staging/prod 같은 환경별 설정 분리 방식을 문서화한다.
- [ ] `cdk synth` 또는 이에 준하는 template 생성 검증이 가능해야 한다.

**검증 메모**

- CDK stack은 snapshot 또는 synth smoke test로 기본 template 생성 여부를 확인한다.

## 향후 확장 범위

- GUI 또는 Web UI는 1차 터미널 UI가 안정화된 뒤 별도 설계한다.
- MongoDB 저장소는 JSONL 스키마가 안정화된 뒤 adapter로 추가한다.
- 멀티 리전 active-passive 운영은 1차 로컬/단일 컨테이너 배포 이후 문서화한다.
- CAPTCHA 자동 우회는 1차 범위에 포함하지 않으며, 현재 요구사항에서는 구현하지 않는다.

## INVEST 확인

| 항목 | 확인 결과 |
|---|---|
| Independent | 각 스토리는 독립적으로 구현/검증 가능한 기능 단위로 분리했다. |
| Negotiable | 인수조건은 결과와 제약을 고정하고 구현 세부는 다음 설계 단계에 남겼다. |
| Valuable | 각 스토리는 최소 하나 이상의 페르소나 목표에 직접 연결된다. |
| Estimable | 요구사항 ID와 selector/API 단서가 있어 구현 규모를 추정할 수 있다. |
| Small | 에픽보다 작고 세부 task보다는 큰 단위로 유지했다. |
| Testable | 모든 스토리에 인수조건과 검증 메모를 포함했다. |

## 요구사항-스토리 추적

| 요구사항 | 주요 스토리 |
|---|---|
| FR-001, FR-003 | US-001 |
| FR-004 | 공통 원칙, US-017 |
| FR-005 | US-004 |
| FR-006 | US-005 |
| FR-007 | US-004, US-005, US-006, US-006A, US-006B |
| FR-029 - FR-030 | US-006A |
| FR-031 | US-006B |
| FR-008 | US-003, US-016 |
| FR-009 | US-007 |
| FR-010 - FR-016 | US-008, US-009 |
| FR-017 | US-010 |
| FR-018 | US-011 |
| FR-019 | US-012 |
| FR-020 - FR-022 | US-014, US-015 |
| FR-023 | US-003, US-008, US-011 |
| FR-024 - FR-025 | US-002 |
| FR-026 | US-017 |
| FR-027 | US-018 |
| FR-028 | US-019 |
| NFR-004 | US-002, US-012, US-014, US-018, US-019 |
| NFR-005 | US-014, US-015, US-018 |
| NFR-006 - NFR-007 | US-004, US-005, US-006, US-009, US-012, US-015 |
| NFR-008 | US-013, US-018 |
