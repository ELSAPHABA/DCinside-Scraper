# Unit Of Work Story Map

## Story To Unit Mapping

| Story | Title | Primary Unit | Supporting Units |
|---|---|---|---|
| US-001 | CLI에서 수집 Job을 생성한다 | UOW-007 | UOW-001, UOW-005 |
| US-002 | User-Agent와 Proxy 설정을 불러온다 | UOW-002 | UOW-007, UOW-008 |
| US-003 | 요청 속도와 worker 수를 조절한다 | UOW-002 | UOW-005, UOW-007 |
| US-004 | 갤러리 내 검색 결과에서 링크를 수집한다 | UOW-003 | UOW-002 |
| US-005 | 통합 검색 결과에서 링크를 수집한다 | UOW-003 | UOW-002 |
| US-006 | 수집 범위와 중복 제거를 적용한다 | UOW-003 | UOW-005 |
| US-006A | 노키워드와 실시간 수집 옵션을 실행한다 | UOW-003 | UOW-005, UOW-007, UOW-008 |
| US-006B | 심층검색으로 여러 갤러리의 키워드 게시글을 수집한다 | UOW-003 | UOW-005 |
| US-007 | 게시글 메타데이터와 본문을 수집한다 | UOW-004 | UOW-002 |
| US-008 | 게시글 이미지 URL과 파일을 처리한다 | UOW-004 | UOW-006, UOW-002 |
| US-009 | `(펌)` 게시글을 일반 게시글과 같은 결과 구조로 수집한다 | UOW-004 | UOW-002 |
| US-010 | 댓글과 덧글을 계층 구조로 수집한다 | UOW-004 | UOW-002 |
| US-011 | 디시콘 URL과 파일을 처리한다 | UOW-004 | UOW-006, UOW-002 |
| US-012 | Job별 JSONL 결과를 저장한다 | UOW-006 | UOW-001, UOW-008 |
| US-013 | 수집 결과 품질을 검토한다 | UOW-008 | UOW-006 |
| US-014 | CAPTCHA 또는 차단 감지 시 중단점을 저장하고 멈춘다 | UOW-005 | UOW-002, UOW-006 |
| US-015 | 사용자가 중단한 Job을 재개한다 | UOW-005 | UOW-006, UOW-007, UOW-008 |
| US-016 | 실패한 게시글 요청을 재시도하고 실패 기록을 남긴다 | UOW-002 | UOW-005, UOW-006 |
| US-017 | Python 라이브러리 API를 제공한다 | UOW-001 | UOW-005, UOW-007 |
| US-018 | 워커 컨테이너 모드를 제공한다 | UOW-008 | UOW-005, UOW-006 |
| US-019 | MCP tool 인터페이스를 제공한다 | UOW-008 | UOW-001, UOW-005 |

## Unit Story Load

| Unit | Primary Stories |
|---|---|
| UOW-001 Core Models And Config | US-017 |
| UOW-002 HTTP Runtime Policy | US-002, US-003, US-016 |
| UOW-003 Search And Link Collection | US-004, US-005, US-006, US-006A, US-006B |
| UOW-004 Post Detail And Content Parsing | US-007, US-008, US-009, US-010, US-011 |
| UOW-005 Job Runner And Checkpoint | US-014, US-015 |
| UOW-006 Output And Storage | US-012 |
| UOW-007 CLI Adapter | US-001 |
| UOW-008 Container, MCP, And Test Harness | US-013, US-018, US-019 |

## Coverage Check

All user stories are assigned to at least one primary unit:

- US-001
- US-002
- US-003
- US-004
- US-005
- US-006
- US-006A
- US-006B
- US-007
- US-008
- US-009
- US-010
- US-011
- US-012
- US-013
- US-014
- US-015
- US-016
- US-017
- US-018
- US-019

## Functional Design Implications

- UOW-003 needs Functional Design for search URL construction, pagination, `search_pos`, deep search, no-keyword range, realtime polling, and dedupe rules.
- UOW-004 needs Functional Design for selectors, `(펌)` AJAX parsing, comments/replies, content blocks, media extraction, and DC video description.
- UOW-005 needs Functional Design for Job lifecycle, checkpoint ordering, resume semantics, stop reasons, and worker queue behavior.
- UOW-006 needs Functional Design for JSONL write semantics, resume output naming, S3-compatible upload behavior, and failure report structure.
- UOW-008 needs NFR and Infrastructure Design input before final container runtime and MCP packaging.

