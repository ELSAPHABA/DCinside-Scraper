# DCinside Scraper Function Specification

디시인사이드 갤러리 게시글 및 댓글 스크래퍼 상세 가이드

## 1. 프로젝트 개요
- **목표**: 
  - 디시인사이드 갤러리의 게시글 및 댓글을 스크래핑하여 데이터베이스에 저장
  - 빠르고 다양한 게시글 검색 기능
- **기술 스택**: `beautifulsoup`, `httpx`, `user-agents`, `json`, `polars`
  - **스크래핑**: BeautifulSoup + httpx 기반 비동기 요청
  - **데이터 저장**: 로컬 JSONL/미디어 파일, 컨테이너 환경의 S3 호환 객체 저장소, PostgreSQL 체크포인트

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
    - `content.text`: 검색/미리보기/Polars 분석용 순수 텍스트
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
    - 노키워드 기간 및 글번호 범위 수집
      - 갤러리 검색 URL에 `s_type=search_subject_memo&s_keyword=%20`을 사용해 검색 상태를 만든 뒤 작성일 빠른 이동으로 시작 위치를 계산
      - 키워드 없이 특정 작성일 범위와 글번호 범위만으로 게시글 수집
    - 실시간 키워드 수집
      - 환경변수로 활성화
      - 지정 키워드의 최신 검색 결과를 반복 확인해 새 게시글만 수집
    - 실시간 전체 수집
      - 환경변수로 활성화
      - 지정 갤러리의 최신 목록을 반복 확인해 새 게시글만 수집
    - 파싱 실패 게시글 재처리
      - 전체 Job을 다시 실행하지 않고 기존 `failures.jsonl`의 parser-stage 실패 게시글만 재수집
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
    - 노키워드 검색 기간/글번호 범위 검색
    - 심층검색
      - 통합 검색으로 키워드가 발견되는 갤러리 목록을 먼저 만들고, 각 갤러리에서 갤러리 내 키워드 검색을 수행
      - 통합 검색의 120페이지 제한을 보완하기 위한 수집 모드
      - 글번호 범위 또는 기간 범위 중 하나 이상을 반드시 입력
  - 실시간 수집 옵션
    - 환경변수
      - `DCINSIDE_REALTIME_ENABLED=true`
      - `DCINSIDE_REALTIME_MODE=keyword|all`
      - `DCINSIDE_REALTIME_KEYWORD=<검색어>` (`keyword` 모드에서 필수)
      - `DCINSIDE_REALTIME_DURATION_SECONDS=<실행_초>`
      - `DCINSIDE_REALTIME_END_AT=<UTC_ISO-8601_종료시각>`
      - `DCINSIDE_REALTIME_POLL_INTERVAL_SECONDS=<반복_주기_초>` (없으면 전역 요청 간격 사용)
    - `DCINSIDE_REALTIME_DURATION_SECONDS`와 `DCINSIDE_REALTIME_END_AT` 중 정확히 하나만 입력
    - 둘 다 없거나 둘 다 있으면 실시간 Job 시작 실패
    - 종료 조건 도달 시 `status="completed"`로 최종 체크포인트 저장 후 종료
    - 수동 중단, 오류, CAPTCHA 감지 시 기존 중단 처리와 동일하게 `status="stopped"` 저장 후 종료
  - 요청 옵션
    - User-Agent Mixer
      - 차단 회피를 위해 요청 시 사용할 User-Agent를 주기적으로 교체
      - User-Agent 목록 파일명은 `user-agents.txt`로 통일
      - 컨테이너 이미지 생성 시 `user-agents.txt`를 포함
      - 로컬 실행 시 실행 파일과 같은 위치의 `user-agents.txt`를 자동 로드
      - 터미널 옵션에서 파일 탐색기 창을 열어 User-Agent 목록 파일을 불러오고, 실행 파일과 같은 위치의 `user-agents.txt`로 저장/교체 가능
      - `user-agents.txt`는 사용자가 직접 편집할 수 있도록 비인코딩 평문으로 저장
      - 파일 포맷은 한 줄에 User-Agent 하나
      - 빈 줄은 무시
      - 파일이 없거나 유효한 User-Agent가 없으면 기본 User-Agent 하나만 사용
      - User-Agent 교체 주기 기본값은 요청 10회마다 1회
      - 교체 주기는 터미널 옵션에서 요청 횟수 기준으로 변경 가능
      - 비동기 멀티 워커 실행 시에도 컨테이너/프로세스 내부 공용 요청 카운터 기준으로 교체
      - 컨테이너 간 User-Agent 교체 카운터는 공유하지 않음
    - Proxy
      - Proxy를 통해 httpx 요청 전송
      - Proxy 설정은 실행 파일과 같은 위치의 `.env` 파일에 저장
      - `.env`는 사용자가 직접 편집할 수 있도록 비인코딩 평문으로 저장
      - 저장 변수
        - `DCINSIDE_PROXY_HOST=<host:port 또는 proxy URL>`
        - `DCINSIDE_PROXY_ID=<proxy ID>`
        - `DCINSIDE_PROXY_PW=<proxy password>`
      - 로컬 실행 Flow
        - 사용자가 터미널에서 Proxy 옵션을 켠 경우 이를 최우선으로 처리
        - Proxy 옵션을 켜면 host, ID, PW를 터미널에서 입력받고, 입력한 값을 `.env`에 저장한 뒤 현재 실행에 사용
        - 사용자가 Proxy 옵션을 켜지 않았고 실행 파일과 같은 위치에 `.env`가 있으면 `.env`의 Proxy 변수를 자동 사용
        - `.env`가 없거나 유효한 Proxy 변수가 없으면 Proxy 비활성화
      - 컨테이너 실행 Flow
        - 컨테이너 이미지는 `docker-entrypoint.sh`를 포함
        - `.dockerignore`는 `.git`, 가상환경, 테스트 캐시, 출력물, `.env` 계열 secret 후보, 문서 산출물을 Docker build context에서 제외
        - `docker run` 시 환경변수로 `DCINSIDE_PROXY_HOST`, `DCINSIDE_PROXY_ID`, `DCINSIDE_PROXY_PW`를 입력 가능
        - Docker `--env-file`을 통해 `.env` 형식 파일을 환경변수로 주입하는 방식도 허용
        - `docker-entrypoint.sh`는 Docker 전용 시작 스크립트이며, 전달받은 argv를 유지한 채 `python -m dcinside_scraper.adapters.container "$@"`로 실행을 위임
        - 컨테이너 내부 프로그램은 Docker가 주입한 환경변수를 직접 읽어 Proxy를 적용
      - `.env`는 문서화된 보안 예외로 평문 저장을 허용하되, `.gitignore` 포함과 터미널 경고를 필수로 함
      - 로그에는 Proxy password, raw `.env` 내용, 인증정보가 남지 않아야 함
    - 스크래핑 속도 조절
      - 요청 사이의 대기 시간을 사용자가 설정 가능
      - 기본값은 안정성을 우선하여 너무 빠른 연속 요청을 피하도록 설정
      - 갤러리 목록, 통합 검색, 게시글 상세, `(펌)` AJAX, DC 동영상 iframe, 댓글 API, 이미지/동영상/디시콘 다운로드 요청에 동일하게 적용
      - CAPTCHA 또는 차단 의심 응답 발생 시 즉시 작업 중단 후 중단점 저장
    - CAPTCHA 대응
      - CAPTCHA 페이지 또는 비정상 접근 차단 응답 포착 시 현재 작업 중단
      - 중단 시 작업 상태를 `stopped`로 변경하고 최종 체크포인트를 저장한 뒤 프로세스 종료
      - 체크포인트 저장 후 터미널과 로그에 저장된 `job_id` 출력
      - CAPTCHA 자동 우회는 구현하지 않음
    - 중단점 저장 및 불러오기
      - 정상 진행 중에는 작업 상태를 `running`으로 기록
      - 게시글 10개 처리 완료마다 체크포인트 저장
      - 작업 중단, 복구 불가능한 오류, CAPTCHA 감지 시 즉시 체크포인트 저장
      - 사용자가 선택하면 저장된 체크포인트부터 수집 재개
      - 로컬 환경에서는 체크포인트 파일을 실행 파일과 같은 위치의 `Checkpoint.json`에 저장

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
    - BeautifulSoup/httpx 스크래퍼는 게시글 URL을 `Referer`로 두고 `iframe_url`을 추가 요청하여 `video.dc_mv`, `source[type="video/mp4"]`, `poster`, 다운로드 hidden 값, 동영상 설명을 파싱
    - 동영상 설명은 iframe 내부 `div.video_infobox > div.box > div.video_txt > div.inr > p` 텍스트를 저장
    - 설명이 없거나 빈 값이면 `description=null` 저장
    - 파싱 가능하면 `description`, `video_url`, `poster_url`, `download_url` 저장
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
  - 컨테이너 운영 시 JSONL과 미디어는 S3 호환 객체 저장소에 저장하고 체크포인트는 PostgreSQL에 저장
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
            "description": "동영상 설명",
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

