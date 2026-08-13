# Requirement Verification Questions

`docs\Function_Specification.md`를 기준으로 디시인사이드 스크래퍼 구현 전에 필요한 결정만 정리한 질문지입니다.

각 질문의 `[Answer]:` 뒤에 선택지 문자만 적어 주세요. 선택지가 맞지 않으면 마지막 `X) 기타`를 고르고 같은 줄이나 다음 줄에 설명을 적어 주세요.

## Question 1
첫 번째 구현 목표는 어디까지로 잡을까요?

A) CLI + Python 라이브러리 import 가능한 핵심 스크래퍼

B) CLI + Python 라이브러리 + 검색 기반 멀티 워커 수집

C) CLI + Python 라이브러리 + 멀티 워커 + 워커 컨테이너 + MCP 도구

X) 기타 (please describe after [Answer]: tag below)

[Answer]: C

## Question 2
가장 중요한 사용 시나리오는 무엇인가요?

A) 특정 갤러리 또는 검색어의 게시글/댓글을 일회성으로 수집

B) 특정 갤러리 또는 검색어를 주기적으로 추적하며 새 글만 수집

C) 통합 커뮤니티 스크래핑 시스템의 디시인사이드 워커로 사용

D) 다른 Python 코드나 에이전트가 호출하는 라이브러리/MCP 도구로 사용

X) 기타 (please describe after [Answer]: tag below)

[Answer]: C

## Question 3
1차 구현에 포함할 수집 진입점은 무엇인가요?

A) 게시글 URL 직접 입력 수집

B) 갤러리 내 검색 결과 기반 수집

C) 통합 검색 결과 기반 수집

D) 게시글 URL 직접 입력 + 갤러리 내 검색 + 통합 검색 모두

X) 기타 (please describe after [Answer]: tag below)

[Answer]: D

[Superseded/Delta 2026-08-05]: 최신 범위는 노키워드 기간/글번호 범위 수집, 심층검색, 실시간 키워드 수집, 실시간 전체 수집을 추가로 포함합니다. 자세한 최신 결정은 `specification-reconciliation.md`와 `requirements.md` FR-029~FR-031을 따릅니다.

## Question 4
HTTP 요청 구현 방식은 어떻게 할까요?

A) `requests` 동기 요청으로 먼저 구현

B) `requests` + `concurrent.futures.ThreadPoolExecutor`로 병렬화

C) `httpx` + `asyncio`로 비동기 멀티 워커 구현

X) 기타 (please describe after [Answer]: tag below)

[Answer]: C

## Question 5
게시글 상세 수집에서 1차 필수 데이터는 어디까지인가요?

A) 제목, 작성자, 작성일, 조회수, 추천/비추천, 본문 텍스트

B) A + 본문 이미지 URL

C) B + 이미지 파일 다운로드

D) C + 첨부 파일 다운로드

X) 기타 (please describe after [Answer]: tag below)

[Answer]: B

## Question 6
댓글과 덧글 수집은 1차 구현에 포함할까요?

A) 포함한다. 게시글 수집 시 댓글/덧글을 기본으로 함께 수집

B) 포함한다. 단, 옵션을 켰을 때만 댓글/덧글 수집

C) 1차 구현에서는 제외하고 게시글 본문 수집을 먼저 완성

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A

## Question 7
디시콘 수집 방식은 어떻게 할까요?

A) `memo` 원문 HTML만 저장

B) 디시콘 이미지/영상 URL과 alt/title/conalt 메타데이터만 저장

C) 디시콘 파일까지 다운로드

X) 기타 (please describe after [Answer]: tag below)

[Answer]: Job 실행 전 터미널에서 옵션값으로 선택하게 하고, 선택에 따라 디시콘 이미지/영상 URL과 alt/title/conalt 메타데이터만 저장만 저장하거나 디시콘 파일까지 다운로드하도록 구현

[Superseded/Delta 2026-08-13]: 현재 구현은 디시콘 URL/메타데이터 저장까지만 지원합니다. 디시콘 파일 다운로드는 댓글 하위 `DcconItem` 저장 경로와 media 실패 기록 정책을 별도 확정한 뒤 후속 확장으로 둡니다.

