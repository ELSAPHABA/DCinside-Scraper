# DCinside-Scraper - 상세 기능 명세서

디시인사이드 갤러리 게시글 및 댓글 스크래퍼 상세 가이드

## 1. 프로젝트 개요
- **목표**: 
  - 디시인사이드 갤러리의 게시글 및 댓글을 스크래핑하여 데이터베이스에 저장
  - 빠르고 다양한 게시글 검색 기능
- **기술 스택**: `beautifulsoup`, `requests`, `user-agents`, `json`
  - **스크래핑**: BeautifulSoup + Requests
  - **데이터 저장**: JSON + 이미지 (기본) MongoDB (확장)

### 1.1. 사용 형태
- 단독 실행형 스크래퍼
  - CLI 또는 설정 파일 기반으로 디시인사이드 게시글/댓글 수집
  - UI는 우선 터미널 기반으로 구성하고, GUI/Web UI는 향후 개선 사항으로 분리
- Python 라이브러리
  - 다른 Python 코드에서 검색, 게시글 수집, 댓글 수집 함수를 import하여 사용
- 워커 컨테이너
  - 향후 통합 커뮤니티 스크래핑 시스템에서 디시인사이드 전용 수집 워커로 실행
  - 외부 Job Queue로부터 수집 요청을 받아 처리
- MCP 도구
  - 외부 에이전트/자동화 시스템이 디시인사이드 검색, 게시글 수집, 댓글 수집 기능을 호출할 수 있도록 제공

## 2. 주요 기능
### 2.1 스크래핑 
#### 2.1.1. 수집 내용
  - 갤러리
  - 글 번호
  - 말머리
    - 마이너 갤러리 게시글이면 말머리 ID와 이름 수집
    - 메이저 갤러리 또는 말머리가 없는 게시글이면 `null`
  - 펌 여부
    - `(펌)` 게시글이면 원 게시글의 갤러리, 글 번호, 유저명, (반)고정닉 여부, 조회수, 추천수 수집
    - 원 게시글의 댓글 수는 수집하지 않음
  - 제목
  - 글쓴이
    - (반)고정닉 or 유동닉
      - (반)고정닉: 식별코드
      - 유동닉: IP 주소
  - 조회수
  - 추천수 + 비추천수
  - 댓글 수
  - 작성일
  - 본문 콘텐츠
    - `content.text`: 검색/미리보기/Pandas 분석용 순수 텍스트
    - `content.blocks`: 원문 순서를 보존한 텍스트, 이미지, DC 동영상, inline 동영상, YouTube 영상/링크, 일반 링크, 시리즈 블록
    - 이미지/동영상/디시콘 파일 저장 or URL 수집 (옵션)
  - 댓글 + 덧글 (글쓴이, 작성일, 내용)
    - 댓글 번호
    - 댓글 글쓴이: (반)고정닉 or 유동닉
      - (반)고정닉: 식별코드
      - 유동닉: IP 주소
    - 텍스트 or 디시콘

#### 2.1.2. 수집 방식
  - 갤러리 ID 수집
  - 글 번호 범위 수집 
  - 작성일 수집 
  - 댓글은 게시글 하위로 수집
  - 본문 텍스트만 수집 / 본문 콘텐츠 블록 수집 / 미디어 파일 다운로드 옵션