#### 2.1.6. 작업 상태 및 체크포인트 저장
  - 상태 및 체크포인트 JSON은 디시인사이드뿐 아니라 향후 에펨코리아, 루리웹, 인벤 등 커뮤니티 스크래퍼가 공유하는 공통 스키마로 관리
  - 게시글 본문 JSONL 스키마는 커뮤니티별로 독립 확장 가능
  - 저장 시점
    - 각 게시글 스크래핑 및 JSONL 저장 완료 후 메모리상의 진행 상태 갱신
    - 게시글 10개 처리 완료마다 체크포인트 저장
    - 수동 중단, 정상 종료, 복구 불가능한 오류, CAPTCHA 또는 차단 감지 시 즉시 체크포인트 저장
  - 저장 순서
    - 게시글 결과를 먼저 멱등하게 저장
    - 게시글 저장 성공 후 `last_completed_post_id`, `last_completed_url`, `scraping_processed_count` 갱신
    - 체크포인트 저장은 원자적으로 처리
  - 상태 값
    - `running`: 정상 수집 진행 중
    - `stopped`: 수동 중단, 오류, CAPTCHA, timeout, lease 만료 등으로 중단
    - `completed`: Queue가 비고 모든 워커가 정상 종료
  - 중단 사유 `reason`
    - `captcha`
    - `manual_stop`
    - `error`
    - `timeout`
    - `lease_expired`
  - 중단 처리
    - `status="stopped"`로 변경
    - 최종 체크포인트 저장
    - 터미널과 로그에 저장한 체크포인트 `job_id` 출력
    - 프로세스 종료
  - 재개 처리
    - 로컬 환경은 터미널 옵션으로 체크포인트 `job_id`를 입력받아 재개
    - 컨테이너 환경은 `docker run` 환경변수 `RESUME=true`, `JOB_ID=<checkpoint job_id>`로 재개
    - 재개 요청 시 `JOB_ID`가 없으면 가장 최근 체크포인트를 자동 선택
    - 재개 시 기존 JSONL 파일에 이어 쓰지 않고 새 JSONL 파일을 생성해 중단점 이후부터 기록
    - 이미 저장된 게시글은 `(site_id, board_id, post_id)` 또는 커뮤니티별 고유 key로 중복 저장되지 않도록 처리
  - 저장소 정책
    - 로컬 환경: `Checkpoint.json`과 Job JSONL 파일을 실행 파일과 같은 위치에 저장
    - 단일 컨테이너 환경: 체크포인트는 PostgreSQL 컨테이너에 저장, Job JSONL 파일과 다운로드 미디어는 S3 호환 오브젝트 스토리지에 저장
      - 기본 구현 대상은 Garage
      - 구현은 Garage 전용 API가 아니라 S3 호환 접속 설정을 사용
      - S3 호환 접속 환경변수: `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_REGION`, `S3_FORCE_PATH_STYLE`
      - SeaweedFS는 대량 미디어/소파일 저장, FUSE, Iceberg 등 고급 저장소 요구가 생길 때 대체 저장소로 검토
    - AWS CDK 배포 환경: `infra/cdk`에서 ECS Fargate 워커, AWS S3 출력 bucket, RDS PostgreSQL 체크포인트 저장소, Secrets Manager secret 주입, CloudWatch Logs/EventBridge 알림 구성을 제공
      - CDK는 워커 이미지 빌드를 수행하지 않고, 사전에 push된 image URI/tag를 참조
      - CDK 배포에서도 namespace, object key, checkpoint key는 공유 저장소 규약을 따름
    - 향후 통합 플랫폼 환경: SQS 기반 Job Queue와 중앙 scheduler를 추가해 여러 커뮤니티 워커 컨테이너를 공통 방식으로 실행
  - 향후 SQS 기반 통합 플랫폼 처리 흐름
    - Queue에서 작업 획득
    - 작업 lease 설정
    - 게시글 요청 및 파싱
    - 게시글 결과를 멱등하게 저장
    - 게시글 처리 완료 기록
    - 다음 작업으로 진행
    - 주기적으로 lease 갱신
  - 작업 진행 상태 JSON 예시:
    ```json
    {
      "job_id": "crawl-20260729-001",
      "site_id": "dcinside",
      "board_id": "example-board",
      "last_completed_post_id": "184920",
      "last_completed_url": "https://example.com/posts/184920",
      "scraping_processed_count": 1380,
      "worker_id": "pod-7f86c",
      "lease_until": "2026-07-29T15:05:00Z",
      "status": "running",
      "updated_at": "2026-07-29T14:57:00Z"
    }
    ```
  - 실행 중단 원인 JSON 예시:
    ```json
    {
      "status": "stopped",
      "job_id": "crawl-20260729-002",
      "reason": "captcha",
      "detected_at": "2026-07-29T15:01:10Z",
      "retry_after": null,
      "proxy_host": "proxy-host-17",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
      "account_id": null
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
  - 심층검색: "deep" 형식

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
      - httpx 요청의 `params`로 전달하거나, 직접 URL 생성 시 UTF-8 URL 인코딩
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
  - 후보 게시글 행 파싱
    - 갤러리 내 검색 단계의 목적은 최종 게시글 JSON을 완성하는 것이 아니라, 게시글 상세 URL과 필터링/중복 제거에 필요한 후보 메타데이터를 수집하는 것이다.
    - 최종 저장용 `말머리`, `제목`, `글쓴이`, `작성일`, `조회수`, `추천수`, 본문, 댓글은 `2.2.3. 게시글 상세 페이지 수집` 단계에서 게시글 링크를 열어 다시 파싱한다.
    - 목록 단계에서 수집한 제목/작성자/작성일/조회수/추천수는 `PostCandidate.metadata` 또는 진단/리포트용 힌트로만 사용한다.
    - 목록 행: `.gall_listwrap.list tbody tr.ub-content.us-post`
    - 광고/공지 행은 `.gall_num` 값이 `-` 이거나 `us-post` 클래스가 없으므로 제외
    - 후보 글 번호: `.gall_num`
    - 후보 말머리: `.gall_subject`
      - `.gall_subject .subject_inner`가 있으면 전체 말머리 이름으로 우선 사용
      - `.subject_inner`가 없으면 `.gall_subject`의 직접 텍스트 노드를 사용
      - 후보 말머리 ID는 현재 요청 URL 또는 상세 링크의 `search_head` 쿼리 값으로 저장
      - 상세 페이지에서 말머리 ID를 확정하기 어려운 경우 보조값으로 사용할 수 있으나, 최종 저장용 말머리 이름은 상세 페이지 값을 우선한다.
    - 후보 제목/상세 링크: `.gall_tit a`
    - 후보 `(펌)` 여부: `.gall_tit > b.font_blue009` 의 텍스트가 `(펌)`이면 후보 `is_repost=true`
      - `.gall_tit span.mark` 는 검색어 하이라이트이므로 단독으로 `(펌)` 판정에 사용하지 않음
      - 최종 JSON의 `is_repost`, `title`, `repost` 객체는 상세 페이지 수집 단계에서 다시 확정한다.
    - 후보 글쓴이: `.gall_writer`
    - 후보 작성일: `.gall_date`의 `title` 값 우선, 없으면 텍스트 값
    - 후보 조회수: `.gall_count`
    - 후보 추천수: `.gall_recommend`

##### 2.2.1.1. 게시글 작성일 이동
  - 빠른 이동 UI는 내부적으로 `/ajax/search_ajax/search_date/` 를 호출해 해당 날짜의 `search_pos`를 받은 뒤 목록 URL로 이동한다.
  - 요청: `POST https://gall.dcinside.com/ajax/search_ajax/search_date/`
    - form data: `ci_t=<ci_c 쿠키 값>`, `date=YYYY-MM-DD`, `id=<갤러리 ID>`, `keyword=<검색어>`, `s_type=<검색옵션>`, `_GALLTYPE_=<갤러리 타입>`
  - 응답: `{"result":"success","data":"<search_pos>"}` 형식이면 `search_pos=<data>` 로 갤러리 검색 목록을 요청
  - 실패하거나 `data`가 없으면 해당 날짜 이동 결과 없음으로 처리