## Question 8
수집 결과 저장 방식은 무엇을 기본으로 할까요?

A) 작업 1회당 하나의 JSON 파일

B) 게시글 1개당 하나의 JSON 파일

C) JSON Lines 파일 하나에 게시글 단위로 append

D) MongoDB 저장까지 1차 구현에 포함

X) 기타 (please describe after [Answer]: tag below)

[Answer]: C

## Question 9
이미지 파일 저장 구조는 어떻게 할까요?

A) 저장하지 않고 URL만 수집

B) `images/<gallery_id>/<post_no>/` 아래에 저장

C) `images/<job_id>/<gallery_id>/<post_no>/` 아래에 저장

X) 기타 (please describe after [Answer]: tag below)

[Answer]: Job 실행 전 터미널에서 옵션값으로 선택하게 하고, 선택에 따라 URL만 저장하거나 `images/<gallery_id>/<post_no>/` 아래에 저장하도록 구현

## Question 10
중단점 저장은 어느 수준으로 할까요?

A) 게시글 1개 처리 완료마다 `Checkpoint.json` 저장

B) 검색 결과 페이지 또는 댓글 페이지 처리 완료마다 저장

C) 작업 중단, 오류, CAPTCHA 감지 시에만 저장

X) 기타 (please describe after [Answer]: tag below)

[Answer]: C, 특히 작업 중단시 무조건 최종으로 `Checkpoint.json`을 저장하고 프로세스를 중단하도록 구현.

[Superseded/Delta 2026-08-05]: 최신 checkpoint 정책은 게시글 10개 저장마다 저장하고, 수동 중단/오류/CAPTCHA 감지 시 즉시 최종 checkpoint를 저장하는 방식입니다.

## Question 11
CAPTCHA 또는 차단 의심 응답을 감지했을 때 동작은 어떻게 할까요?

A) 즉시 중단하고 `Checkpoint.json` 저장

B) 즉시 중단하고 `Checkpoint.json` 저장 후 터미널에 재개 명령 안내

C) 즉시 중단하고 `Checkpoint.json` 저장 후 사용자 브라우저로 해당 URL 열기

X) 기타 (please describe after [Answer]: tag below)

[Answer]: B

## Question 12
스크래핑 속도 조절 기본값은 어떻게 둘까요?

A) 전역 요청 간격 1초

B) 전역 요청 간격 2초

C) 요청 유형별 설정: 목록/검색 1초, 게시글 1초, 댓글 1.5초, 이미지 0.5초

D) 사용자가 설정하지 않으면 제한 없음

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A, 나중에 옵션에서 전역 요청 간격을 조절할 수 있도록 구현

## Question 13
User-Agent Mixer의 기본 동작은 어떻게 할까요?

A) `User-Agent.txt`가 있으면 사용하고 없으면 기본 User-Agent 하나만 사용

B) 첫 실행 시 터미널에서 파일 탐색기로 목록 파일을 선택하게 함

C) 실행할 때마다 목록 파일 선택 여부를 물어봄

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A, 단, 옵션 설정에서 `파일 탐색기`를 열어 `User-Agent.txt`를 불러와 프로그램 파일의 같은 폴더에 저장하도록 구현. 이후 실행 시에는 `User-Agent.txt`가 있으면 자동으로 사용하고 없으면 기본 User-Agent 하나만 사용하도록 구현

[Superseded/Delta 2026-08-05]: 최신 파일명은 `user-agents.txt`입니다. 한 줄에 하나의 User-Agent를 저장하고, 빈 줄은 무시하며, 기본 교체 주기는 요청 10회마다 1회입니다. 교체 주기는 터미널 옵션으로 변경할 수 있고 컨테이너 이미지에는 txt 파일을 포함합니다.

## Question 14
Proxy 설정의 기본 동작은 어떻게 할까요?

A) 기본 비활성화, 사용자가 옵션을 켰을 때만 터미널에서 host/ID/PW 입력

B) 첫 실행 시 항상 Proxy 설정 여부를 물어봄