#### 2.1.2.1. 수집 옵션
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
    - 특정 말머리 글 수집
      - 마이너 갤러리에서만 지원
      - 존재하지 않는 말머리 ID를 지정하거나 메이저 갤러리에서 요청하면 실패 처리
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
  - 본문 미디어 수집 옵션
    - 이미지/동영상/디시콘 URL 및 메타데이터만 저장
    - 이미지/동영상/디시콘 파일 저장
    - 이미지/동영상/디시콘 URL 및 파일 모두 저장
    - YouTube 등 외부 임베드 영상은 다운로드하지 않고 URL, provider, video_id, embed_url만 저장
    - 시리즈는 게시글 모음 메타데이터로 저장하고, 연결된 게시글 본문은 별도 수집 Job 대상일 때만 수집
  - 검색 옵션
    - 전체 검색
    - 특정 검색
    - 특정 기간 검색
    - 특정 글번호 범위 검색
  - 요청 옵션
    - User-Agent Mixer
      - 차단 회피를 위해 요청 시 사용할 User-Agent를 주기적으로 교체
      - 터미널에서 파일 탐색기 창을 열어 User-Agent 목록 파일을 불러오기
      - 불러온 목록은 실행 파일과 같은 위치의 `User-Agent.txt`에 저장
      - `User-Agent.txt`는 사용자가 직접 편집할 수 있도록 비인코딩 평문으로 저장
    - Proxy
      - Proxy를 통해 requests 요청 전송
      - host, ID, PW는 터미널에서 입력
      - 입력한 Proxy 설정은 실행 파일과 같은 위치의 `Proxy-Profile.txt`에 저장
      - `Proxy-Profile.txt`는 사용자가 직접 편집할 수 있도록 비인코딩 평문으로 저장
    - 스크래핑 속도 조절
      - 요청 사이의 대기 시간을 사용자가 설정 가능
      - 기본값은 안정성을 우선하여 너무 빠른 연속 요청을 피하도록 설정
      - 갤러리 목록, 통합 검색, 게시글 상세, `(펌)` AJAX, DC 동영상 iframe, 댓글 API, 이미지/동영상/디시콘 다운로드 요청에 동일하게 적용
      - CAPTCHA 또는 차단 의심 응답 발생 시 즉시 작업 중단 후 중단점 저장
    - CAPTCHA 대응
      - CAPTCHA 페이지 또는 비정상 접근 차단 응답 포착 시 현재 작업 중단
      - 중단 시 현재 수집 위치, 검색 조건, 수집 옵션, 마지막 처리 글 번호/페이지를 중단점으로 저장
      - CAPTCHA 자동 우회는 구현하지 않음
    - 중단점 저장 및 불러오기
      - 수집 작업 진행 중 마지막 정상 처리 위치를 주기적으로 저장
      - 사용자가 선택하면 저장된 중단점부터 수집 재개
      - 중단점 파일은 실행 파일과 같은 위치의 `Checkpoint.json`에 저장

#### 2.1.3. 수집 주기
  - 수집 주기는 사용자가 설정 가능 (예: 수동, 매일, 매주)
  - 새로운 게시글이 있는 경우에만 새로운 글부터 수집하도록 최적화

#### 2.1.4. 본문 콘텐츠 및 미디어 수집
  - 기준 컨테이너는 `.writing_view_box .write_div`
  - BeautifulSoup으로 `.write_div`의 하위 노드를 DOM 순서대로 순회하여 `content.blocks` 배열에 저장
  - 빈 `<p>`, `<br>`만 있는 노드는 저장하지 않음
  - 각 블록은 공통으로 `order`, `type` 값을 가진다.
  - `type="text"`
    - 일반 텍스트 문단 또는 텍스트만 있는 `p`, `div`
    - `text`에 정규화된 문자열 저장
  - `type="link"`
    - 일반 링크: `.write_div a[href]`
    - 단, YouTube 블록 또는 시리즈 블록 내부 링크는 별도 `link` 블록으로 중복 저장하지 않음
    - `text`, `url` 저장
  - `type="image"`
    - 이미지 후보: `.write_div img[src]`, `.write_div img[data-fileno]`
    - `(펌)` 게시글 원글 카드 이미지: `#pum_container.cloned_card .cloned_media img[src]` 또는 AJAX 응답 HTML의 `.cloned_media img[src]`
    - URL 우선순위: `data-original` -> `src` -> `onclick`의 `imgPop(...)` URL
    - `src`가 `gallview_loading_ori.gif` 이면 실제 이미지가 아니므로 `data-original` 값을 사용
    - `url`, `original_url`, `file_no`, `temp_no`, `alt`, `download` 저장
  - `type="dc_video"`
    - DC 업로드 동영상 iframe: `iframe[src*="/board/movie/movie_view"]`
    - `movie_no`, `iframe_url` 저장
    - BeautifulSoup/httpx 스크래퍼는 게시글 URL을 `Referer`로 두고 `iframe_url`을 추가 요청하여 `video.dc_mv`, `source[type="video/mp4"]`, `poster`, 다운로드 hidden 값을 파싱
    - 파싱 가능하면 `video_url`, `poster_url`, `download_url` 저장
    - iframe 상세 요청이 실패하면 `iframe_url`, `movie_no`, `resolved=false`를 저장하고 게시글 전체 실패로 처리하지 않음
  - `type="inline_video"`
    - 본문 안의 `video` 또는 `video > source[type="video/mp4"]`
    - `data_src`, `video_url`, `sources`, `download` 저장
  - `type="youtube"`
    - YouTube embed: `embed[src*="youtube.com/embed"]`, `iframe[src*="youtube.com/embed"]`
    - 함께 표시되는 원본 링크: 같은 블록 내부의 `a.lnk[href]`
    - `provider="youtube"`, `video_id`, `embed_url`, `url` 저장
    - 외부 영상 파일 다운로드는 하지 않음
  - `type="series"`
    - 시리즈 블록: `.dc_series`
    - 시리즈 제목과 하위 게시글 링크 목록 저장
    - 각 항목은 `title`, `url`, `gallery_id`, `post_number`를 가능한 범위에서 저장
  - `content.text`는 `content.blocks` 중 텍스트성 블록의 `text`를 합쳐 저장
    - 포함 대상: `text`, `link.text`, `series.title`, `series.items[].title`
    - 제외 대상: 조회수/추천수/갤러리명 같은 카드 메타데이터
  - 기존 `images` top-level 배열을 유지할 경우, 원본 기준 데이터가 아니라 `content.blocks`의 `image` 블록만 뽑은 호환/요약 필드로 취급
  - 미디어 파일명은 기본적으로 `media/<gallery_id>/<post_no>/<order>_<type>.<ext>` 형식으로 저장

