# Functional Design 계획 - UOW-007 CLI Adapter

이 계획은 `UOW-007 CLI Adapter`의 기능 설계를 확정하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-007 CLI Adapter
- **Depends On**: UOW-001 Core Models And Config, UOW-002 HTTP Runtime Policy, UOW-003 Search And Link Collection, UOW-004 Post Detail And Content Parsing, UOW-005 Job Runner And Checkpoint, UOW-006 Output And Storage
- **Primary Stories**: US-001
- **Related Stories**: US-002, US-003, US-006A, US-014, US-015, US-017
- **Scope**: terminal CLI entrypoint, argument parsing, interactive wizard menu, `JobConfig`/`ResumeRequest` creation, local runtime dependency assembly, local output/checkpoint wiring, User-Agent import flow, Proxy `.env` flow, resume command, safe terminal messages
- **Out Of Scope**: scraper parsing logic, search traversal internals, worker queue internals, concrete HTML selectors, container entrypoint, PostgreSQL checkpoint adapter, Garage provisioning, MCP tools, GUI/Web UI

## Scope Change Notes

- 2026-08-08 변경: 대화형 마법사 메뉴는 UOW-007 1차 구현 범위에 포함한다.
- 마법사 메뉴는 `wizard` subcommand로 제공하고, 내부에서는 명령형 CLI와 같은 `JobConfig`/`ResumeRequest` builder 및 core API를 재사용한다.
- 별도 `python main.py` 루트 스크립트는 필수 범위로 두지 않는다.

## Functional Design 작업 체크리스트

