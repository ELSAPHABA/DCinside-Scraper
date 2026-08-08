# NFR Design 계획 - UOW-007 CLI Adapter

이 계획은 `UOW-007 CLI Adapter`의 NFR 요구사항을 구현 패턴과 논리 컴포넌트로 구체화하기 위한 질문지입니다.

답변 방법: 모든 `[Answer]:` 항목을 채워 주세요. 선택지는 하나를 고르거나, `X)`로 구체적인 방식을 적어도 됩니다.

## Unit Context

- **Unit**: UOW-007 CLI Adapter
- **NFR Requirements**: 승인됨
- **Depends On**: UOW-001 Core Models And Config, UOW-002 HTTP Runtime Policy, UOW-003 Search And Link Collection, UOW-004 Post Detail And Content Parsing, UOW-005 Job Runner And Checkpoint, UOW-006 Output And Storage
- **Scope**: stdlib command CLI, numbered wizard menu, model builder reuse, safe error/traceback output, Proxy `.env` update, User-Agent import, Ctrl+C stop hook, adapter tests
- **Out Of Scope**: scraping/parsing logic, HTTP retry internals, worker scheduling, storage layout internals, Docker entrypoint, MCP adapter, GUI/Web UI, external TUI dependency

## NFR Design 작업 체크리스트

- [x] UOW-007 NFR Requirements 승인 확인
- [x] NFR Requirements 산출물 확인
- [x] NFR Design 질문 생성
- [x] NFR Design 질문 답변 완료 확인
- [x] 답변의 모호함 또는 충돌 여부 분석
- [x] follow-up 질문 필요 여부 확인
- [x] `aidlc-docs/construction/uow-007-cli-adapter/nfr-design/nfr-design-patterns.md` 생성
- [x] `aidlc-docs/construction/uow-007-cli-adapter/nfr-design/logical-components.md` 생성
- [x] Security/Resiliency/PBT compliance 확인

## NFR Design Questions

### Question 1. CLI Module Layout

CLI 구현 파일은 어떻게 나눌까요?

A) (권장) 1차 구현은 `src/dcinside_scraper/adapters/cli.py` 한 파일에 `main`, parser builder, model builders, wizard handler, file helpers를 둔다. 테스트가 커질 때만 후속으로 분리한다.

추천 사유: UOW-007은 adapter 하나입니다. 지금부터 패키지를 여러 파일로 쪼개면 이동 비용만 생깁니다.

B) `adapters/cli/` 패키지를 만들고 parser, wizard, reporter, files, runtime을 모두 별도 파일로 나눈다.

C) `main.py` 루트 스크립트에 전부 넣는다.

X) 기타

[Answer]: A

### Question 2. Internal Command Shape

명령형 CLI와 wizard의 입력을 어떤 내부 형태로 맞출까요?

A) (권장) `argparse.Namespace`와 wizard 답변 dict를 작은 표준 dict로 정규화한 뒤, 같은 `build_job_config(command)`/`build_resume_request(command)` 함수에 넘긴다.

추천 사유: 별도 클래스 없이도 command/wizard builder 재사용을 달성할 수 있습니다.

B) command마다 dataclass를 새로 만든다.

C) wizard가 `argparse.Namespace`를 직접 만들어 위장한다.

X) 기타

[Answer]: A

### Question 3. Wizard Implementation Pattern

마법사 메뉴 구현 패턴은 어떻게 둘까요?

A) (권장) `WizardSession(input_stream, output_stream)` 같은 작은 helper가 prompt/read/print만 담당하고, 선택 결과는 내부 command dict로 반환한다. 상태 머신/프레임워크는 만들지 않는다.

추천 사유: 테스트 주입이 가능하고, 번호 입력식 메뉴 요구만 충족합니다.

B) 전역 `input()`/`print()`를 직접 흩뿌려 구현한다.

C) prompt-toolkit/Rich 기반 TUI 클래스를 만든다.

X) 기타

[Answer]: A

### Question 4. Safe Error Reporter Pattern

safe summary와 traceback 출력은 어떤 컴포넌트가 담당할까요?

A) (권장) `print_error(exc, *, stage, output, include_traceback=True)` 함수가 `ErrorMapper.map()` 결과를 먼저 출력하고, `traceback.format_exception()`을 이어 출력한다. locals/config dump는 구현하지 않는다.

추천 사유: 함수 하나로 충분하고, Q9 traceback 요구와 redaction 경계를 동시에 유지할 수 있습니다.

B) 모든 command handler가 직접 `traceback.print_exc()`를 호출한다.

C) traceback은 전역 exception hook에 맡긴다.

X) 기타

[Answer]: A

### Question 5. `.env` Update Pattern

Proxy `.env` 갱신은 어떤 방식으로 구현할까요?

A) (권장) `update_proxy_env(path, values)` 순수 파일 helper가 기존 줄을 읽고 `DCINSIDE_PROXY_*` 키만 교체/추가한 뒤 temp file + `os.replace`로 저장한다.