#### 2.1.5. 데이터 저장
  - 수집된 게시글 데이터는 Job당 하나의 JSONL 파일로 저장
  - 게시글 하나는 JSON 객체 한 줄로 append
  - Job 실행 조건과 요약 정보는 별도 metadata JSON 파일로 저장 가능
  - 이미지/동영상/디시콘 파일은 별도의 `media/` 폴더에 저장
  - MongoDB를 활용한 확장 가능 (선택 사항)
  - 파일명: `job_YYYYMMDD_HHMMSS.jsonl` (예: `job_20230101_120000.jsonl`)
  - Job 메타데이터 예시:
    ```json
    {
      "job_id": "job_20230101_120000",
      "gallery_id": "example",
      "post_no_range": [0, 1000],
      "post_date_range": ["YYYY-MM-DD-HH:MM:SS", "YYYY-MM-DD-HH:MM:SS"],
      "subject_head_filter": {
        "enabled": true,
        "id": 160,
        "name": "2D✨️"
      },
      "search_field": "all",
      "search_keyword": "검색 키워드",
      "scrap_start_timestamp": "YYYY-MM-DD-HH:MM:SS",
      "output_file": "job_20230101_120000.jsonl"
    }
    ```
  - 게시글 JSONL 한 줄 예시:
    ```json
    {
      "scrap_timestamp": "YYYY-MM-DD-HH:MM:SS",
      "gallery_id": "example",
      "post_number": 12345,
      "subject_head": {
        "id": 160,
        "name": "2D✨️"
      },
      "is_repost": false,
      "repost": null,
      "title": "Example Post",
      "author": "BAMF (hz6ipw7c0072454)",
      "nickname_type": "fixed",
      "date": "2023-01-01-12:00:00",
      "views": 100,
      "recommendations": {
        "upvotes": 10,
        "downvotes": 2
      },
      "content": {
        "text": "This is an example post. image caption series title linked post title",
        "blocks": [
          {
            "order": 0,
            "type": "text",
            "text": "This is an example post."
          },
          {
            "order": 1,
            "type": "image",
            "url": "https://dcimg.example/viewimage.php?...",
            "original_url": "https://image.dcinside.com/viewimagePop.php?...",
            "file_no": "123456",
            "temp_no": null,
            "alt": "image alt",
            "download": {
              "enabled": true,
              "path": "media/example/12345/1_image.jpg",
              "status": "saved"
            }
          },
          {
            "order": 2,
            "type": "dc_video",
            "movie_no": "6898168",
            "iframe_url": "https://gall.dcinside.com/board/movie/movie_view?no=6898168",
            "resolved": true,
            "video_url": "https://dcm6.dcinside.co.kr/viewmovie.php?...&type=mp4",
            "poster_url": "https://dcm6.dcinside.co.kr/viewmovie.php?...&type=jpg",
            "download_url": "https://dcm1.dcinside.co.kr/download.php?...",
            "download": {
              "enabled": false,
              "path": null,
              "status": "skipped"
            }
          },
          {
            "order": 3,
            "type": "youtube",
            "provider": "youtube",
            "video_id": "2-3F7y5AKJw",
            "embed_url": "https://www.youtube.com/embed/2-3F7y5AKJw",
            "url": "https://youtu.be/2-3F7y5AKJw"
          },
          {
            "order": 4,
            "type": "link",
            "text": "external link title",
            "url": "https://example.com/article"
          },
          {
            "order": 5,
            "type": "series",
            "title": "시리즈 제목 1",
            "items": [
              {
                "title": "연결된 게시글 제목",
                "url": "https://gall.dcinside.com/mgallery/board/view/?id=singlebungle1472&no=2518712",
                "gallery_id": "singlebungle1472",
                "post_number": 2518712
              }
            ]
          }
        ]
      },
      "images": [
        {
          "order": 1,
          "url": "https://dcimg.example/viewimage.php?...",
          "path": "media/example/12345/1_image.jpg"
        }
      ],
      "comments": [
        {
          "comment_number": 12345,
          "author": "ㅇㅇ (123.232)",
          "nickname_type": "floating",
          "date": "2023-01-02-12:00:00",
          "content": "This is a comment.",
          "replies": [
            {
              "comment_number": 12352,
              "author": "Replier1 (hfd12pw7c00721231)",
              "nickname_type": "fixed",
              "date": "2023-01-03-12:00:00",
              "content": "This is a reply to the comment."
            },
            {
              "comment_number": 12423,
              "author": "ㅇㅇ (323.112)",
              "nickname_type": "floating",
              "date": "2023-01-04-12:00:00",
              "content": "This is another reply to the comment."
            },
            {
              "comment_number": 12512,
              "author": "Replier3 (hfads21fd31)",
              "nickname_type": "fixed",
              "date": "2023-01-05-12:00:00",
              "content": "emoji-62b5df2be09d3ca567b1c5bc12d46b394aa3b1058c6e4d0ca4164.jpg"
            }
          ]
        },
        {
          "comment_number": 13231,
          "author": "Commenter2 (xyz789)",
          "nickname_type": "fixed",
          "date": "2023-01-03-12:00:00",
          "content": "This is another comment.",
          "replies": []
        }
      ]
    }
    ```
  - `(펌)` 게시글 차이 예시:
    ```json
    {
      "scrap_timestamp": "YYYY-MM-DD-HH:MM:SS",
      "gallery_id": "example",
      "post_number": 12346,
      "subject_head": null,
      "is_repost": true,
      "repost": {
        "gallery_id": "stockus",
        "gallery_name": "미국 주식",
        "post_number": 17025333,
        "author": "ㅇㅇ (116.47)",
        "nickname_type": "floating",
        "views": 58,
        "recommendations": {
          "upvotes": 4
        }
      },
      "title": "이거 뭐냐?",
      "author": "BadAss (adjust6974)",
      "nickname_type": "floating",
      "date": "2023-01-02-12:00:00",
      "views": 150,
      "recommendations": {
        "upvotes": 15,
        "downvotes": 1
      },
      "content": {
        "text": "This is another example post.",
        "blocks": [
          {
            "order": 0,
            "type": "text",
            "text": "This is another example post."
          },
          {
            "order": 1,
            "type": "image",
            "url": "https://dcimg.example/repost_image.jpg",
            "original_url": null,
            "file_no": null,
            "temp_no": null,
            "alt": "",
            "download": {
              "enabled": false,
              "path": null,
              "status": "skipped"
            }
          }
        ]
      },
      "images": [
        {
          "order": 1,
          "url": "https://dcimg.example/repost_image.jpg",
          "path": null
        }
      ],
      "comments": []
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
    - 말머리 필터: `search_head=<말머리_ID>` (마이너 갤러리 전용)
      - 특정 말머리 게시글만 수집할 때 사용
      - `sort_type`은 말머리 ID가 아니라 정렬/목록 상태 값이므로 말머리 필터로 사용하지 않음
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
      - `.gall_subject .subject_inner`가 있으면 전체 말머리 이름으로 우선 사용
      - `.subject_inner`가 없으면 `.gall_subject`의 직접 텍스트 노드를 사용
      - 말머리 ID는 현재 요청 URL 또는 상세 링크의 `search_head` 쿼리 값으로 저장
    - 제목/상세 링크: `.gall_tit a`
    - `(펌)` 여부: `.gall_tit > b.font_blue009` 의 텍스트가 `(펌)`이면 `is_repost=true`
      - `.gall_tit span.mark` 는 검색어 하이라이트이므로 단독으로 `(펌)` 판정에 사용하지 않음
      - `is_repost=true` 인 경우 JSON 저장용 제목에서는 `(펌)` 문자열을 제거
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

##### 2.2.1.2. 마이너 갤러리 말머리 탭
  - 대상: 마이너 갤러리의 말머리 탭 기반 수집
  - 말머리 탭 목록 파싱
    - 목록 페이지의 `a[onclick^="listSearchHead"]`를 파싱
    - `onclick="listSearchHead(<ID>)"`의 숫자를 말머리 ID로 저장
    - 링크 텍스트를 말머리 이름으로 저장
    - `class`에 `on`이 있으면 현재 활성 말머리로 판단
  - 예시
    ```json
    {
      "id": 160,
      "name": "2D✨️"
    }
    ```
  - 말머리 필터 요청
    - 특정 말머리만 수집할 때 목록 URL에 `search_head=<말머리_ID>`를 추가
    - 예: `/mgallery/board/lists/?id=singlebungle1472&search_head=160&page=1`
    - 말머리 필터 적용 시 `page=1`부터 수집 시작
    - 페이지 이동, 게시글 상세 링크, 댓글 링크에 이미 포함된 `search_head` 값은 보존
  - 유효성 검증
    - 마이너 갤러리 여부는 `/mgallery/board/lists/` 경로 또는 페이지의 갤러리 타입 값이 `M`인지로 판단
    - 메이저 갤러리에서 말머리 필터를 요청하면 Job 시작 전 실패 처리
    - 요청한 말머리 ID가 `a[onclick^="listSearchHead"]` 목록에 없으면 Job 시작 전 실패 처리
    - `search_head=<ID>` 요청 후 응답 URL에서 `search_head`가 사라지거나 활성 말머리 탭이 확인되지 않으면 존재하지 않는 말머리로 보고 실패 처리
    - 존재하지 않는 말머리 ID는 갤러리 메인 목록을 반환할 수 있으므로, 단순 HTTP 200 또는 게시글 존재 여부만으로 성공 판단하지 않음
  - 말머리 탭 탐색 fallback
    - 기본 방식은 목록 페이지의 `a[onclick^="listSearchHead"]` 파싱
    - 탭 목록이 DOM에서 확인되지 않을 때만 `search_head=N`을 10씩 증가시키며 fallback 탐색
    - fallback 탐색에서도 활성 탭 또는 `.gall_subject` 값이 요청한 말머리와 일치해야 존재하는 말머리로 인정
  - 저장 구조
    - 게시글 JSON에는 다음 top-level 필드를 저장
      ```json
      {
        "subject_head": {
          "id": 160,
          "name": "2D✨️"
        }
      }
      ```
    - 메이저 갤러리 또는 말머리 없는 게시글은 `"subject_head": null`
    

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
    - `(펌)` 게시글이면 JSON 저장용 제목에서 `(펌)` 문자열을 제거
    - 예: `.title_subject` 값이 `(펌) 이거 뭐냐?` 이면 `"title": "이거 뭐냐?"`
  - 말머리
    - 마이너 갤러리 상세 페이지에서 `h3.title > span.title_headtext` 값을 수집
    - 값의 앞뒤 `[` `]`를 제거해 `subject_head.name`으로 저장
    - URL 또는 hidden 값의 `search_head`가 있으면 `subject_head.id`로 저장
    - 목록 수집 단계에서 이미 말머리 ID/이름을 확보한 경우 목록에서 얻은 값을 우선 사용
    - 메이저 갤러리 또는 말머리 요소가 없으면 `subject_head=null`
  - `(펌)` 여부
    - `h3.title > b.font_blue009` 의 텍스트가 `(펌)`이면 `is_repost=true`
    - 또는 `.writing_view_box .write_div script` 안에 `/ajax/pum_ajax/get_contents` 호출이 있으면 `is_repost=true`
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
  - 본문 콘텐츠
    - 기준 컨테이너: `.writing_view_box .write_div`
    - 저장 기준: `2.1.4. 본문 콘텐츠 및 미디어 수집`의 `content.blocks` 구조
    - 텍스트 추출 전 제거: `.img_comment`, `.image_comment`, `.tip_box2`, `.num.img`, `button`, `script`
    - `content.text`: 텍스트성 블록을 합친 분석용 순수 텍스트
    - `content.blocks`: 원문 순서를 보존한 `text`, `link`, `image`, `dc_video`, `inline_video`, `youtube`, `series` 블록 배열
    - `(펌)` 게시글은 `.write_div` 전체 텍스트를 그대로 쓰면 원글 카드의 갤러리명/조회수/추천수까지 섞이므로, 원글 카드 내부 본문은 `.cloned_card_body p` 또는 AJAX 응답 HTML의 `.cloned_card_body`를 우선 사용
    - `(펌)` 원글 카드 이미지/동영상도 같은 `content.blocks` 구조로 저장하되, 원글 카드 메타데이터는 `repost` 객체에만 저장
  - 미디어 파일 저장 or URL 수집 (옵션)
    - 이미지, DC 업로드 동영상, inline mp4, 디시콘은 URL/메타데이터만 저장하거나 파일 다운로드 가능
    - YouTube 등 외부 임베드는 URL/메타데이터만 저장하고 파일 다운로드 대상에서 제외
    - 다운로드 파일 경로는 각 블록의 `download.path`에 저장
  - `(펌)` 원 게시글 정보
    - 렌더링된 DOM 기준 원글 카드: `#pum_container.cloned_card`
    - BeautifulSoup + requests 기준으로는 JavaScript가 실행되지 않으므로 `.write_div script` 에서 `/ajax/pum_ajax/get_contents` 호출을 찾고 직접 AJAX 요청
    - AJAX 요청: `POST https://gall.dcinside.com/ajax/pum_ajax/get_contents`
      - form data: `ci_t=<script의 ci_t>`, `_GALLTYPE_=<script의 _GALLTYPE_>`, `id=<원글 갤러리 ID>`, `no=<원글 번호>`
      - 요청 헤더: `X-Requested-With: XMLHttpRequest`, `Content-Type: application/x-www-form-urlencoded; charset=UTF-8`
    - AJAX 응답 HTML 파싱
      - 원글 갤러리명/링크: `header.gallview_head a[href*="/board/lists"]`
      - 원글 갤러리 ID: 갤러리 링크 또는 원글 링크의 `id` 쿼리 값
      - 원글 번호: `.cloned_card_body > a[href*="/board/view"]` 의 `no` 쿼리 값
      - 원글 유저명: `header.gallview_head .gall_writer .nickname`
      - 원글 유동닉 여부: `.nickname .ip` 가 있으면 `floating`, 없으면 `fixed`
      - 원글 조회수: `header.gallview_head .gall_count` 의 `"조회 NNN"` 값
      - 원글 추천수: `header.gallview_head .gall_reply_num` 의 `"추천 NNN"` 값
      - 원글 댓글 수는 `repost` JSON에 저장하지 않음
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
    - 게시글 메타데이터, `content.blocks` 본문 콘텐츠, 댓글, 덧글을 수집
    - 수집 결과는 게시글 단위로 JSON 저장소에 기록
  - 3단계: 종료 조건
    - 링크 수집 워커가 설정 범위를 벗어나면 Queue 추가 중단
    - Queue가 비고 모든 게시글 수집 워커가 종료되면 job 완료
  - 실패 처리
    - 게시글 요청 실패 시 같은 링크를 제한 횟수만 재시도
    - 제한 횟수 초과 시 실패 목록에 `(gallery_id, post_number, url, reason)` 저장