##### 2.2.1.1.1. 노키워드 기간 및 글번호 범위 수집
  - 대상: 키워드 없이 특정 갤러리의 작성일 범위와 글번호 범위만으로 게시글 수집
  - 초기 URL
    - `/mgallery/board/lists/?id=<갤러리_ID>&s_type=search_subject_memo&s_keyword=%20`
    - 일반 갤러리는 `/board/lists/`, 마이너 갤러리는 `/mgallery/board/lists/`
    - `s_keyword=%20`으로 요청하면 검색 상태가 유지되며 작성일 빠른 이동 UI가 활성화됨
  - 분석된 DOM 구조
    - 빠른 이동 버튼: `#container > section.left_content > article:nth-child(3) > div.bottom_paging_wrap > div.bottom_movebox > button`
    - 빠른 이동 버튼 class: `.btn_schmove`
    - 빠른 이동 레이어: `.fast_move_lyr`
    - 작성일 입력: `#calendarInput`
      - `type="text"`
      - `class="dayin calendar"`
      - `readonly`
      - 값 형식: `YYYY-MM-DD`
    - 확인 버튼: `.fast_move_btn`
  - 스크래퍼 구현 방식
    - 브라우저 클릭 없이 `POST /ajax/search_ajax/search_date/`를 직접 호출
    - `keyword` form 값은 빈 문자열로 전달
      - 초기 URL의 `s_keyword=%20`은 화면에서 검색 상태를 만들기 위한 값이며, DOM의 hidden `#s_keyword` 값은 빈 문자열로 정규화됨
    - 요청 form data:
      - `ci_t=<ci_c 쿠키 값>`
      - `date=<YYYY-MM-DD>`
      - `id=<갤러리_ID>`
      - `keyword=`
      - `s_type=search_subject_memo`
      - `_GALLTYPE_=<갤러리 타입>`
    - 응답 예시:
      ```json
      {
        "result": "success",
        "data": "-2479616"
      }
      ```
    - `data` 값을 `search_pos`로 사용해 목록 URL 생성
      - `/mgallery/board/lists/?id=<갤러리_ID>&search_pos=<data>&s_type=search_subject_memo&s_keyword=`
  - 기간/글번호 범위 처리
    - `date_to`가 있으면 `date_to`로 작성일 빠른 이동을 먼저 수행
    - 이동한 검색 구간에서 `page=1`부터 수집
    - 이후 기존 갤러리 검색 수집 규칙처럼 page와 `search_next`를 따라감
    - 게시글 작성일이 `date_from`보다 과거이거나 글번호가 `min_post_no`보다 작아지면 수집 종료
    - `date_from <= 작성일 <= date_to`, `min_post_no <= 글번호 <= max_post_no` 조건을 만족하는 게시글만 Queue에 추가

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