- [x] UOW-005 Build and Test 승인 확인
- [x] UOW-007 범위 확인
- [x] UOW-001~UOW-006 계약 확인
- [x] Functional Design 질문 생성
- [x] Functional Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-007-cli-adapter/functional-design/business-logic-model.md` 생성
- [x] `aidlc-docs/construction/uow-007-cli-adapter/functional-design/business-rules.md` 생성
- [x] `aidlc-docs/construction/uow-007-cli-adapter/functional-design/domain-entities.md` 생성

## Functional Design Questions

### Question 1. CLI Entrypoint

CLI 진입점은 어디에 둘까요?

A) (권장) `dcinside_scraper.adapters.cli`에 `main(argv: list[str] | None = None) -> int`를 두고, `pyproject.toml` console script는 이 함수를 호출한다. import만으로 실행, 파일 생성, 네트워크 요청은 하지 않는다.

추천 사유: 기존 core import 안전성 요구사항을 지키면서도 테스트에서 `main([...])`을 바로 호출할 수 있습니다.

B) `src/dcinside_scraper/core/api.py`에 CLI parsing까지 넣는다.

C) 프로젝트 루트에 독립 실행 스크립트 하나만 둔다.

X) 기타

[Answer]: A

### Question 2. Command Shape

CLI 명령 구조는 어떻게 둘까요?

A) (권장) 표준 라이브러리 `argparse` 기반으로 `run`, `resume`, `import-user-agents`, `configure-proxy`, `wizard` subcommand를 둔다. `run`은 `--source direct-post|gallery-search|integrated-search|deep-search|no-keyword-range`를 받는다.

추천 사유: 새 CLI 의존성을 추가하지 않고, 실행/재개/설정 작업의 책임이 분리됩니다.

변경 참고: 번호 입력식 마법사 메뉴는 이번 UOW-007에 포함하되, 별도 scraping 로직 없이 같은 builder와 core API를 호출합니다.

B) subcommand 없이 하나의 명령에 모든 옵션을 flat하게 둔다.

C) 모든 입력을 대화형 prompt로만 받는다.

X) 기타

[Answer]: A

### Question 3. JobConfig Mapping

CLI 인자를 `JobConfig`로 바꾸는 로직은 어디에 둘까요?

A) (권장) `build_job_config(args) -> JobConfig`와 `build_resume_request(args) -> ResumeRequest` 같은 순수 변환 함수를 두고, Pydantic validation 오류를 CLI가 안전한 메시지로 출력한다.

추천 사유: validation은 이미 UOW-001 모델이 담당합니다. CLI는 dict 조립과 메시지 변환만 하면 됩니다.

B) `main()` 안에서 raw dict를 만들고 바로 runner에 넘긴다.

C) `JobRunner`가 `argparse.Namespace`를 직접 해석하게 한다.

X) 기타

[Answer]: A

### Question 4. Realtime Env Flow

실시간 수집 옵션은 CLI에서 어떻게 다룰까요?

A) (권장) 확정 요구사항대로 `DCINSIDE_REALTIME_*` 환경변수를 읽어 `RealtimeKeywordSource` 또는 `RealtimeAllSource`를 만든다. `DCINSIDE_REALTIME_DURATION_SECONDS`와 `DCINSIDE_REALTIME_END_AT`은 정확히 하나만 허용하고, 일반 `run --source ...`와 충돌하면 validation 오류로 중단한다.

추천 사유: 실시간 수집은 이미 환경변수 기반으로 문서화되어 있습니다. CLI 전용 플래그를 또 만들면 같은 기능의 입력 경로가 늘어납니다.

B) 실시간 수집도 `run --source realtime-keyword|realtime-all` 플래그로만 받는다.

C) 실시간 수집은 UOW-008 container 전용으로 미루고 CLI에서는 지원하지 않는다.

X) 기타

[Answer]: A

### Question 5. Runtime Assembly

CLI는 코어 실행 의존성을 어디까지 직접 조립할까요?

A) (권장) CLI가 `HttpClient`, `LinkCollectorService`, `PostDetailService`, `LocalOutputStore`, `LocalCheckpointStore`를 생성하고 `core.api.run_job()` 또는 `core.api.resume_job()`에 주입한다. scraping 로직은 CLI에 넣지 않는다.

추천 사유: UOW-007은 adapter입니다. 이미 구현된 core/service/storage를 연결하는 선에서 끝내는 것이 가장 작습니다.

B) CLI가 검색, 게시글 수집, 저장 순서를 직접 실행한다.

C) CLI는 config 파일만 생성하고 실행은 하지 않는다.

X) 기타

[Answer]: A

### Question 6. Output And Checkpoint Location

로컬 실행의 출력 경로와 checkpoint 경로는 어떻게 정할까요?

A) (권장) `--output-path`를 `StorageConfig.base_output_path`에 매핑하고, 생략하면 현재 작업 디렉터리를 사용한다. `Checkpoint.json`과 `outputs/<job_id>/<run_id>/...` 레이아웃은 UOW-006 `OutputRunLayout` 규칙을 그대로 따른다.

추천 사유: 저장소 레이아웃은 이미 UOW-006에서 확정됐습니다. CLI가 파일 경로 규칙을 다시 구현할 필요가 없습니다.

B) 항상 실행 파일이 있는 디렉터리에 저장한다.

C) 항상 사용자 홈 디렉터리에 저장한다.

X) 기타

[Answer]: A

### Question 7. User-Agent And Proxy Setup

User-Agent 파일과 Proxy 설정 flow는 어떻게 둘까요?

A) (권장) `--user-agent-file`, `--user-agent-rotate-every`는 현재 실행에 적용하고, `import-user-agents`는 선택한 파일을 실행 기준 디렉터리의 `user-agents.txt`로 복사한다. `configure-proxy`는 host, ID, PW를 입력받아 평문 `.env`에 저장하되, 저장 전 보안 경고를 출력한다. 실행 시 Proxy는 명시 옵션, `.env`, 비활성 순서로 적용한다.

추천 사유: UOW-002의 `UserAgentConfig`, `ProxyConfig`, `.env` 우선순위를 그대로 사용하면서 사용자가 요청한 평문 파일 편집 가능성도 유지합니다.

B) CLI에서는 User-Agent/Proxy 설정을 다루지 않고 파일이 있으면 자동 사용만 한다.

C) 매 실행마다 Proxy와 User-Agent 경로를 모두 prompt로 묻는다.

X) 기타

[Answer]: A

### Question 8. Scrape Options

이미지, 디시콘, 댓글, 요청 간격, worker 수 같은 실행 옵션은 어떤 CLI 옵션으로 둘까요?

A) (권장) `--image-mode`, `--dccon-mode`, `--include-comments/--no-comments`, `--request-interval-seconds`, `--post-worker-count`, `--media-worker-count`, `--queue-max-size`, `--max-comment-pages`를 두고 기존 `ScrapeOptions`/`WorkerConfig`에 매핑한다.

추천 사유: 이미 모델 필드가 있으므로 CLI 옵션명만 얇게 붙이면 됩니다.

B) 우선 기본값만 사용하고 CLI 옵션은 후속 unit으로 미룬다.

C) 옵션 파일로만 받는다.

X) 기타

[Answer]: A

### Question 9. Terminal Output And Exit Codes

터미널 출력과 종료 코드는 어떻게 정할까요?

A) (권장) 시작 시 `job_id`, output path, source summary, worker count, request interval을 출력하고, 종료 시 report summary와 resume command를 출력한다. 성공은 exit code `0`, validation 오류는 `2`, 수집 중단/CAPTCHA/실행 오류는 `1`로 둔다. Proxy password, raw `.env`, cookie, raw HTML은 출력하지 않는다.

추천 사유: 사람이 읽을 정보는 충분하고, shell script에서 실패를 구분할 수 있습니다.

B) 전체 config와 exception traceback을 항상 출력한다.

C) 기본 출력은 없고 파일 report만 남긴다.

X) 기타

[Answer]: A, exception traceback도 같이 출력한다.

### Question 10. Test Scope

UOW-007 기본 테스트 범위는 어디까지 둘까요?

A) (권장) live network 없이 `argparse` parsing, `build_job_config`, `build_resume_request`, realtime env validation, User-Agent import copy, Proxy `.env` writer redaction, import side-effect 없음, fake runner 호출을 단위 테스트한다.

추천 사유: CLI adapter는 입력 변환과 의존성 주입이 핵심입니다. 실제 DCinside 접속은 이미 다른 unit의 선택적 smoke test가 담당합니다.

B) 실제 DCinside 페이지를 호출하는 CLI 통합 테스트를 기본 테스트로 둔다.

C) CLI는 수동 테스트만 하고 자동 테스트는 UOW-008로 미룬다.

X) 기타

[Answer]: A

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-007 Functional Design 산출물 3개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 UOW-007 NFR Requirements로 넘어가지 않습니다.
