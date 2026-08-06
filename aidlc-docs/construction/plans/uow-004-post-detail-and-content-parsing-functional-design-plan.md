# Functional Design 계획 - UOW-004 Post Detail And Content Parsing

이 계획은 `UOW-004 Post Detail And Content Parsing`의 기능 설계를 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-004 Post Detail And Content Parsing
- **Depends On**: UOW-001 Core Models And Config, UOW-002 HTTP Runtime Policy
- **Primary Stories**: US-007, US-008, US-009, US-010, US-011
- **Scope**: post metadata parsing, ordered content blocks, image/media/DC video/Youtube/link/series metadata, `(펌)` AJAX card parsing, comment/reply AJAX parsing, dccon metadata parsing
- **Out Of Scope**: search/link collection, worker queue lifecycle, checkpoint persistence, JSONL/Garage storage, CLI prompt UX, container/MCP hosting

## Functional Design 작업 체크리스트

- [x] UOW-003 Build and Test 승인 확인
- [x] UOW-004 범위 확인
- [x] `docs/Function_Specification.md` 게시글 상세/댓글/미디어 항목 확인
- [x] Functional Design 질문 생성
- [x] Functional Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-004-post-detail-and-content-parsing/functional-design/business-logic-model.md` 생성
- [x] `aidlc-docs/construction/uow-004-post-detail-and-content-parsing/functional-design/business-rules.md` 생성
- [x] `aidlc-docs/construction/uow-004-post-detail-and-content-parsing/functional-design/domain-entities.md` 생성

## Functional Design Questions

### Question 1. Detail Service Contract

UOW-004의 게시글 상세 수집 결과는 어떤 형태로 제공할까요?

A) (권장) `PostDetailService`가 `PostRequest` 또는 UOW-003 `PostCandidate`와 주입된 UOW-002 `HttpClient`를 받아 `PostResult`를 반환한다. public `fetch_post`/`fetch_comments`도 HTTP client 주입을 요구한다. 저장, checkpoint, queue 투입은 후속 UOW에서 담당한다.

추천 사유: UOW-004는 상세 페이지를 `PostResult`로 만드는 책임만 가지면 됩니다. 저장/체크포인트를 넣으면 UOW-005/UOW-006 책임이 앞당겨집니다.

B) UOW-004가 `PostResult` 생성 후 JSONL 저장까지 직접 수행한다.

C) UOW-004는 parser 함수만 제공하고 HTTP fetch는 후속 UOW로 미룬다.

X) 기타

[Answer]: A

### Question 2. Metadata Parser Boundary

게시글 상세 HTML의 메타데이터 파싱은 어디까지 UOW-004에서 처리할까요?

A) (권장) BeautifulSoup 기반 `PostMetadataParser`가 제목, 말머리, 작성자, nickname type, 작성일, 조회수, 추천/비추천, 댓글 수, 갤러리 ID, 글번호, `(펌)` 표시를 `PostResult` 필드와 metadata로 변환한다.

추천 사유: 상세 fetch 이후 저장 가능한 `PostResult`를 만들려면 메타데이터는 이 unit에서 확정되어야 합니다.

B) 제목, 글번호, 본문만 파싱하고 조회수/추천수/작성자 등은 제외한다.

C) 상세 HTML 원문을 후속 저장 unit에 넘겨 저장 시점에 파싱한다.

X) 기타

[Answer]: A

### Question 3. Ordered Content Blocks

본문 콘텐츠는 어떤 구조로 파싱할까요?

A) (권장) `.writing_view_box .write_div` 하위 DOM을 순서대로 순회하여 `TextBlock`, `ImageBlock`, `DcVideoBlock`, `YouTubeBlock`, `LinkBlock`, `SeriesBlock`, `UnknownEmbedBlock`으로 변환한다. `.img_comment`, `.image_comment`, `.tip_box2`, `.num.img`, `button`, `script` 등 노이즈는 제거한다.

추천 사유: 이후 Polars/RAG 가공과 미디어 처리를 하려면 원문 순서가 보존된 block 구조가 가장 덜 깨집니다.

B) 본문 전체 텍스트와 이미지 URL 목록만 저장한다.

C) HTML 원문을 그대로 `metadata.raw_html`에 저장한다.

X) 기타

[Answer]: A

### Question 4. Media And Download Boundary

이미지, DC 동영상, YouTube, inline video, 디시콘의 파일/URL 처리는 어디까지 UOW-004에서 담당할까요?

A) (권장) UOW-004는 URL, 썸네일, 설명, alt/title, media type 같은 metadata와 content block만 만들고 파일 다운로드/저장은 UOW-006 media storage로 미룬다. 단, DC 동영상 iframe처럼 추가 HTML fetch가 필요한 metadata 추출은 UOW-004에서 수행한다.

추천 사유: UOW-006이 아직 구현되지 않았으므로 파일 쓰기까지 넣으면 순서가 꼬입니다. URL/metadata만 있어도 후속 저장 unit이 다운로드를 처리할 수 있습니다.

B) UOW-004가 모든 이미지/동영상/디시콘 파일을 로컬에 직접 다운로드한다.

C) UOW-004는 미디어를 모두 무시하고 텍스트만 파싱한다.

X) 기타

[Answer]: A

### Question 5. Repost `(펌)` Parsing

`(펌)` 게시글은 어떻게 파싱할까요?

A) (권장) `h3.title > b.font_blue009` 또는 `.write_div script`의 `/ajax/pum_ajax/get_contents` 호출로 `is_repost`를 판단하고, AJAX 응답을 직접 요청해 `RepostInfo`와 원글 카드의 content block/media metadata를 파싱한다. JSON 저장용 제목에서는 `(펌)`을 제거하고, 원글 댓글 수는 저장하지 않는다.

추천 사유: BeautifulSoup/httpx 환경에서는 JavaScript가 실행되지 않으므로 AJAX 응답을 직접 파싱해야 실제 원글 카드 데이터를 얻을 수 있습니다.

B) 렌더링된 `#pum_container`가 HTML에 있을 때만 파싱하고 AJAX는 호출하지 않는다.

