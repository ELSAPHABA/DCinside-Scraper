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
  - 작성일
  - 내용 (텍스트 및 이미지)
  - 댓글 + 덧글 (글쓴이, 작성일, 내용)

#### 2.1.2. 수집 방식 (수정 중)
  - 갤러리 ID 수집
  - 글 번호 범위 수집 
  - 작성일 수집 
  - 댓글은 게시글 하위로 수집
  - 글자만 수집 / 이미지 포함 수집 옵션

#### 2.1.2.1. 수집 옵션 (수정 중)
  - 갤러리 수집옵션
    - 전체 갤러리 수집
    - 특정 갤러리 수집
  - 글 수집옵션
    - 전체 글 수집
    - 특정 글 수집
    - 특정 기간 글 수집
    - 특정 글번호 범위 글 수집
  - 검색옵션
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
      "search_keyword": "검색 키워드"
    {
      "gallery_id": "example",
      "post_number": 12345,
      "title": "Example Post",
      "author": "Example User",
      "date": "2023-01-01-12:00:00",
      "content": "This is an example post.",
      "images": ["image1.jpg", "image2.jpg"],
      "comments": [
        {
          "author": "Commenter1",
          "date": "2023-01-02-12:00:00",
          "content": "This is a comment.",
          "replies": [
            {
              "author": "Replier1",
              "date": "2023-01-03-12:00:00",
              "content": "This is a reply to the comment."
            },
            {
              "author": "Replier2",
              "date": "2023-01-04-12:00:00",
              "content": "This is another reply to the comment."
            },
            {
              "author": "Replier3",
              "date": "2023-01-05-12:00:00",
              "content": "emoji-62b5df2be09d3ca567b1c5bc12d46b394aa3b1058c6e4d0ca4164.jpg"
            }
          ]
        },
        {
          "author": "Commenter2",
          "date": "2023-01-03-12:00:00",
          "content": "This is another comment.",
          "replies": []
        }
      ]
    },
    {
      "gallery_id": "example",
      "post_number": 12346,
      "title": "Another Example Post",
      "author": "Example User2",
      "date": "2023-01-02-12:00:00",
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

#### 2.2.1 갤러리 검색 API
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
  - 검색 기준점: `&search_pos=<검색_기준점>`
    - 


#### 2.2.2. 통합 검색 API
  - 대상: 전체 갤러리 검색
  - 기본 링크: https://search.dcinside.com/post/
  - 순서: /p/<페이지>/sort/<latest or accuracy>/q/<키워드>
  - page: 페이지 번호
    - 시작값: 1
    - 최대값: 120
    - `#dgn_btn_paging` 의 마지막 `<a>` 태그의 텍스트 값이 변하지 않으면 마지막 페이지로 판단
    - latest: 최신순
    - accuracy: 정확도순
  - q: 키워드
    - 키워드는 UTF-8 16진수로 변환
      - 디시: `.EB.94.94.EC.8B.9C`
      - 갤러리: `.EA.B0.A4.EB.9F.AC.EB.A6.AC`
    - 스페이스는 `.20`로 치환

## 3. 기술 스택 (수정 중)
  - requests 라이브러리를 활용한 Proxy 요청
  - 요청별 세션 분리 (쿠키 reset)
  - BeautifulSoup 라이브러리를 활용한 HTML 파싱
  - json 라이브러리를 활용한 JSON 처리
  - user-agents 라이브러리를 활용한 User-Agent 랜덤 생성
  - 비동기 처리를 위한 asyncio 라이브러리 활용
  - httpx 라이브러리를 활용한 비동기 HTTP 요청
  - Queue를 활용한 job 관리

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