#### 2.2.2.1. 심층검색
  - 목적
    - 통합 검색 결과가 최대 120페이지까지만 제공되는 한계를 보완
    - 키워드가 등장하는 갤러리를 먼저 찾고, 각 갤러리의 갤러리 내 검색으로 같은 키워드를 다시 수집
  - 필수 입력
    - 키워드
    - 글번호 범위 또는 기간 범위 중 하나 이상
      - 글번호 범위 예: `min_post_no`, `max_post_no`
      - 기간 범위 예: `date_from`, `date_to`
    - 둘 다 없으면 심층검색 Job 시작 실패
  - 1단계: 통합 검색 기반 갤러리 후보 수집
    - 기존 `2.2.2. 통합 검색 API`를 사용해 키워드 검색 수행
    - 통합 검색 페이지는 최대 120페이지까지만 탐색
    - 각 검색 결과에서 갤러리 후보 추출
      - `gallery_id`: 상세 URL의 `id` 쿼리 값
      - `gallery_type`: 상세 URL 경로가 `/board/view/`이면 일반 갤러리, `/mgallery/board/view/`이면 마이너 갤러리
      - `gallery_name`: 통합 검색 결과의 `p.dsc_sub > a.sub_txt` 텍스트
      - `gallery_url`: 통합 검색 결과의 `p.dsc_sub > a.sub_txt[href]`
    - 갤러리 후보는 `(gallery_type, gallery_id)` 기준으로 중복 제거
    - 갤러리 후보가 없으면 Job 완료 처리
  - 2단계: 갤러리별 키워드 검색
    - 후보 갤러리마다 기존 `2.2.1 갤러리 내 검색 API`로 키워드 검색 수행
    - 기본 검색 옵션은 `s_type=search_subject_memo`
    - 사용자가 검색 필드를 지정하면 해당 `s_type`을 사용
    - 마이너 갤러리는 `/mgallery/board/lists/`, 일반 갤러리는 `/board/lists/` 사용
    - 각 갤러리에서 `page`와 `search_pos` 순서대로 탐색
    - 기간 범위가 있으면 작성일 빠른 이동 API로 `date_to`의 `search_pos`를 먼저 계산할 수 있음
    - 글번호 범위 또는 기간 범위를 벗어나면 해당 갤러리 검색 종료
  - 3단계: 게시글 링크 수집 및 중복 제거
    - 최종 게시글 후보는 `(gallery_id, post_number)` 기준으로 중복 제거
    - 통합 검색 1단계에서 발견한 게시글도 같은 dedupe set에 포함
    - 조건에 맞는 게시글만 게시글 수집 Queue에 추가
  - 저장 및 로그
    - Job metadata에 심층검색 모드와 발견한 갤러리 후보 수를 기록
    - 갤러리별 수집 성공/실패/범위 종료 건수를 structured log에 기록
    - 실패한 갤러리는 전체 Job을 실패시키지 않고 실패 목록에 `(gallery_id, gallery_type, reason)` 형식으로 기록

  #### 2.2.3. 게시글 상세 페이지 수집
  - 갤러리: 게시글 URL의 `id` 값
  - 글 번호: 게시글 URL의 `no` 값
  - 제목: `.title_subject`
    - `(펌)` 게시글이면 JSON 저장용 제목에서 `(펌)` 문자열을 제거
    - 예: `.title_subject` 값이 `(펌) 이거 뭐냐?` 이면 `"title": "이거 뭐냐?"`
    - 실사이트 smoke test 반영: `h3.title` 전체 텍스트에는 말머리, `(펌)`, 모바일/앱 작성 표시가 같이 들어갈 수 있으므로 JSON 저장용 제목은 우선 `.title_subject` 텍스트만 사용
    - `.title_subject`가 없을 때만 `h3.title`, `.gallview_head .title`, `<title>`을 fallback으로 사용하고, fallback 텍스트에서는 `b.font_blue009`, `.title_headtext`, `.headtext`, `.title_device`, `.blind` 값을 제거
    - `"모바일에서 작성"`, `"앱에서 작성"` 같은 기기 표시 또는 blind 접근성 텍스트는 제목으로 저장하지 않음
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
    - 실사이트 smoke test 반영: `viewimage.php?no=` 값이 항상 짧은 파일 번호가 아닐 수 있으며, 긴 서명 토큰 형태로 내려오면 이를 `media_id` 또는 `file_no`로 저장하지 않음
    - 긴 이미지 식별자/서명 토큰은 원본 `url` 또는 `source_url`에만 보존하고, `media_id`는 `null`로 저장
    - `movie_view?no=<숫자>`처럼 짧고 안정적인 자체 동영상 번호는 기존처럼 `media_id`로 저장 가능
  - `(펌)` 원 게시글 정보
    - 렌더링된 DOM 기준 원글 카드: `#pum_container.cloned_card`
    - BeautifulSoup + httpx 기준으로는 JavaScript가 실행되지 않으므로 `.write_div script` 에서 `/ajax/pum_ajax/get_contents` 호출을 찾고 직접 AJAX 요청
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
  - 대상: 갤러리 내 검색 API, 통합 검색 API, 심층검색에서 얻은 게시글 링크
  - 1단계: 링크 수집 워커
    - 단일 워커가 검색 결과 페이지를 순차 탐색
    - 갤러리 내 검색은 `page`와 `search_pos` 순서대로 탐색
    - 통합 검색은 최신순 `/post/p/<페이지>/q/<키워드>`, 정확도순 `/post/p/<페이지>/sort/accuracy/q/<키워드>` 순서대로 탐색
    - 심층검색은 통합 검색으로 갤러리 후보를 먼저 수집한 뒤 후보 갤러리별 갤러리 내 검색을 순차 탐색
    - 설정 범위(글 번호, 작성일, 최대 페이지 등)에 맞는 게시글 링크와 후보 메타데이터만 Queue에 추가
    - 중복 게시글은 `(gallery_id, post_number)` 기준으로 제거
  - 2단계: 게시글 수집 워커
    - 여러 워커가 Queue에서 게시글 링크를 가져와 병렬 비동기 수집
    - 게시글 상세 페이지를 열어 최종 저장용 게시글 메타데이터, `content.blocks` 본문 콘텐츠, 댓글, 덧글을 수집
    - 수집 결과는 게시글 단위로 JSON 저장소에 기록
    - 게시글 저장 완료 후 체크포인트 진행 상태를 갱신
    - 게시글 10개 처리 완료마다 체크포인트 저장
  - 3단계: 종료 조건
    - 링크 수집 워커가 설정 범위를 벗어나면 Queue 추가 중단
    - Queue가 비고 모든 게시글 수집 워커가 종료되면 `status="completed"`로 최종 체크포인트 저장 후 job 완료
  - 실패 처리
    - 게시글 요청 실패 시 같은 링크를 제한 횟수만 재시도
    - 제한 횟수 초과 시 실패 목록에 `(gallery_id, post_number, url, reason)` 저장
    - parser-stage 게시글 실패는 원본 `failures.jsonl`을 보존한 뒤 `retry-failures` 재처리 경로로 별도 회수 가능

  #### 2.2.5. 실시간 수집 흐름
  - 대상
    - 실시간 키워드 수집: 지정 키워드의 최신 검색 결과를 반복 확인
    - 실시간 전체 수집: 지정 갤러리의 최신 목록을 반복 확인
  - 활성화 조건
    - `DCINSIDE_REALTIME_ENABLED=true`
    - `DCINSIDE_REALTIME_MODE=keyword|all`
    - `keyword` 모드에서는 `DCINSIDE_REALTIME_KEYWORD` 필수
  - 종료 조건
    - `DCINSIDE_REALTIME_DURATION_SECONDS` 또는 `DCINSIDE_REALTIME_END_AT` 중 정확히 하나만 필수
    - `DCINSIDE_REALTIME_END_AT`은 UTC ISO-8601 문자열 사용
    - 두 값이 모두 있거나 둘 다 없으면 validation 오류로 Job 시작 실패
  - 반복 처리
    - 반복 주기는 `DCINSIDE_REALTIME_POLL_INTERVAL_SECONDS` 사용
    - 값이 없으면 전역 요청 간격을 사용
    - 매 반복마다 최신 목록 또는 최신 검색 결과의 `page=1`부터 확인
    - 이미 처리한 게시글은 `(gallery_id, post_number)` 기준으로 건너뜀
    - 새 게시글만 게시글 수집 Queue에 추가
  - 실시간 키워드 수집
    - 기존 갤러리 내 검색 또는 통합 검색 진입점 설정을 재사용
    - 각 반복은 최신 검색 구간에서 시작하며 최초 `search_pos`는 생략하거나 빈 값으로 요청
  - 실시간 전체 수집
    - 지정 갤러리의 `/board/lists/` 또는 `/mgallery/board/lists/` 최신 목록을 반복 확인
    - 검색 키워드 없이 `page=1`의 신규 게시글을 기준으로 수집
  - 상태/체크포인트
    - 실시간 실행 중에도 `status="running"` 기록
    - 게시글 10개 처리 완료마다 체크포인트 저장
    - 타이머 또는 종료 시각에 도달하면 `status="completed"`로 최종 체크포인트 저장
    - 수동 중단, 오류, CAPTCHA 감지 시 `status="stopped"`로 최종 체크포인트 저장

