# DCinside-Scraper - 상세 기능 명세서

디시인사이드 갤러리 게시글 및 댓글 스크래퍼 상세 가이드

## 1. 프로젝트 개요
- **목표**: 
  - 디시인사이드 갤러리의 게시글 및 댓글을 스크래핑하여 데이터베이스에 저장
  - 빠르고 다양한 게시글 검색 기능
- **기술 스택**: `beautifulsoup`, `requests`, `user-agents`, `json`
  - **스크래핑**: BeautifulSoup + Requests
  - **데이터 저장**: JSON + 이미지 (기본) MongoDB (확장)

## 2. 주요 기능
### 2.1 스크래핑 
#### 2.1.1. 수집 내용
  - 갤러리
  - 글 번호
  - 제목
  - 글쓴이
    - (반)고정닉 or 유동닉
      - (반)고정닉: 식별코드
      - 유동닉: IP 주소
  - 조회수
  - 추천수 + 비추천수
  - 댓글 수
  - 작성일
  - 내용 (텍스트 및 이미지)
    - 이미지 저장 or URL 수집 (옵션)
  - 댓글 + 덧글 (글쓴이, 작성일, 내용)
    - 댓글 번호
    - 댓글 글쓴이: (반)고정닉 or 유동닉
      - (반)고정닉: 식별코드
      - 유동닉: IP 주소
    - 텍스트 or 디시콘

#### 2.1.2. 수집 방식 (수정 중)
  - 갤러리 ID 수집
  - 글 번호 범위 수집 
  - 작성일 수집 
  - 댓글은 게시글 하위로 수집
  - 글자만 수집 / 이미지 포함 수집 옵션

#### 2.1.2.1. 수집 옵션 (수정 중)
  - 갤러리 글 수집 옵션
    - 전체 갤러리 글 수집
    - 특정 갤러리 글 수집
      - 갤러리 ID 입력
  - 글 수집 옵션
    - 전체 글 수집
    - 특정 글 수집
    - (반)고정닉 or 유동닉 글 수집
      - 전체 수집
      - (반)고정닉만 수집
      - 유동닉만 수집
    - 특정 기간 글 수집
    - 특정 글번호 범위 글 수집
  - 댓글 수집 옵션
    - 전체 댓글 수집
    - 특정 댓글 수집
    - (반)고정닉 or 유동닉 댓글 수집
      - 전체 수집
      - (반)고정닉만 수집
      - 유동닉만 수집
    - 특정 기간 댓글 수집
    - 특정 글번호 범위 댓글 수집
  - 이미지 수집 옵션
    - 이미지 저장
    - 이미지 URL 수집
    - 이미지 저장 및 URL 수집
  - 검색 옵션
    - 전체 검색
    - 특정 검색
    - 특정 기간 검색
    - 특정 글번호 범위 검색

#### 2.1.3. 수집 주기
  - 수집 주기는 사용자가 설정 가능 (예: 수동, 매일, 매주)
  - 새로운 게시글이 있는 경우에만 새로운 글부터 수집하도록 최적화

#### 2.1.4. 이미지 수집
  - 게시글 내 이미지 URL을 추출하여 로컬 또는 클라우드에 저장
  - 이미지 파일명은 게시글 번호와 일치하도록 저장