## 3. 기술 스택
  - Proxy를 통한 requests 요청 전송
  - 요청별 세션 분리 (쿠키 reset)
  - BeautifulSoup 라이브러리를 활용한 HTML 파싱
  - json 라이브러리를 활용한 JSON 처리
  - user-agents.txt 리스트 이용 User-Agent 주기적교체
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
│   ├── proxy.py
│   ├── user_agent.py
│   └── logger.py
├── config/
│   └── settings.py
├── User-Agent.txt
├── Proxy-Profile.txt
├── Checkpoint.json
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

### ?.3. 텔레그램 작업 예약 및 알림 시스템
- 텔레그램 봇을 활용한 작업 예약 및 알림 시스템 구축
- 작업 상태 알림 및 결과 전송 기능
- 터미널에서 봇 토큰 입력

### ?.4. 통합 작업 관리 시스템
- 마스터 컨테이너 - 워커 컨테이너 구조 기반의 통합 작업 관리 시스템 구축
- 작업 컨테이너 스케줄링 및 모니터링 기능
- 작업 상태 시각화 및 알림 기능
- 작업 실패 시 재시도 및 오류 로그 관리

### ?.5. 커뮤니티 통합 스크래퍼
- 통합 스크래핑 시스템의 디시인사이드용 워커 컨테이너로 스케줄링 및 스케일링

## ?. 미들웨어 활용 계획
MCP, 라이브러리, KubeRay, 커뮤니티 통합 스크래퍼