## 3. 기술 스택
  - Proxy를 통한 httpx 요청 전송
  - `.env` 파일 기반 Proxy 환경변수 로드
  - 요청별 세션 분리 (쿠키 reset)
  - BeautifulSoup 라이브러리를 활용한 HTML 파싱
  - json 라이브러리를 활용한 JSON 처리
  - Polars 라이브러리를 활용한 JSONL 가공 및 분석
  - user-agents.txt 리스트 이용 User-Agent 주기적 교체
  - 비동기 처리를 위한 asyncio 라이브러리 활용
  - httpx 라이브러리를 활용한 비동기 HTTP 요청
  - asyncio.Queue를 활용한 링크 수집 워커 + 게시글 수집 워커 분리
  - 로컬 체크포인트는 `Checkpoint.json`, 컨테이너 체크포인트는 PostgreSQL, 컨테이너 JSONL 출력은 Garage 기반 S3 호환 오브젝트 스토리지 사용
  - AWS CDK를 활용한 ECS Fargate, AWS S3, RDS PostgreSQL 기반 선택 배포 경로 제공
  - SeaweedFS는 대량 미디어/소파일 저장, FUSE, Iceberg 요구가 생길 때 확장 후보로 유지

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
├── user-agents.txt
├── .env
├── .dockerignore
├── docker-entrypoint.sh
├── Checkpoint.json
├── pyproject.toml
└── README.md
```

## ?. 향후 확장 계획
### ?.1. 데이터베이스 확장
- PostgreSQL 기반 Job 이력/실패 요약 테이블 확장
- S3 호환 객체 저장소 기반 JSONL/미디어 보존 정책 확장
- 임베딩 처리 및 벡터 유사도 검색 (Vector Search)
- 데이터베이스 구조 설계 및 최적화
- Polars를 활용한 데이터 분석 및 시각화 기능 추가

### ?.2. 검색 기능 확장
- 검색 옵션 추가 (예: 특정 키워드 포함/제외, 정규식 검색)
- 검색 결과 필터링 및 정렬 기능 강화 

### ?.3. 텔레그램 작업 예약 및 알림 시스템
- 텔레그램 봇을 활용한 작업 예약 및 알림 시스템 구축
- 작업 상태 알림 및 결과 전송 기능
- 터미널에서 봇 토큰 입력

### ?.4. 통합 작업 관리 시스템
- 단일 스크래퍼의 AWS 배포는 `infra/cdk`의 CDK 구성으로 관리
- CDK는 VPC, S3 output bucket, RDS PostgreSQL, ECS cluster, Fargate worker task, CloudWatch Logs/EventBridge 기반 실패 감지를 구성
- CDK는 중앙 Job Queue, 통합 운영 UI, Docker image build, EKS 배포를 포함하지 않음
- 마스터 컨테이너 - 워커 컨테이너 구조 기반의 통합 작업 관리 시스템 구축
- 작업 컨테이너 스케줄링 및 모니터링 기능
- 작업 상태 시각화 및 알림 기능
- 작업 실패 시 재시도 및 오류 로그 관리
- SQS 기반 작업 큐, lease 갱신, lease 만료 시 `reason="lease_expired"` 체크포인트 저장

### ?.5. 커뮤니티 통합 스크래퍼
- 통합 스크래핑 시스템의 디시인사이드용 워커 컨테이너로 스케줄링 및 스케일링
- 향후 에펨코리아, 루리웹, 인벤 등 커뮤니티별 스크래퍼를 추가할 때 각 커뮤니티의 원본 게시글 구조는 개별 JSON 스키마로 저장
- 개별 JSON 스키마는 수집 원본 보존을 우선하며, 커뮤니티별 특수 필드는 그대로 유지

### ?.6. 공통 분석 스키마 및 Polars 정규화
- 목적: 커뮤니티별 개별 JSON 스키마를 통합 커뮤니티 전략분석 플랫폼에서 함께 분석할 수 있는 Polars 가공용 공통 스키마로 변환
- 범위: 향후 개발 참고사항이며, 1차 DCinside 스크래퍼의 필수 저장 구조를 변경하지 않음
- 처리 위치
  - 스크래핑 단계: 커뮤니티별 개별 JSONL 저장
  - 정규화 단계: 개별 JSONL을 읽어 공통 분석 테이블로 변환
  - 분석 단계: Polars로 공통 테이블을 로드해 커뮤니티 간 비교/집계 수행
- 정규화 원칙
  - 원본 JSONL은 변경하지 않고 보존
  - 공통 스키마에 없는 커뮤니티별 특수 필드는 `extra` 또는 별도 확장 컬럼으로 보존
  - 커뮤니티에 없는 값은 `null`로 채움
  - 날짜, 숫자, 추천/비추천 수, 조회수, 작성자 식별자 등 분석 필드는 타입을 통일
- 공통 테이블 기본 구조
  - `posts`
    - 게시글 단위 테이블
    - 예: `site_id`, `board_id`, `post_id`, `url`, `title`, `author_name`, `author_type`, `created_at`, `content_text`, `view_count`, `upvote_count`, `downvote_count`, `comment_count`, `scraped_at`, `job_id`
  - `comments`
    - 댓글/덧글 단위 테이블
    - 예: `site_id`, `board_id`, `post_id`, `comment_id`, `parent_comment_id`, `depth`, `author_name`, `author_type`, `body`, `created_at`, `upvote_count`, `downvote_count`, `scraped_at`, `job_id`
  - `media`
    - 이미지, 동영상, YouTube, 링크 등 본문 미디어 단위 테이블
    - 예: `site_id`, `board_id`, `post_id`, `media_id`, `media_type`, `order`, `url`, `local_path`, `description`, `scraped_at`, `job_id`
- 댓글 정규화 규칙
  - 수집 JSON에서는 댓글을 게시글 하위에 중첩 저장할 수 있음
  - Polars 공통 스키마 정규화 시 게시글과 댓글을 별도 테이블로 분리
  - 일반 댓글은 `depth=0`, `parent_comment_id=null`
  - 덧글은 `depth=1`, `parent_comment_id=<상위 댓글 ID>`
  - 게시글 테이블에는 댓글 본문을 중첩 저장하지 않고 `comment_count`와 게시글 메타데이터만 유지
- 정규화 출력 형식
  - 1차 후보: 공통 스키마별 JSONL 파일 (`posts.jsonl`, `comments.jsonl`, `media.jsonl`)
  - 대용량 분석이 필요해지면 Parquet 출력 추가 검토
- 구현 형태
  - 커뮤니티별 normalizer를 두어 `dcinside JSONL -> common posts/comments/media` 형태로 변환
  - 다른 커뮤니티도 `community JSONL -> common posts/comments/media` 변환기를 추가하는 방식으로 확장
  - 통합 분석 로직은 개별 커뮤니티 JSON이 아니라 공통 스키마만 대상으로 처리

### ?.7. Parser-stage 게시글 실패 재처리 유닛
- 목적: 전체 검색/수집 Job을 다시 실행하지 않고, 기존 실패 기록에서 parser-stage 게시글 실패만 골라 direct-post 경로로 재수집
- 구현 상태: UOW-009 `Parser Failure Retry Reprocessor`에서 구현
- 대상 실패
  - `failures.jsonl`의 `stage == "post"`
  - `reason`이 제목/작성자/게시글 식별자/metadata/content/comment 파싱 실패 계열
  - 실사이트 smoke test에서 `post title missing`처럼 일시적 비정상/부분 응답 후 같은 URL 재시도 시 정상 파싱되는 사례를 회수하기 위한 용도
- 제외 실패
  - CAPTCHA, 차단, 네트워크, 저장소, 체크포인트, 수동 중단, 취소 계열 실패
  - 위 실패는 기존 HTTP retry, checkpoint/resume, 운영 대응 절차에서 처리
- 입력
  - 로컬 실패 파일: `--failure-file <path>`
  - 로컬/S3 호환 명시 ref: `--failure-ref <local-path|file://...|s3://bucket/key>`
  - 이미 성공한 게시글 제외용 명시 파일: `--existing-posts <posts.jsonl|s3://bucket/key>`
  - 이미 성공한 게시글 제외용 로컬 root scan: `--existing-posts-root <local-directory>`
  - `--from-report`, `--from-checkpoint`는 기존 실행 결과에서 실패 입력과 호환 옵션을 복원하기 위한 예약 helper이며, 현재 실행 경로에서는 명시적인 `--failure-file` 또는 `--failure-ref` 입력을 우선 사용