#### 2.1.5. 데이터 저장
  - 수집된 데이터는 JSON 형식으로 저장
  - 이미지 파일은 별도의 폴더에 저장
  - MongoDB를 활용한 확장 가능 (선택 사항)
  - 파일명: job_YYYYMMDD_HHMMSS.json (예: job_20230101_120000.json)
  - 데이터베이스 구조 예시:
    ```json
    {
      // 검색 필드
      // 검색 옵션 설정 시에만 작성
      "gallery_id": "example", // 통합 검색시 "all"
      "post_no_range": [0, 1000], // 전체 범위 검색시 [None, None]
      "post_date_range": ["YYYY-MM-DD-HH:MM:SS", "YYYY-MM-DD-HH:MM:SS"], // 전체 기간 검색시 [None, None]
      "search_field": "all", // "all" (통합 검색), "tittle+content", "title", "content", "author", "comment"
      "search_keyword": "검색 키워드",
      "scrap_start_timestamp": "YYYY-MM-DD-HH:MM:SS"
    {
      "scrap_timestamp": "YYYY-MM-DD-HH:MM:SS",
      "gallery_id": "example",
      "post_number": 12345,
      "title": "Example Post",
      "author": "BAMF (hz6ipw7c0072454)",
      "nickname_type": "fixed", // "fixed" ((반)고정닉), "floating" (유동닉)
      "date": "2023-01-01-12:00:00",
      "views": 100,
      "recommendations": {
        "upvotes": 10,
        "downvotes": 2
      },
      "content": "This is an example post.",
      "images": ["image1.jpg", "image2.jpg"],
      "comments": [
        {
          "comment_number": 12345,
          "author": "ㅇㅇ (123.232)",
          "nickname_type": "floating", // "fixed" ((반)고정닉), "floating" (유동닉)
          "date": "2023-01-02-12:00:00",
          "content": "This is a comment.",
          "replies": [
            {
              "comment_number": 12352,
              "author": "Replier1",
              "nickname_type": "fixed", // "fixed" ((반)고정닉), "floating" (유동닉)
              "date": "2023-01-03-12:00:00",
              "content": "This is a reply to the comment."
            },
            {
              "comment_number": 12423,
              "author": "ㅇㅇ (323.112)",
              "nickname_type": "floating", // "fixed" ((반)고정닉), "floating" (유동닉)
              "date": "2023-01-04-12:00:00",
              "content": "This is another reply to the comment."
            },
            {
              "comment_number": 12512,
              "author": "Replier3",
              "nickname_type": "fixed", // "fixed" ((반)고정닉), "floating" (유동닉)
              "date": "2023-01-05-12:00:00",
              "content": "emoji-62b5df2be09d3ca567b1c5bc12d46b394aa3b1058c6e4d0ca4164.jpg"
            }
          ]
        },
        {
          "comment_number": 13231,
          "author": "Commenter2",
          "nickname_type": "fixed", // "fixed" ((반)고정닉), "floating" (유동닉)
          "date": "2023-01-03-12:00:00",
          "content": "This is another comment.",
          "replies": []
        }
      ]
    },
    {
      "scrap_timestamp": "YYYY-MM-DD-HH:MM:SS",
      "gallery_id": "example",
      "post_number": 12346,
      "title": "Another Example Post",
      "author": "BadAss (adjust6974)",
      "nickname_type": "floating", // "fixed" ((반)고정닉), "floating" (유동닉)
      "date": "2023-01-02-12:00:00",
      "views": 150,
      "recommendations": {
        "upvotes": 15,
        "downvotes": 1
      },
      "content": "This is another example post.",
      "images": ["image3.jpg"],
      "comments": []
    }
    }
    ```

### 2.2. 검색 옵션
  - 갤러리 ID: "example" 형식 ("all" 입력시 통합검색)
  - 날짜 범위: ["YYYY-MM-DD-HH:MM:SS", "YYYY-MM-DD-HH:MM:SS"] 형식 (옵션)
  - 글 번호 범위: [min_post_no, max_post_no] 형식 (옵션)
  - 갤러리 내 검색:
    - 제목 + 내용: "title+content" 형식
    - 제목: "title" 형식
    - 내용: "content" 형식
    - 글쓴이: "author" 형식
    - 댓글: "comment" 형식
  - 통합검색: "all" 형식

#### 2.2.1 갤러리 내 검색 API
  - 대상: 특정 갤러리 내 검색
  - 기본 링크: `https://gall.dcinside.com/mgallery/board/lists/`
    - 일반 갤러리는 `/board/lists/`, 마이너 갤러리는 `/mgallery/board/lists/`
  - 요청 파라미터
    - 갤러리 ID: `id=<갤러리_ID>`
    - 검색옵션: `s_type=<검색옵션>`
      - 제목 + 내용: `search_subject_memo`
      - 제목: `search_subject`
      - 내용: `search_memo`
      - 글쓴이: `search_name`
      - 댓글: `search_comment`
    - 키워드: `s_keyword=<키워드>`
      - `requests`의 `params`로 전달하거나, 직접 URL 생성 시 UTF-8 URL 인코딩
    - 페이지 번호: `page=<페이지_번호>`
    - 검색 기준점: `search_pos=<검색_기준점>`
      - 최초 검색은 `search_pos`를 생략하거나 빈 값으로 요청
      - 다음 검색 구간은 응답 HTML의 `a.search_next[href]` 값을 그대로 사용
      - 이전 검색 구간은 응답 HTML의 `a.search_prev[href]` 값을 그대로 사용
      - `search_pos` 시작값을 최신 글번호에서 직접 계산하지 않는다.
  - 수집 순서
    - 최초 URL에서 `page=1`부터 현재 `search_pos` 구간의 마지막 페이지까지 수집
    - 마지막 페이지는 `a.page_end[href]`의 `page` 값 또는 페이징 링크 중 가장 큰 `page` 값으로 판단
    - 현재 구간 수집 후 `a.search_next[href]`가 있으면 해당 URL로 이동해 다시 `page=1`부터 반복
    - `a.search_next[href]`가 없거나 게시글 행이 없으면 종료
  - 게시글 행 파싱
    - 목록 행: `.gall_listwrap.list tbody tr.ub-content.us-post`
    - 광고/공지 행은 `.gall_num` 값이 `-` 이거나 `us-post` 클래스가 없으므로 제외
    - 글 번호: `.gall_num`
    - 말머리: `.gall_subject`
    - 제목/상세 링크: `.gall_tit a`
    - 글쓴이: `.gall_writer`
    - 작성일: `.gall_date`의 `title` 값 우선, 없으면 텍스트 값
    - 조회수: `.gall_count`
    - 추천수: `.gall_recommend`