C) `(펌)`은 제목 문자열만 정리하고 원글 정보는 저장하지 않는다.

X) 기타

[Answer]: A

### Question 6. Comment And Reply Source

댓글/덧글은 어떤 소스를 기본으로 파싱할까요?

A) (권장) `/board/comment/` AJAX JSON을 기본 소스로 사용하고, `depth == 0`은 댓글, `depth == 1`은 덧글로 변환한다. HTML 렌더링 구조(`li[id^="comment_li_"]`, 다음 형제 `ul.reply_list[p-no]`)는 fixture/보조 fallback parser로 둔다.

추천 사유: 댓글은 상세 HTML에 고정 포함되지 않습니다. JSON을 기본으로 두면 덧글 parent 관계와 페이지 처리가 더 안정적입니다.

B) 상세 HTML에 렌더링된 댓글 DOM만 파싱한다.

C) 댓글은 UOW-004에서 제외하고 후속 unit으로 미룬다.

X) 기타

[Answer]: A

### Question 7. Comment Memo And Dccon Parsing

댓글 `memo`와 디시콘은 어떻게 저장할까요?

A) (권장) `memo`가 일반 텍스트이면 `memo_text`로 저장하고, HTML 또는 디시콘이 포함되면 BeautifulSoup으로 한 번 더 파싱해 텍스트와 `DcconItem` 목록을 분리한다. `img.written_dccon`과 `video.written_dccon`의 src/data-src/source/alt/title/conalt metadata만 저장한다.

추천 사유: 댓글 본문과 디시콘 metadata를 분리해야 후속 다운로드/분석 단계가 단순합니다.

B) `memo` HTML 문자열을 그대로 저장한다.

C) 디시콘이 포함된 댓글은 텍스트 없이 dccon URL만 저장한다.

X) 기타

[Answer]: A

### Question 8. Partial Failure Handling

상세 수집 중 일부 하위 요청이 실패하면 어떻게 처리할까요?

A) (권장) 필수 상세 HTML fetch/핵심 메타데이터 파싱 실패는 typed error로 실패 처리한다. 댓글, `(펌)` AJAX, DC video iframe 같은 하위 fetch/parse 실패는 `PostResult.metadata["detail_failures"]`에 safe reason만 기록하고 가능한 `PostResult`를 반환한다. CAPTCHA/block은 UOW-002 예외를 그대로 전파한다.

추천 사유: 게시글 본문은 살릴 수 있는 경우가 많습니다. 다만 CAPTCHA/block은 checkpoint 중단을 위해 삼키면 안 됩니다.

B) 댓글이나 미디어 하나라도 실패하면 전체 게시글을 실패 처리한다.

C) 모든 실패를 무시하고 실패 metadata를 남기지 않는다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-004 Functional Design 산출물 3개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-004 NFR Requirements로 넘어가지 않습니다.