C) `Proxy-Profile.txt`가 있을 때만 자동 사용

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A, 단, 옵션 설정에서 `파일 탐색기`를 열어 `Proxy-Profile.txt`를 불러와 프로그램 파일의 같은 폴더에 저장하도록 구현. 이후 실행 시에는 `Proxy-Profile.txt`가 있으면 자동으로 사용하고 없으면 기본 Proxy 설정을 사용하도록 구현

[Superseded/Delta 2026-08-05]: 최신 Proxy 저장 방식은 실행 파일과 같은 위치의 평문 `.env`입니다. 사용자가 Proxy 옵션을 켠 경우 우선 적용하고, 옵션이 없더라도 `.env`가 있으면 자동 사용합니다. 환경 변수명은 `DCINSIDE_PROXY_HOST`, `DCINSIDE_PROXY_ID`, `DCINSIDE_PROXY_PW`를 사용합니다.

## Question 15
검색 기반 멀티 워커 수집에서 중복 제거 기준은 무엇으로 할까요?

A) `(gallery_id, post_no)` 기준

B) 상세 URL 문자열 기준

C) `(gallery_id, post_no)` 기준으로 제거하고 URL도 보조로 저장

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A

## Question 16
작업 종료 조건은 무엇을 우선으로 할까요?

A) 최대 페이지 수

B) 글 번호 범위

C) 작성일 범위

D) 최대 수집 게시글 수

E) 위 조건들을 조합해서 먼저 도달한 조건으로 종료

X) 기타 (please describe after [Answer]: tag below)

[Answer]: B와 C를 조합해서 먼저 도달한 조건으로 종료하도록 구현.

## Question 17
Python 라이브러리 import API는 어느 정도로 노출할까요?

A) `search_gallery`, `search_integrated`, `fetch_post`, `fetch_comments` 정도의 함수만 노출

B) A + 설정 객체와 결과 dataclass까지 노출

C) 내부 모듈 전체를 패키지 API로 정리

X) 기타 (please describe after [Answer]: tag below)

[Answer]: B

## Question 18
워커 컨테이너와 MCP는 1차 구현에서 어떻게 다룰까요?

A) 명세와 구조만 남기고 구현은 제외

B) 핵심 스크래퍼 완성 후 얇은 어댑터만 추가

C) 1차 구현부터 컨테이너 실행과 MCP 도구까지 포함

X) 기타 (please describe after [Answer]: tag below)

[Answer]: C

## Question 19
테스트 기준은 어떻게 잡을까요?

A) 저장된 HTML fixture 기반 파싱 테스트

B) 실제 DCinside 페이지에 대한 수동 smoke test

C) fixture 테스트 + 선택적 live smoke test

X) 기타 (please describe after [Answer]: tag below)

[Answer]: B

## Question 20
수집 대상 범위 제한은 어떻게 둘까요?

A) 공개 게시글/댓글만 수집하고 로그인, 성인 인증, 삭제글 접근은 제외

B) 공개 게시글/댓글을 기본으로 하되, 사용자가 쿠키를 직접 제공한 경우만 인증 페이지 접근 허용

C) 가능한 모든 접근 방식을 지원

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A

## Question 21: Security Extensions
Security Baseline 확장 규칙을 이 프로젝트에 적용할까요?

A) 예. 프로덕션 수준 애플리케이션 기준의 SECURITY 규칙을 blocking constraint로 적용

B) 아니요. PoC/개인 도구 수준으로 보고 SECURITY 규칙은 생략

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A

## Question 22: Resiliency Extensions
Resiliency Baseline 확장 규칙을 이 프로젝트에 적용할까요?

A) 예. 장애 허용, 복구, 관측성 관련 설계 지침을 적용

B) 아니요. PoC/개인 도구 수준으로 보고 resiliency baseline은 생략

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A

## Question 23: Property-Based Testing Extension
Property-Based Testing 규칙을 이 프로젝트에 적용할까요?

A) 예. 파싱, 직렬화, 상태 처리에 PBT 규칙을 적용

B) 부분 적용. 순수 함수와 JSON 직렬화 round-trip에만 적용

C) 아니요. 일반 fixture 기반 테스트만 사용

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A
