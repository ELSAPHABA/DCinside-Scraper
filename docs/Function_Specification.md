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
    - 제목 + 내용: "tittle+content" 형식
    - 제목: "title" 형식
    - 내용: "content" 형식
    - 글쓴이: "author" 형식
    - 댓글: "comment" 형식
  - 통합검색: "all" 형식

#### 2.2.1 갤러리 내 검색 API
  - 대상: 특정 갤러리 내 검색
  - 기본 링크: https://gall.dcinside.com/mgallery/board/lists?
  - 갤러리 ID: `&id=<갤러리_ID>`
  - 검색옵션: `&s_type=search_<검색옵션>`
    - 제목 + 내용: "subject_memo"
    - 제목: "subject"
    - 내용: "memo"
    - 글쓴이: "name"
    - 댓글: "comment"
  - 키워드: `&s_keyword=<키워드>`
    - 스페이스는 `%20`로 인코딩
  - 페이지 번호: `&page=<페이지_번호>`
    - 요청 페이지 번호와 응답 페이지 번호가 다르면 마지막 페이지로 판단
  - 검색 기준점: `&search_pos=<검색_기준점>`
    - 방법 1: 최신 글번호 스크랩
      - 셀렉터: `'.gall_listwrap.list table tbody`의 `tr.us-post` && `{data-type = ("icon_pic" | "icon_txt" | "icon_movie" | "icon_recomimg" | "icon_recomtxt" | "icon_recomovie")}`의 텍스트 값
      - 글 번호 전부 수집 수 가장 높은 수가 최신 글번호
    - 시작값: 최신 글번호 - 10000
    - 감소값: -10000
    - 방법 2: `next_link = soup.select_one("a.search_next")` 후, `next_link`의 `search_pos` 값 - 10000
  - 순서: 검색 기준점 이동 -> 페이지 번호 이동 -> 검색 기준점 이동 -> 반복

##### 2.2.1.1. 게시글 작성일 이동
  - 셀렉터: `#calendarInput`의 `value=`에 `YYYY-MM-DD` 형식으로 입력 후 `#container > section.left_content.result > article:nth-child(3) > div.bottom_paging_wrap.re > div.pop_wrap.type3.fast_move_lyr > div > div.inner.fast > div.moveset > button` 클릭
    

#### 2.2.2. 통합 검색 API
  - 대상: 전체 갤러리 검색
  - 기본 링크: https://search.dcinside.com/post/
  - 순서: /p/<페이지>/sort/<latest or accuracy>/q/<키워드>
  - p: 페이지 번호
    - 시작값: 1
    - 최대값: 120
    - `#dgn_btn_paging` 의 마지막 `<a>` 태그의 텍스트 값이 변하지 않으면 마지막 페이지로 판단
  - sort: 정렬
    - latest: 최신순
    - accuracy: 정확도순
  - q: 키워드
    - 키워드는 UTF-8 16진수로 변환
      - 디시: `.EB.94.94.EC.8B.9C`
      - 갤러리: `.EA.B0.A4.EB.9F.AC.EB.A6.AC`
    - 스페이스는 `.20`로 치환

  #### 2.2.3. 검색 결과 게시글 수집
  - 갤러리: 링크의 `id` 값
  - 글 번호: 링크의 `no` 값
  - 제목: `#container > section > article:nth-child(3) > div.view_content_wrap > header > div > h3 > span.title_subject`
  - 글쓴이: `#container > section > article:nth-child(3) > div.view_content_wrap > header > div > div > div.fl > span > span.nickname.in`의 `title` 값
    - (반)고정닉 or 유동닉: `#container > section > article:nth-child(3) > div.view_content_wrap > header > div > div` 에서 `data-uid="..." data-ip data-loc="view"` 이면 (반)고정닉, `data-uid data-ip="..." data-loc="view"` 이면 유동닉
  - 조회수: `#container > section > article:nth-child(3) > div.view_content_wrap > header > div > div > div.fr > span.gall_count` 의 `"조회 NNN"` 값
  - 추천수 + 비추천수
    - 추천수: `#container > section > article:nth-child(3) > div.view_content_wrap > header > div > div > div.fr > span.gall_reply_num` 의 `"추천 NNN"` 값
    - 비추천수: `#container > section > article:nth-child(3) > div.view_content_wrap > header > div > div > div.fr > span.gall_reply_num` 의 `"비추천 NNN"` 값
  - 댓글 수: `#container > section > article:nth-child(3) > div.view_content_wrap > header > div > div > div.fr > span.gall_comment > a` 의 `"댓글 NNN"` 값
  - 작성일: `#container > section > article:nth-child(3) > div.view_content_wrap > header > div > div > div.fl > span > span.gall_date` 의 `title="YYYY-MM-DD HH:MM:SS"` 값
  - 내용 (텍스트 및 이미지)
    - 텍스트: 
    - 이미지 저장 or URL 수집 (옵션)
      - 이미지: `#container > section > article:nth-child(3) > div.view_content_wrap > div > div.inner.clear > div.writing_view_box > div.write_div` 하위 `<div class="img_area noN" id="img_focus_NNNNNNN">` 의 `onclick="javascript:imgPop('https://image.dcinside.com/viewimagePop.php?no=...', ...);"` 값에서 `https://image.dcinside.com/viewimagePop.php?no=...` 저장
      - 이미지 URL: `#img_focus_NNNNNNN > div > img`의 `onclick="javascript:imgPop('https://image.dcinside.com/viewimagePop.php?no=...', ...);"` 값에서 `https://image.dcinside.com/viewimagePop.php?no=...` 부분 추출
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

## 3. 기술 스택 (수정 중)
  - requests 라이브러리를 활용한 Proxy 요청
  - 요청별 세션 분리 (쿠키 reset)
  - BeautifulSoup 라이브러리를 활용한 HTML 파싱
  - json 라이브러리를 활용한 JSON 처리
  - user-agents 라이브러리를 활용한 User-Agent 랜덤 생성
  - 비동기 처리를 위한 asyncio 라이브러리 활용
  - httpx 라이브러리를 활용한 비동기 HTTP 요청
  - Queue를 활용한 멀티 워커 job 처리

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

## ?. 미들웨어 활용
MCP, 라이브러리