##### 2.2.1.1. 게시글 작성일 이동
  - 빠른 이동 UI는 내부적으로 `/ajax/search_ajax/search_date/` 를 호출해 해당 날짜의 `search_pos`를 받은 뒤 목록 URL로 이동한다.
  - 요청: `POST https://gall.dcinside.com/ajax/search_ajax/search_date/`
    - form data: `ci_t=<ci_c 쿠키 값>`, `date=YYYY-MM-DD`, `id=<갤러리 ID>`, `keyword=<검색어>`, `s_type=<검색옵션>`, `_GALLTYPE_=<갤러리 타입>`
  - 응답: `{"result":"success","data":"<search_pos>"}` 형식이면 `search_pos=<data>` 로 갤러리 검색 목록을 요청
  - 실패하거나 `data`가 없으면 해당 날짜 이동 결과 없음으로 처리
    

#### 2.2.2. 통합 검색 API
  - 대상: 전체 갤러리 검색
  - 기본 링크: `https://search.dcinside.com/post/`
  - URL 형식
    - 최신순 1페이지: `/post/q/<인코딩된_키워드>`
    - 최신순 2페이지 이후: `/post/p/<페이지>/q/<인코딩된_키워드>`
    - 정확도순 1페이지: `/post/sort/accuracy/q/<인코딩된_키워드>`
    - 정확도순 2페이지 이후: `/post/p/<페이지>/sort/accuracy/q/<인코딩된_키워드>`
  - 키워드 인코딩
    - UTF-8 URL 인코딩의 `%`를 `.`로 치환
    - 예: `싱글벙글` -> `.EC.8B.B1.EA.B8.80.EB.B2.99.EA.B8.80`
    - 스페이스는 `.20`
  - 페이지 번호
    - 시작값: 1
    - 최대값: 120
    - 마지막 페이지는 `a.page_end[href]`의 `p/<페이지>` 값으로 판단
    - `a.page_end`가 없으면 페이징 링크 중 가장 큰 페이지까지 수집
  - 게시글 링크 파싱
    - 결과 목록: `.integrate_cont.sch_result.result_all ul.sch_result_list > li`
    - 제목/상세 링크: `a.tit_txt`
    - 내용 미리보기: `p.link_dsc_txt` 중 `.dsc_sub`가 아닌 요소
    - 갤러리명/갤러리 링크: `p.dsc_sub > a.sub_txt`
    - 작성일: `p.dsc_sub > span.date_time`
    - 갤러리 ID와 글 번호는 상세 링크의 `id`, `no` 쿼리 값에서 추출
    - 상세 링크가 `/board/view/`이면 일반 갤러리, `/mgallery/board/view/`이면 마이너 갤러리

  #### 2.2.3. 게시글 상세 페이지 수집
  - 갤러리: 게시글 URL의 `id` 값
  - 글 번호: 게시글 URL의 `no` 값
  - 제목: `.title_subject`
  - 글쓴이: `.gall_writer.ub-writer`
    - 닉네임: `data-nick`
    - 식별코드: `data-uid`
    - IP: `data-ip`
    - (반)고정닉 or 유동닉: `data-uid` 값이 있으면 (반)고정닉, `data-uid` 값이 없고 `data-ip` 값이 있으면 유동닉
  - 조회수: `.gall_count` 의 `"조회 NNN"` 값
  - 추천수 + 비추천수
    - 추천수: `.gall_reply_num` 의 `"추천 NNN"` 값, 없으면 `.up_num` 값
    - 비추천수: `#recommend_view_down_<글 번호>` 또는 `.down_num` 값
  - 댓글 수: `.gall_comment` 의 `"댓글 NNN"` 값
  - 작성일: `.gall_date` 의 `title="YYYY-MM-DD HH:MM:SS"` 값
  - 본문
    - 기준 컨테이너: `.writing_view_box .write_div`
    - 텍스트 추출 전 제거: `.img_comment`, `.image_comment`, `.tip_box2`, `.num.img`, `button`, `script`
    - 텍스트: 제거 후 `.write_div`의 텍스트 값
    - 본문 링크: `.write_div a[href]`
  - 이미지 저장 or URL 수집 (옵션)
    - 이미지 목록: `.write_div img[data-fileno]`
    - 이미지 파일 번호: `data-fileno`
    - 이미지 URL 우선순위: `data-original` -> `src` -> `onclick`의 `imgPop(...)` URL
    - `src`가 `gallview_loading_ori.gif` 이면 실제 이미지가 아니므로 `data-original` 값을 사용
  - 첨부 파일 저장 or URL 수집 (옵션)
    - 첨부 파일 목록: `.appending_file a[href]`
    - 파일명: 링크 텍스트 또는 `href`의 `f_no` 값
    - 다운로드 URL: `href`
  - 댓글 + 덧글 (글쓴이, 작성일, 내용)
    - 댓글은 게시글 HTML에 고정으로 포함되지 않고, `/board/comment/` AJAX 응답으로 로드된다.
    - 댓글 요청: `POST https://gall.dcinside.com/board/comment/`
      - 게시글 HTML에서 `#e_s_n_o`, `#board_type`, `#_GALLTYPE_`, `#secret_article_key` 값을 먼저 수집
      - 주요 form data: `id=<갤러리 ID>`, `no=<글 번호>`, `cmt_id=<갤러리 ID>`, `cmt_no=<글 번호>`, `e_s_n_o=<e_s_n_o>`, `comment_page=<페이지 번호>`, `sort=D`, `prevCnt=`, `board_type=<board_type>`, `_GALLTYPE_=<_GALLTYPE_>`, `secret_article_key=<secret_article_key>`, `clean=`, `nptest=`
      - 요청 헤더: `X-Requested-With: XMLHttpRequest`, `Content-Type: application/x-www-form-urlencoded; charset=UTF-8`
    - 댓글 페이지: 응답 JSON의 `pagination` 또는 현재 페이지 댓글 수를 기준으로 `comment_page=1,2,3...` 순서대로 요청
    - 댓글 응답: JSON의 `comments` 배열 사용
      - 일반 댓글: `depth == 0`
      - 덧글: `depth == 1`, 부모 댓글 번호는 `c_no`
      - 댓글/덧글 번호: `no`
      - 글쓴이: `name`
      - (반)고정닉 or 유동닉: `user_id` 값이 있으면 (반)고정닉, `user_id` 값이 없고 `ip` 값이 있으면 유동닉
      - IP: `ip`
      - 작성일: `reg_date` 값. 올해일 경우 `MM.DD HH:MM:SS` (저장은 `YYYY.MM.DD HH:MM:SS`), 작년 또는 그 이전일 경우 `YYYY.MM.DD HH:MM:SS`
      - 덧글 수: 일반 댓글의 `rcnt`
      - 삭제 여부: `del_yn`, `is_delete`
      - 내용: `memo`
        - 일반 텍스트는 `memo`를 텍스트로 저장
        - 디시콘/HTML이 포함된 경우 `memo`를 BeautifulSoup으로 한 번 더 파싱
        - 디시콘 이미지: `img.written_dccon[src]` 의 `src`, `alt`, `title`, `conalt` 값
        - 디시콘 영상: `video.written_dccon[data-src]` 또는 `video.written_dccon > source[src]` 값
    - 렌더링된 HTML을 보조로 파싱할 경우
      - 댓글 목록: `li[id^="comment_li_"]`
      - 댓글 글쓴이: `#comment_li_<댓글 번호> > div > div.addbox > div.cmt_nickbox > span.gall_writer`
      - 댓글 내용: `#comment_li_<댓글 번호> > div > div.addbox > div.clear.cmt_txtbox.btn_reply_write_all`
      - 덧글은 `#comment_li_<댓글 번호>` 내부가 아니라, 같은 `ul.cmt_list` 안에서 댓글 바로 다음 형제 `<li>` 하위의 `<ul class="reply_list" id="reply_list_<댓글 번호>" p-no="<댓글 번호>">` 에 들어간다.
      - BeautifulSoup 기준: `comment_li.find_next_sibling("li")` 에서 `ul.reply_list[p-no="<댓글 번호>"]` 를 찾고, 없으면 덧글 없음으로 처리
      - `li#comment_li_0`, `.dory`, `.cmt_pw_ad` 는 광고/댓글돌이 항목이므로 댓글/덧글 수집 대상에서 제외

  #### 2.2.4. 검색 기반 멀티 워커 수집 흐름
  - 대상: 갤러리 내 검색 API와 통합 검색 API에서 얻은 게시글 링크
  - 1단계: 링크 수집 워커
    - 단일 워커가 검색 결과 페이지를 순차 탐색
    - 갤러리 내 검색은 `page`와 `search_pos` 순서대로 탐색
    - 통합 검색은 최신순 `/post/p/<페이지>/q/<키워드>`, 정확도순 `/post/p/<페이지>/sort/accuracy/q/<키워드>` 순서대로 탐색
    - 설정 범위(글 번호, 작성일, 최대 페이지 등)에 맞는 게시글 링크만 Queue에 추가
    - 중복 게시글은 `(gallery_id, post_number)` 기준으로 제거
  - 2단계: 게시글 수집 워커
    - 여러 워커가 Queue에서 게시글 링크를 가져와 병렬 비동기 수집
    - 게시글 본문, 이미지, 댓글, 덧글을 수집
    - 수집 결과는 게시글 단위로 JSON 저장소에 기록
  - 3단계: 종료 조건
    - 링크 수집 워커가 설정 범위를 벗어나면 Queue 추가 중단
    - Queue가 비고 모든 게시글 수집 워커가 종료되면 job 완료
  - 실패 처리
    - 게시글 요청 실패 시 같은 링크를 제한 횟수만 재시도
    - 제한 횟수 초과 시 실패 목록에 `(gallery_id, post_number, url, reason)` 저장