- 입력 규칙
  - 하나 이상의 failure input이 필수
  - `--from-report`와 `--from-checkpoint`는 동시에 지정하면 validation 오류
  - `--existing-posts-root`는 로컬 파일시스템 전용
  - S3/Garage 입력은 `s3://bucket/key` 명시 object ref만 지원하고 prefix listing은 수행하지 않음
  - 원본 `failures.jsonl`은 읽기 전용으로 사용하며 직접 수정하지 않음
- 동작
  - 실패 record를 한 줄씩 읽고 잘못된 JSON/스키마 record는 카운트만 남기고 건너뜀
  - 재처리 후보는 `(site_id, gallery_id, post_id)` 기준으로 중복 제거하며 마지막 유효 실패 record를 사용
  - 기존 `posts.jsonl`에서 이미 성공한 `(site_id, gallery_id, post_id)`는 재처리 대상에서 제외
  - 선택된 URL을 `DirectPostSource`로 변환해 기존 JobRunner를 통해 새 Job/run으로 실행
  - 새 run에 `posts.jsonl`, `failures.jsonl`, `report.json`을 기록
- 결과 메타데이터
  - `JobReport.metadata["parser_failure_retry"]`에 재처리 요약을 저장
  - 주요 필드: `initial_failure_count`, `invalid_failure_record_count`, `ineligible_failure_count`, `selected_retry_count`, `deduped_failure_count`, `skipped_existing_count`, `success_count`, `remaining_failure_count`

## ?. 미들웨어 활용 계획
MCP, 라이브러리, KubeRay, 커뮤니티 통합 스크래퍼