추천 사유: UOW-006과 같은 원자적 쓰기 패턴을 작게 재사용하면서 기존 `.env` 내용을 보존할 수 있습니다.

B) `.env` 전체를 세 줄로 덮어쓴다.

C) `python-dotenv`의 set_key를 사용한다.

X) 기타

[Answer]: A

### Question 6. User-Agent Import Pattern

User-Agent 파일 import는 어떤 방식으로 구현할까요?

A) (권장) `import_user_agents(source, destination)` helper가 regular file/UTF-8/nonblank 검사를 수행한 뒤 temp file + `os.replace`로 `user-agents.txt`를 교체한다.

추천 사유: 기존 destination을 빈/깨진 파일로 덮어쓰지 않으면서 표준 라이브러리만 사용합니다.

B) `shutil.copyfile`로 바로 덮어쓴다.

C) User-Agent 문자열 문법을 모두 파싱한 뒤 저장한다.

X) 기타

[Answer]: A

### Question 7. Ctrl+C Hook Pattern

Ctrl+C graceful stop은 어떻게 연결할까요?

A) (권장) running command가 `JobRunner` 인스턴스를 만들고, signal/KeyboardInterrupt handler가 첫 interrupt에서 `runner.request_stop()`을 호출한다. 두 번째 interrupt는 best-effort close 후 exit code `1`로 끝낸다.

추천 사유: 이미 UOW-005에 manual stop API가 있으므로 adapter는 연결만 하면 됩니다.

B) Ctrl+C는 기본 `KeyboardInterrupt` traceback에 맡긴다.

C) Ctrl+C를 무시하고 runner가 끝날 때까지 기다린다.

X) 기타

[Answer]: A

### Question 8. Runtime Factory Pattern

CLI의 runtime dependency assembly는 어떤 패턴으로 둘까요?

A) (권장) `build_local_runtime(config, runtime_options)` 함수 또는 context helper가 `HttpClient`, `LinkCollectorService`, `PostDetailService`, `LocalOutputStore`, `LocalCheckpointStore`를 생성한다. 별도 factory class는 만들지 않는다.

추천 사유: 의존성 조립은 한 번 쓰는 adapter 코드입니다. 클래스보다 함수가 작고 테스트하기 쉽습니다.

B) `LocalRuntimeFactory` 클래스를 만들어 모든 생성 책임을 넣는다.

C) command handler마다 직접 모든 객체를 만든다.

X) 기타

[Answer]: A

### Question 9. Test Organization

UOW-007 테스트 파일은 어떻게 구성할까요?

A) (권장) 예제 테스트는 `tests/test_cli_adapter.py`, PBT는 `tests/test_cli_properties.py`, strategy는 `tests/strategies/cli.py`에 둔다. 테스트는 helper/fake runner 중심으로 실행한다.

추천 사유: 기존 UOW 테스트 구조와 맞고, CLI adapter 범위가 한 곳에 모입니다.

B) 모든 테스트를 `tests/test_cli.py` 하나에 넣는다.

C) wizard 테스트와 command 테스트를 완전히 별도 디렉터리로 나눈다.

X) 기타

[Answer]: A

### Question 10. Console Script And Compatibility

실행 진입점 호환성은 어디까지 둘까요?

A) (권장) `pyproject.toml`에 console script를 추가하고, 문서상 실행은 `python -m dcinside_scraper.adapters.cli ...`와 console script 둘 다 허용한다. 루트 `main.py`는 만들지 않는다.

추천 사유: 패키지형 실행과 설치 후 실행을 모두 지원하면서 루트 스크립트 중복은 피합니다.

B) 루트 `main.py`도 만들어 `python main.py`를 공식 지원한다.

C) console script만 지원하고 `python -m` 실행은 지원하지 않는다.

X) 기타

[Answer]: A + B

## 답변 후 진행 방식

답변이 모두 채워지면 다음을 수행합니다.

1. 답변의 모호함과 충돌 여부를 검토합니다.
2. 모호한 답변이 있으면 follow-up 질문을 추가합니다.
3. 답변이 명확하면 UOW-007 NFR Design 산출물 2개를 생성합니다.
4. 산출물 생성 후 사용자 승인 전에는 Infrastructure Design 또는 Code Generation으로 넘어가지 않습니다.

## 검토 결과

- Q1-Q9는 A로 확정되었습니다.
- Q10은 A + B로 확정되어 console script, `python -m`, 얇은 루트 `main.py` wrapper를 모두 허용합니다.
- 답변 간 충돌은 없습니다. 루트 `main.py`는 중복 구현 없이 `dcinside_scraper.adapters.cli.main`만 호출하는 compatibility wrapper로 제한합니다.
- follow-up 질문은 필요하지 않습니다.
- 산출물 생성 후 UOW-007 NFR Design Review 단계에서 사용자 승인을 대기합니다.