## 3. 기술 스택 (수정 중)
  - requests 라이브러리를 활용한 Proxy 요청
  - 요청별 세션 분리 (쿠키 reset)
  - BeautifulSoup 라이브러리를 활용한 HTML 파싱
  - json 라이브러리를 활용한 JSON 처리
  - user-agents 라이브러리를 활용한 User-Agent 랜덤 생성
  - 비동기 처리를 위한 asyncio 라이브러리 활용
  - httpx 라이브러리를 활용한 비동기 HTTP 요청
  - asyncio.Queue를 활용한 링크 수집 워커 + 게시글 수집 워커 분리

## 4. 디렉토리 구조
```
DCinside-Scraper/
├── main.py
├── scraper/
│   ├── __init__.py
│   ├── gallery_scraper.py
│   ├── post_scraper.py
│   └── comment_scraper.py
├── database/
│   ├── __init__.py
│   ├── json_handler.py
│   └── mongodb_handler.py
├── utils/
│   ├── __init__.py
│   ├── user_agent.py
│   └── logger.py
├── config/
│   └── settings.py
├── pyproject.toml
└── README.md
```

## ?. 향후 확장 계획
### ?.1. 데이터베이스 확장
- MongoDB를 활용한 데이터베이스 확장
- 임베딩 처리 및 벡터 유사도 검색 (Vector Search)
- 데이터베이스 구조 설계 및 최적화
- Pandas를 활용한 데이터 분석 및 시각화 기능 추가

### ?.2. 검색 기능 확장
- 검색 옵션 추가 (예: 특정 키워드 포함/제외, 정규식 검색)
- 검색 결과 필터링 및 정렬 기능 강화 

### ?.3. 통합 작업 관리 시스템
- 마스터 컨테이너 - 워커 컨테이너 구조 기반의 통합 작업 관리 시스템 구축
- 작업 컨테이너 스케줄링 및 모니터링 기능
- 작업 상태 시각화 및 알림 기능
- 작업 실패 시 재시도 및 오류 로그 관리

### ?.4. 커뮤니티 통합 스크래퍼
- 통합 스크래핑 시스템의 디시인사이드용 워커 컨테이너로 스케줄링 및 스케일링

## ?. 미들웨어 활용 계획
MCP, 라이브러리, KubeRay, 커뮤니티 통합 스크래퍼
