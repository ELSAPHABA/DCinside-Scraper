# DCinside-Scraper 배포/운영 가이드

이 문서는 DCinside-Scraper를 로컬 프로그램, 컨테이너 워커, MCP 서버, 라이브러리 구성요소로 배포하고 운영하는 방법을 설명합니다. 처음 운영하는 사람이 실행, 설정, 중단, 재개, 장애 대응, 백업까지 빠짐없이 수행할 수 있도록 실제 코드 기준의 절차를 정리합니다.

## 운영 원칙

- 기본 실행 단위는 하나의 Job입니다. 하나의 CLI 실행 또는 하나의 컨테이너 프로세스가 하나의 Job을 실행합니다.
- 수집 구조는 링크 수집기 1개와 게시글 상세 수집 워커 N개입니다.
- 큐에는 Job이 아니라 게시글 후보 링크가 들어갑니다.
- 로컬 실행은 파일 저장소와 `Checkpoint.json`을 사용합니다.
- 컨테이너 실행은 S3 호환 저장소와 PostgreSQL 체크포인트 저장소를 사용합니다.
- CAPTCHA 또는 차단이 감지되면 자동 우회하지 않고 작업을 중단합니다.
- User-Agent 교체, Proxy, 요청 간격 조절은 안정성 보조 기능입니다. 차단 회피를 보장하지 않습니다.
- 과도한 요청은 서비스에 부담을 줄 수 있습니다. 워커 수와 요청 간격은 보수적으로 시작하세요.

## 배포 형태

| 배포 형태 | 용도 | 저장소 | 체크포인트 | 권장 상황 |
| --- | --- | --- | --- | --- |
| 로컬 CLI | 개발, 수동 수집, 기능 검증 | 로컬 `outputs/` | 로컬 `Checkpoint.json` | 단일 PC에서 직접 실행 |
| 컨테이너 워커 | 운영 수집, 반복 실행, 서버 배포 | S3 호환 저장소 | PostgreSQL | 장시간 운영, 여러 워커 관리 |
| MCP 서버 | 외부 에이전트 또는 도구에서 호출 | 호출자가 구성 | 호출자가 구성 | MCP 클라이언트와 연동 |
| 라이브러리 import | 다른 Python 앱에 내장 | 호출자가 구성 | 호출자가 구성 | 통합 커뮤니티 플랫폼에 편입 |

운영 배포의 기본 권장 구성은 컨테이너 워커 + Garage + PostgreSQL입니다. 저장소 컨테이너와 스크래퍼 컨테이너를 하나의 Compose 파일에 강하게 묶기보다는, Garage/PostgreSQL을 공유 인프라로 운영하고 각 커뮤니티 스크래퍼 워커가 환경 변수로 접속하는 구성이 향후 확장에 유리합니다.

여러 커뮤니티 스크래퍼가 같은 S3 호환 저장소와 PostgreSQL을 공유할 때는 `docs/Shared_Storage_Contract.md`의 namespace, object key, checkpoint key 규약을 우선합니다.

## 사전 요구사항

### 공통

- Python 3.11 이상
- 디시인사이드에 접근 가능한 네트워크
- UTF-8 터미널 환경 권장
- 프로젝트 루트에서 실행

### 로컬 CLI

- `python -m pip install -e .`
- 테스트가 필요하면 `python -m pip install -e ".[test]"`
- Polars 분석까지 하려면 `python -m pip install -e ".[analysis]"`

### 컨테이너 워커

- Docker
- S3 호환 저장소. 기본 권장 대상은 Garage입니다.
- PostgreSQL
- 컨테이너 이미지 빌드 또는 배포 파이프라인

### MCP 서버

- `python -m pip install -e ".[mcp]"`
- MCP 클라이언트 또는 에이전트 런타임

## 설치와 빌드

### 로컬 설치

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
```

설치 확인:

```powershell
dcinside-scraper --help
python -m dcinside_scraper.adapters.cli --help
python main.py --help
```

정상이라면 `run`, `resume`, `import-user-agents`, `configure-proxy`, `wizard` 명령이 표시됩니다.

### 컨테이너 이미지 빌드

```powershell
docker build -t dcinside-scraper-worker .
```

현재 Dockerfile은 아래 흐름으로 이미지를 만듭니다.

1. `python:3.11-slim` 사용
2. `/app`을 작업 디렉터리로 설정
3. `pyproject.toml`, `README.md`, `src/` 복사
4. `pip install --no-cache-dir ".[s3,postgres]"` 실행
5. `python -m dcinside_scraper.adapters.container`를 ENTRYPOINT로 설정

컨테이너에는 S3와 PostgreSQL extra가 포함됩니다. MCP extra는 컨테이너 기본 이미지에 포함되지 않습니다.

## 로컬 CLI 운영

### 기본 실행

게시글 하나 수집:

```powershell
dcinside-scraper run `
  --source direct-post `
  --url "https://gall.dcinside.com/board/view/?id=dcbest&no=442937"
```

여러 게시글 수집:

```powershell
dcinside-scraper run `
  --source direct-post `
  --url "https://gall.dcinside.com/board/view/?id=dcbest&no=442937" `
  --url "https://gall.dcinside.com/mgallery/board/view/?id=stockus&no=17025357"
```

갤러리 키워드 검색:

```powershell
dcinside-scraper run `
  --source gallery-search `
  --gallery-type minor `
  --gallery-id "singlebungle1472" `
  --s-type "search_subject_memo" `
  --keyword "싱글벙글" `
  --page 1
```

통합 검색:

```powershell
dcinside-scraper run `
  --source integrated-search `
  --keyword "싱글벙글" `
  --sort-mode relevance `
  --page-start 1 `
  --page-end 10
```

심층 검색:

```powershell
dcinside-scraper run `
  --source deep-search `
  --keyword "싱글벙글" `
  --seed-sort-mode relevance `
  --date-from "2026-08-01" `
  --date-to "2026-08-09"
```

노키워드 범위 수집:

```powershell
dcinside-scraper run `
  --source no-keyword-range `
  --gallery-type minor `
  --gallery-id "singlebungle1472" `
  --date-from "2026-08-01" `
  --date-to "2026-08-09"
```

### 로컬 출력 경로

기본 출력은 실행 위치의 `outputs/` 아래에 생성됩니다.

```text
outputs/
└── <job_id>/
    └── <run_id>/
        ├── posts.jsonl
        ├── failures.jsonl
        ├── report.json
        └── media/
```

체크포인트는 실행 위치의 `Checkpoint.json`입니다.

출력 위치를 바꾸려면 `--output-path`를 사용합니다.

```powershell
dcinside-scraper run `
  --source direct-post `
  --url "https://gall.dcinside.com/board/view/?id=dcbest&no=442937" `
  --output-path "D:\scraper-data\dcinside"
```

이 경우 출력은 `D:\scraper-data\dcinside\outputs\...`에 생성되고, 체크포인트는 `D:\scraper-data\dcinside\Checkpoint.json`에 저장됩니다.

### Job ID 운영 규칙

`--job-id`를 지정하지 않으면 자동 생성됩니다. 운영에서는 재시도, 로그 검색, 저장소 확인을 쉽게 하기 위해 직접 지정하는 것을 권장합니다.

권장 형식:

```text
dcinside-<source>-<gallery_or_keyword>-<YYYYMMDDHHMMSS>
```

예시:

```powershell
dcinside-scraper run `
  --job-id "dcinside-gallery-singlebungle1472-20260809120000" `
  --source gallery-search `
  --gallery-type minor `
  --gallery-id "singlebungle1472" `
  --s-type "search_subject_memo" `
  --keyword "싱글벙글"
```

### 중단과 재개

로컬 CLI에서 Ctrl+C를 한 번 누르면 graceful stop을 요청합니다. 가능한 경우 현재 처리 중인 작업을 정리하고 체크포인트를 저장합니다.

재개:

```powershell
dcinside-scraper resume --job-id "dcinside-gallery-singlebungle1472-20260809120000"
```

최신 체크포인트를 재개:

```powershell
dcinside-scraper resume
```

주의사항:

- `Checkpoint.json`은 작업 설정 snapshot과 완료된 게시글 키를 포함합니다.
- 수동 편집은 권장하지 않습니다.
- 체크포인트와 출력 JSONL은 같은 `--output-path` 기준으로 관리하세요.
- 저장소 파일만 옮기고 `Checkpoint.json`을 옮기지 않으면 resume이 실패할 수 있습니다.

### 파싱 실패 게시글 재처리

Job이 완료됐지만 `failures.jsonl`에 parser-stage 게시글 실패가 남았다면 전체 검색 Job을 다시 실행하지 말고 `retry-failures`를 사용합니다.

기본 재처리:

```powershell
dcinside-scraper retry-failures `
  --failure-file .\outputs\job-a\run-1\failures.jsonl `
  --job-id "retry-parser-job-a-20260810120000"
```

이미 성공한 게시글을 제외:

```powershell
dcinside-scraper retry-failures `
  --failure-file .\outputs\job-a\run-1\failures.jsonl `
  --existing-posts .\outputs\job-b\run-2\posts.jsonl
```

여러 로컬 output 아래의 기존 성공 게시글을 한 번에 제외:

```powershell
dcinside-scraper retry-failures `
  --failure-file .\outputs\job-a\run-1\failures.jsonl `
  --existing-posts-root .\outputs
```

운영 규칙:

- 원본 `failures.jsonl`은 삭제하거나 직접 수정하지 않습니다.
- 재처리 결과는 새 run의 `posts.jsonl`, `failures.jsonl`, `report.json`에 저장됩니다.
- `--existing-posts-root`는 로컬 파일시스템 전용입니다.
- S3/Garage 입력은 `s3://bucket/key` 형태의 명시 object ref만 지원하며 prefix 자동 탐색은 하지 않습니다.

## 컨테이너 운영

### 컨테이너 환경 변수

컨테이너 워커는 실행 시 아래 환경 변수가 필요합니다.

필수:

| 환경 변수 | 설명 |
| --- | --- |
| `DATABASE_URL` | PostgreSQL DSN |
| `S3_ENDPOINT_URL` | Garage 또는 S3 호환 endpoint |
| `S3_BUCKET` | 저장 bucket |
| `S3_ACCESS_KEY_ID` | S3 access key |
| `S3_SECRET_ACCESS_KEY` | S3 secret key |

선택:

| 환경 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `S3_REGION` | 없음 | S3 region |
| `S3_FORCE_PATH_STYLE` | `false` | path-style endpoint 강제 여부 |
| `RESUME` | `false` | `true`이면 run 인자 대신 checkpoint resume |
| `JOB_ID` | 없음 | 실행 또는 resume 대상 Job ID |
| `DCINSIDE_USER_AGENT_FILE` | 없음 | 컨테이너 내부 User-Agent 파일 경로 |
| `DCINSIDE_USER_AGENT_ROTATE_EVERY` | `10` | 요청 몇 회마다 User-Agent 교체 |
| `DCINSIDE_PROXY_HOST` | 없음 | Proxy host |
| `DCINSIDE_PROXY_ID` | 없음 | Proxy ID |
| `DCINSIDE_PROXY_PW` | 없음 | Proxy password |
| `DCINSIDE_REALTIME_ENABLED` | 없음 | 실시간 수집 활성화 |
| `DCINSIDE_REALTIME_MODE` | 없음 | `keyword` 또는 `all` |
| `DCINSIDE_REALTIME_KEYWORD` | 없음 | 실시간 키워드 수집 검색어 |
| `DCINSIDE_REALTIME_DURATION_SECONDS` | 없음 | 실시간 실행 시간, 초 |
| `DCINSIDE_REALTIME_END_AT` | 없음 | 실시간 종료 시각 |
| `DCINSIDE_REALTIME_POLL_INTERVAL_SECONDS` | `30` | 실시간 폴링 간격 |

실시간 종료 조건은 `DCINSIDE_REALTIME_DURATION_SECONDS`와 `DCINSIDE_REALTIME_END_AT` 중 하나만 지정해야 합니다.

### 환경 파일 예시

`.env.container`:

```dotenv
DATABASE_URL=postgresql://scraper:password@postgres.example.internal:5432/scraper
S3_ENDPOINT_URL=http://garage.example.internal:3900
S3_BUCKET=dcinside-scraper
S3_ACCESS_KEY_ID=access-key
S3_SECRET_ACCESS_KEY=secret-key
S3_REGION=garage
S3_FORCE_PATH_STYLE=true
DCINSIDE_USER_AGENT_ROTATE_EVERY=10
```

운영 환경의 `.env.container`는 저장소에 커밋하지 마세요.

### 컨테이너 실행

직접 게시글 수집:

```powershell
docker run --rm `
  --env-file .\.env.container `
  -e JOB_ID=dcinside-direct-20260809120000 `
  dcinside-scraper-worker `
  run `
  --source direct-post `
  --url "https://gall.dcinside.com/board/view/?id=dcbest&no=442937"
```

갤러리 검색 수집:

```powershell
docker run --rm `
  --env-file .\.env.container `
  -e JOB_ID=dcinside-gallery-singlebungle1472-20260809120000 `
  dcinside-scraper-worker `
  run `
  --source gallery-search `
  --gallery-type minor `
  --gallery-id "singlebungle1472" `
  --s-type "search_subject_memo" `
  --keyword "싱글벙글" `
  --request-interval-seconds 2.0 `
  --post-worker-count 2
```

컨테이너 entrypoint는 기본적으로 `run` 명령을 받습니다. resume은 `resume` 서브커맨드가 아니라 `RESUME=true` 환경 변수로 실행합니다.

```powershell
docker run --rm `
  --env-file .\.env.container `
  -e RESUME=true `
  -e JOB_ID=dcinside-gallery-singlebungle1472-20260809120000 `
  dcinside-scraper-worker
```

`JOB_ID`를 생략하고 `RESUME=true`만 지정하면 PostgreSQL 체크포인트 저장소의 최신 체크포인트를 로드하는 흐름을 사용합니다.

컨테이너에서 S3/Garage의 실패 파일을 재처리:

```powershell
docker run --rm `
  --env-file .\.env.container `
  -e JOB_ID=retry-parser-20260810120000 `
  dcinside-scraper-worker `
  retry-failures `
  --failure-ref s3://dcinside-scraper/outputs/job-a/run-1/failures.jsonl `
  --existing-posts s3://dcinside-scraper/outputs/job-b/run-2/posts.jsonl
```

컨테이너에서 로컬 failure 파일을 재처리할 때는 host output을 read-only로 mount한 뒤 컨테이너 내부 경로를 입력합니다.

```powershell
docker run --rm `
  --env-file .\.env.container `
  -v D:\scraper-outputs:/inputs:ro `
  dcinside-scraper-worker `
  retry-failures `
  --failure-file /inputs/job-a/run-1/failures.jsonl
```

### 컨테이너 출력

컨테이너는 stdout에 JSON 형태의 결과 또는 오류를 출력합니다. 완료 여부는 exit code로 판단합니다.

| Exit code | 의미 |
| --- | --- |
| `0` | 정상 완료 |
| `1` | 런타임 오류, 중단, CAPTCHA/차단에 따른 stop, 저장소 오류 등 |
| `2` | 설정 또는 입력값 검증 오류 |

운영 스케줄러에서는 exit code 0만 성공으로 보고, 1과 2는 알림 대상으로 처리하세요.

### S3/Garage 객체 구조

컨테이너 모드의 S3 object key는 로컬 출력 구조와 같은 논리 레이아웃을 사용합니다.

```text
outputs/<job_id>/<run_id>/posts.jsonl
outputs/<job_id>/<run_id>/failures.jsonl
outputs/<job_id>/<run_id>/report.json
outputs/<job_id>/<run_id>/media/...
```

운영 관점에서 중요한 점:

- `posts.jsonl`은 게시글 단위 JSONL입니다.
- `failures.jsonl`은 게시글별 실패 기록입니다.
- `report.json`은 작업 종료 시 생성됩니다.
- 프로세스가 중간에 죽으면 `report.json`이 없을 수 있습니다.
- resume 판단은 S3가 아니라 PostgreSQL 체크포인트를 기준으로 합니다.
- 현재 S3 출력은 로컬 spool 파일을 유지하고, append 후 전체 JSONL 객체를 다시 업로드하는 방식입니다. 대량 수집에서는 object 크기와 업로드 비용을 관찰하세요.

## 저장소 인프라 권장 구성

### Garage

Garage는 S3 호환 객체 저장소로 사용합니다.

운영 요구사항:

- bucket 생성
- access key와 secret key 발급
- 컨테이너 네트워크에서 접근 가능한 endpoint 제공
- path-style endpoint가 필요하면 `S3_FORCE_PATH_STYLE=true` 설정
- bucket lifecycle 또는 별도 정리 정책 수립

이 프로젝트는 Garage 전용 API를 사용하지 않고 S3 호환 API만 사용합니다. 따라서 향후 SeaweedFS로 확장할 수 있습니다. SeaweedFS로 전환할 때도 endpoint, bucket, access key, secret key, path-style 설정만 맞으면 코드 변경 없이 같은 인터페이스를 유지하는 것을 목표로 합니다.

### PostgreSQL

체크포인트 테이블은 애플리케이션이 자동 생성합니다.

```sql
create table if not exists dcinside_checkpoints (
  job_id text primary key,
  updated_at timestamptz not null,
  checkpoint_json jsonb not null
);
```

운영 요구사항:

- `DATABASE_URL`로 접속 가능한 DB와 사용자
- `create table` 권한
- insert/update/select 권한
- 정기 백업
- 오래된 checkpoint 정리 정책

체크포인트에는 작업 설정 snapshot, 검색 위치, 완료된 게시글 키, 남은 큐가 들어갑니다. DB를 복구하지 못하면 컨테이너 resume이 불가능합니다.

## User-Agent 운영

기본 파일명은 `user-agents.txt`입니다. 한 줄에 하나의 User-Agent를 적습니다.

로컬에서 파일 가져오기:

```powershell
dcinside-scraper import-user-agents ".\downloaded-user-agents.txt"
```

로컬 실행에서 명시:

```powershell
dcinside-scraper run `
  --source direct-post `
  --url "https://gall.dcinside.com/board/view/?id=dcbest&no=442937" `
  --user-agent-file ".\user-agents.txt" `
  --user-agent-rotate-every 10
```

컨테이너에서 사용하려면 파일을 이미지에 포함하거나 volume으로 주입하고, 경로를 환경 변수로 넘깁니다.

volume 주입 예시:

```powershell
docker run --rm `
  --env-file .\.env.container `
  -e DCINSIDE_USER_AGENT_FILE=/app/config/user-agents.txt `
  -v ${PWD}\user-agents.txt:/app/config/user-agents.txt:ro `
  dcinside-scraper-worker `
  run `
  --source direct-post `
  --url "https://gall.dcinside.com/board/view/?id=dcbest&no=442937"
```

운영 권장:

- 기본 교체 주기 10회를 먼저 사용합니다.
- 차단이 발생한다고 무조건 교체 주기를 낮추지 마세요.
- 요청 간격을 늘리고 워커 수를 낮추는 것이 먼저입니다.
- 빈 파일, UTF-8이 아닌 파일은 거부됩니다.

## Proxy 운영

로컬 Proxy 설정은 `.env` 파일을 사용합니다.

```dotenv
DCINSIDE_PROXY_HOST=http://proxy.example.com:8080
DCINSIDE_PROXY_ID=username
DCINSIDE_PROXY_PW=password
```

CLI로 생성:

```powershell
dcinside-scraper configure-proxy `
  --host "http://proxy.example.com:8080" `
  --id "username" `
  --password "password"
```

컨테이너에서는 환경 변수로 주입합니다.

```powershell
docker run --rm `
  --env-file .\.env.container `
  -e DCINSIDE_PROXY_HOST=http://proxy.example.com:8080 `
  -e DCINSIDE_PROXY_ID=username `
  -e DCINSIDE_PROXY_PW=password `
  dcinside-scraper-worker `
  run `
  --source direct-post `
  --url "https://gall.dcinside.com/board/view/?id=dcbest&no=442937"
```

운영 주의:

- `.env`는 평문입니다.
- `.gitignore`에 `.env`가 포함되어 있지만, 실수로 별도 이름의 env 파일을 커밋하지 않도록 주의하세요.
- 로그에는 안전한 proxy label만 남기는 구조이지만, 외부 실행 스크립트가 환경 변수를 출력하지 않게 하세요.
- 프록시 장애는 HTTP 요청 실패로 나타납니다. 먼저 프록시 없이 동일 요청이 되는지 확인하세요.

## 요청 속도와 워커 튜닝

관련 옵션:

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--request-interval-seconds` | `1.0` | 요청 간 최소 대기 시간 |
| `--post-worker-count` | `1` | 게시글 상세 수집 워커 수 |
| `--queue-max-size` | 없음 | 게시글 후보 큐 최대 크기 |
| `--max-comment-pages` | `100` | 게시글당 댓글 AJAX 최대 페이지 수 |

보수적 시작값:

```powershell
--request-interval-seconds 2.0 --post-worker-count 1
```

중간 규모 수집:

```powershell
--request-interval-seconds 1.5 --post-worker-count 2 --queue-max-size 100
```

장애가 잦을 때:

```powershell
--request-interval-seconds 5.0 --post-worker-count 1 --queue-max-size 20
```

튜닝 순서:

1. 기본값으로 작은 Job을 실행합니다.
2. CAPTCHA, 403, 비정상 HTML, 타임아웃이 없는지 확인합니다.
3. 워커 수를 1씩만 늘립니다.
4. 실패가 증가하면 워커 수를 되돌리고 요청 간격을 늘립니다.
5. 장시간 Job은 중간 중단과 resume이 가능한지 먼저 검증합니다.

## 실시간 수집 운영

실시간 수집은 환경 변수로 활성화합니다.

실시간 키워드:

```powershell
$env:DCINSIDE_REALTIME_ENABLED = "true"
$env:DCINSIDE_REALTIME_MODE = "keyword"
$env:DCINSIDE_REALTIME_KEYWORD = "싱글벙글"
$env:DCINSIDE_REALTIME_DURATION_SECONDS = "3600"

dcinside-scraper run `
  --job-id "dcinside-realtime-keyword-20260809120000"
```

실시간 전체:

```powershell
$env:DCINSIDE_REALTIME_ENABLED = "true"
$env:DCINSIDE_REALTIME_MODE = "all"
$env:DCINSIDE_REALTIME_DURATION_SECONDS = "3600"

dcinside-scraper run `
  --job-id "dcinside-realtime-all-singlebungle1472-20260809120000" `
  --gallery-type minor `
  --gallery-id "singlebungle1472"
```

컨테이너:

```powershell
docker run --rm `
  --env-file .\.env.container `
  -e JOB_ID=dcinside-realtime-keyword-20260809120000 `
  -e DCINSIDE_REALTIME_ENABLED=true `
  -e DCINSIDE_REALTIME_MODE=keyword `
  -e DCINSIDE_REALTIME_KEYWORD="싱글벙글" `
  -e DCINSIDE_REALTIME_DURATION_SECONDS=3600 `
  dcinside-scraper-worker `
  run
```

운영 규칙:

- 종료 조건은 실행 시간 또는 종료 시각 중 하나만 지정합니다.
- 실시간 Job은 영구 데몬이 아니라 종료 조건을 가진 장시간 Job입니다.
- 주기 실행이 필요하면 스케줄러가 Job을 다시 실행하게 구성하세요.
- 같은 갤러리/키워드의 실시간 Job을 동시에 여러 개 실행하면 중복 수집이 늘어납니다.

## 스케줄링

### Windows 작업 스케줄러

PowerShell 스크립트 예시 `run-dcinside-job.ps1`:

```powershell
Set-Location "D:\HongDev\ELSAPHABA\DCinside-Scraper"
.\.venv\Scripts\Activate.ps1

dcinside-scraper run `
  --job-id "dcinside-gallery-singlebungle1472-$(Get-Date -Format yyyyMMddHHmmss)" `
  --source gallery-search `
  --gallery-type minor `
  --gallery-id "singlebungle1472" `
  --s-type "search_subject_memo" `
  --keyword "싱글벙글" `
  --request-interval-seconds 2.0 `
  --post-worker-count 1

exit $LASTEXITCODE
```

작업 스케줄러에서는 `powershell.exe`를 실행하고 인수에 아래처럼 넣습니다.

```text
-ExecutionPolicy Bypass -File "D:\path\run-dcinside-job.ps1"
```

### Linux cron

```cron
0 * * * * cd /srv/dcinside-scraper && . .venv/bin/activate && dcinside-scraper run --job-id "dcinside-hourly-$(date +\%Y\%m\%d\%H\%M\%S)" --source integrated-search --keyword "싱글벙글" --page-start 1 --page-end 5 >> /var/log/dcinside-scraper.log 2>&1
```

### systemd service

`/etc/systemd/system/dcinside-scraper.service` 예시:

```ini
[Unit]
Description=DCinside Scraper Job
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/srv/dcinside-scraper
EnvironmentFile=/srv/dcinside-scraper/.env.runtime
ExecStart=/srv/dcinside-scraper/.venv/bin/dcinside-scraper run --source integrated-search --keyword 싱글벙글 --page-start 1 --page-end 5
```

주기 실행은 timer를 별도로 둡니다.

## MCP 서버 운영

설치:

```powershell
python -m pip install -e ".[mcp]"
```

실행:

```powershell
python -m dcinside_scraper.adapters.mcp
```

제공 도구:

| 도구 | 설명 |
| --- | --- |
| `search_gallery` | 갤러리 검색 |
| `search_integrated` | 통합 검색 |
| `fetch_post` | 게시글 상세 수집 |
| `fetch_comments` | 댓글 수집 |
| `run_job` | Job 실행 |
| `resume_job` | Job 재개 |

운영 주의:

- MCP 서버는 별도 프로세스로 실행합니다.
- 저장소와 HTTP 런타임 구성은 MCP 핸들러 실행 환경에 맞춰 주입해야 합니다.
- 장시간 대량 수집은 MCP 요청 하나로 무리하게 실행하기보다 Job 단위 실행과 checkpoint/resume을 사용하는 것이 낫습니다.

## 로그와 모니터링

### 로컬 CLI stdout

CLI는 시작 시 아래 정보를 출력합니다.

```text
job_id: ...
source: ...
output_path: ...
workers: ...
request_interval_seconds: ...
```

종료 시 아래 정보를 출력합니다.

```text
status: completed|stopped|failed
success_count: ...
failure_count: ...
deduped_count: ...
filtered_count: ...
resume: python -m dcinside_scraper.adapters.cli resume --job-id ...
```

### 컨테이너 stdout

컨테이너는 JSON line 형태의 결과 또는 오류를 출력합니다. 컨테이너 운영 환경에서는 stdout 수집기를 붙이고 exit code를 알림 조건으로 사용하세요.

### 확인할 지표

| 지표 | 확인 위치 | 의미 |
| --- | --- | --- |
| `success_count` | `report.json`, stdout | 성공 수집 게시글 수 |
| `failure_count` | `report.json`, stdout | 게시글 단위 실패 수 |
| `deduped_count` | `report.json`, stdout | 중복 제거 수 |
| `filtered_count` | `report.json`, stdout | 범위 필터로 제외된 수 |
| `status` | `report.json`, checkpoint | 작업 상태 |
| `reason` | checkpoint | 중단 사유 |
| `updated_at` | checkpoint | 마지막 체크포인트 저장 시각 |

알림 권장 조건:

- exit code가 0이 아님
- `failure_count`가 평소보다 급증
- `status`가 `stopped` 또는 `failed`
- `reason`이 `captcha`, `timeout`, `error`
- 일정 시간 동안 checkpoint `updated_at`이 갱신되지 않음
- S3에 `report.json`이 생성되지 않은 상태로 컨테이너가 종료됨

## 장애 대응 Runbook

### 1. 입력값 검증 오류

증상:

- exit code 2
- `ERROR [validation_failure]`
- 필수 옵션 누락

조치:

1. CLI help를 확인합니다.
2. `--source`별 필수 옵션을 확인합니다.
3. 날짜는 `YYYY-MM-DD` 형식인지 확인합니다.
4. 실시간 종료 조건이 두 개 모두 설정되어 있지 않은지 확인합니다.
5. 컨테이너라면 필수 환경 변수가 모두 있는지 확인합니다.

### 2. CAPTCHA 또는 차단

증상:

- 작업 status가 `stopped`
- checkpoint reason이 `captcha` 또는 차단 관련 오류
- HTML이 정상 게시글 구조가 아님

조치:

1. 작업을 즉시 반복 재시도하지 않습니다.
2. `--post-worker-count`를 1로 낮춥니다.
3. `--request-interval-seconds`를 늘립니다.
4. User-Agent 파일이 정상인지 확인합니다.
5. Proxy를 쓰는 경우 프록시 품질을 확인합니다.
6. 충분히 기다린 뒤 `resume`합니다.

CAPTCHA 자동 우회는 구현하지 않습니다.

### 3. Parser-stage 게시글 실패

증상:

- 작업 자체는 `completed`이나 `failure_count`가 증가
- `failures.jsonl`의 `stage`가 `post`
- `reason`이 `post title missing`, `post author missing`, `post identity missing` 같은 parser-stage 사유
- 같은 URL을 브라우저나 단건 direct-post로 다시 열면 정상 게시글인 경우가 있음

실사이트 smoke test에서 확인한 사례:

- 검색 Job 1차 실행 중 `post title missing`이 다수 발생
- 같은 실패 URL만 direct-post 경로로 재시도하자 모두 회수됨
- 원인은 삭제글이 아니라 요청 시점의 일시적 비정상/부분 응답 또는 parser가 허용하지 않은 상세 구조일 수 있음

조치:

1. 실패 URL 대표 1개를 브라우저 또는 단건 direct-post로 확인합니다.
2. 정상 게시글이면 전체 검색 Job을 다시 돌리지 말고 실패 URL만 재처리합니다.
3. `retry-failures` 명령을 사용해 원본 실패 파일은 보존하고 새 run에 회수 결과를 저장합니다.
4. 이미 성공한 게시글이 섞여 있으면 `--existing-posts` 또는 로컬 전용 `--existing-posts-root`로 제외합니다.
5. 같은 reason이 계속 남으면 parser fixture를 추가하고 selector를 수정합니다.

원본 `failures.jsonl`은 감사와 재현을 위해 삭제하거나 직접 수정하지 않습니다.

### 4. 미디어 ID 길이 검증 오류

증상:

- 게시글 상세 수집 중 validation 오류
- 오류 필드가 `MediaItem.media_id`
- 메시지가 `String should have at most 200 characters` 계열
- 이미지 URL의 `viewimage.php?no=` 값이 긴 서명 토큰 형태

조치:

1. 스크래퍼가 긴 `viewimage.php?no=` 값을 `media_id`로 저장하지 않는 버전인지 확인합니다.
2. 긴 이미지 서명 토큰은 `url` 또는 `source_url`에만 보존하고 `media_id=null`로 저장해야 합니다.
3. `movie_view?no=<숫자>`처럼 짧고 안정적인 자체 동영상 번호는 `media_id`로 유지할 수 있습니다.
4. 오래된 결과에서 이 오류가 발생했다면 해당 게시글만 direct-post 또는 `retry-failures` 재처리 경로로 다시 수집합니다.

### 5. S3/Garage 쓰기 실패

증상:

- exit code 1
- 저장소 오류
- S3 bucket에 object가 생성되지 않음

조치:

1. `S3_ENDPOINT_URL`이 컨테이너에서 접근 가능한지 확인합니다.
2. `S3_BUCKET`이 존재하는지 확인합니다.
3. access key와 secret key 권한을 확인합니다.
4. Garage가 path-style을 요구하면 `S3_FORCE_PATH_STYLE=true`를 설정합니다.
5. 네트워크 DNS와 방화벽을 확인합니다.
6. 실패 후에는 PostgreSQL checkpoint 기준으로 resume합니다.

### 6. PostgreSQL 체크포인트 실패

증상:

- exit code 1
- checkpoint write/load failed
- resume 시 checkpoint not found

조치:

1. `DATABASE_URL` 접속 정보를 확인합니다.
2. DB 사용자가 `create table`, `select`, `insert`, `update` 권한을 갖는지 확인합니다.
3. `dcinside_checkpoints` 테이블이 생성되었는지 확인합니다.
4. `job_id`가 정확한지 확인합니다.
5. DB 복구 후 같은 `JOB_ID`로 resume합니다.

확인 SQL:

```sql
select job_id, updated_at
from dcinside_checkpoints
order by updated_at desc
limit 20;
```

### 7. 출력은 있는데 report가 없음

원인:

- 작업 도중 프로세스가 강제 종료됨
- S3 report 업로드 전에 장애 발생
- 로컬에서 프로세스 kill

조치:

1. `posts.jsonl`과 `failures.jsonl`이 어디까지 작성되었는지 확인합니다.
2. checkpoint가 남아 있으면 resume합니다.
3. resume 완료 후 새 run의 `report.json`을 기준으로 최종 집계합니다.

### 8. 댓글 수집이 너무 느림

원인:

- 댓글 많은 게시글
- `--max-comment-pages`가 높음
- 요청 간격이 큼

조치:

1. 댓글이 필요 없으면 `--no-comments`를 사용합니다.
2. 댓글이 필요하지만 너무 느리면 `--max-comment-pages`를 낮춥니다.
3. 대량 수집에서는 먼저 게시글 본문만 수집하고 댓글 수집은 별도 Job으로 나누는 방식을 검토합니다.

### 9. JSONL을 Polars가 읽지 못함

조치:

1. 파일이 완전히 쓰인 뒤 읽습니다.
2. 작업 중인 `posts.jsonl`을 동시에 분석하지 않습니다.
3. 실패한 줄이 있는지 확인합니다.
4. `failures.jsonl`과 `report.json`을 같이 확인합니다.

예시:

```python
import polars as pl

posts = pl.read_ndjson("outputs/job/run/posts.jsonl")
```

## 백업과 복구

### 로컬 백업

같이 백업해야 하는 파일:

- `outputs/`
- `Checkpoint.json`
- 운영에 사용하는 `.env`
- 운영에 사용하는 `user-agents.txt`

주의:

- `.env`에는 프록시 비밀번호가 들어갈 수 있습니다.
- 백업 저장소 접근 권한을 제한하세요.

### 컨테이너 백업

같이 백업해야 하는 대상:

- Garage/S3 bucket
- PostgreSQL `dcinside_checkpoints` 테이블
- 운영 env 파일 또는 secret manager 설정
- User-Agent 파일

복구 순서:

1. PostgreSQL checkpoint를 복구합니다.
2. S3 bucket과 object를 복구합니다.
3. 같은 `JOB_ID`로 `RESUME=true` 컨테이너를 실행합니다.
4. 완료 후 새 `report.json`과 기존 JSONL을 확인합니다.

### 보존 정책

권장 보존 단위:

- 원본 JSONL: 장기 보존
- `failures.jsonl`: 최소 재처리 기간 동안 보존
- `report.json`: 장기 보존
- checkpoint: 완료 후 일정 기간 보존
- media: 저장소 비용에 따라 별도 lifecycle 적용

완료된 Job의 checkpoint를 즉시 삭제하지 마세요. 결과 검증과 재처리 기준으로 사용할 수 있습니다.

## 보안 운영

민감 정보:

- `DCINSIDE_PROXY_PW`
- `S3_SECRET_ACCESS_KEY`
- `DATABASE_URL`의 비밀번호
- Proxy ID/PW가 들어간 `.env`

권장:

- `.env`와 `.env.container`는 커밋하지 않습니다.
- CI/CD 로그에 환경 변수를 출력하지 않습니다.
- 운영 서버의 파일 권한을 제한합니다.
- access key는 스크래퍼 bucket에 필요한 권한만 부여합니다.
- PostgreSQL 계정은 checkpoint 테이블에 필요한 권한만 부여합니다.
- 주기적으로 key를 교체합니다.

## 배포 전 체크리스트

로컬:

- [ ] Python 3.11 이상 확인
- [ ] `python -m pip install -e .` 완료
- [ ] `dcinside-scraper --help` 정상
- [ ] 작은 `direct-post` Job 성공
- [ ] `outputs/<job_id>/<run_id>/posts.jsonl` 생성 확인
- [ ] `Checkpoint.json` 생성 확인
- [ ] `resume --job-id` 동작 확인

컨테이너:

- [ ] Docker 이미지 빌드 성공
- [ ] Garage/S3 bucket 생성
- [ ] S3 access key 권한 확인
- [ ] PostgreSQL 접속 확인
- [ ] `.env.container` 작성
- [ ] 작은 `direct-post` Job 성공
- [ ] S3 `posts.jsonl`, `report.json` 생성 확인
- [ ] PostgreSQL `dcinside_checkpoints` row 생성 확인
- [ ] `RESUME=true` 실행 확인

운영:

- [ ] Job ID naming 규칙 확정
- [ ] 요청 간격과 워커 기본값 확정
- [ ] User-Agent 파일 관리 방식 확정
- [ ] Proxy 사용 여부 확정
- [ ] 백업 주기 확정
- [ ] 실패 알림 기준 확정
- [ ] CAPTCHA 발생 시 대응 절차 공유

## 운영 제한과 향후 과제

현재 운영 제한:

- 컨테이너는 하나의 프로세스가 하나의 Job을 실행하는 구조입니다.
- 중앙 Job 큐 서비스는 아직 없습니다.
- 실패 게시글 전용 중앙 DLQ는 아직 없습니다.
- parser-stage 게시글 실패 재처리 명령은 제공되지만, scheduler나 중앙 큐에 자동 연결되지는 않습니다.
- S3 출력은 append마다 spool된 JSONL 전체를 업로드합니다.
- CAPTCHA 자동 우회는 제공하지 않습니다.
- 기본 컨테이너 이미지는 MCP extra를 포함하지 않습니다.

향후 과제:

- UOW-010: AWS CDK 기반 IaC
- 커뮤니티별 스크래퍼 공통 운영 Job 큐
- 실패 재처리 Job의 중앙 DLQ/scheduler 연동
- 공통 스키마 정규화 파이프라인
- PostgreSQL 기반 Job 이력 테이블
- S3 JSONL 파티셔닝 또는 append 최적화
- Kubernetes Job/CronJob manifest
- MCP 운영 이미지 분리

## 관련 문서

- 프로젝트 README: `README.md`
- 기능 명세서: `docs/Function_Specification.md`
- 공유 저장소 규약: `docs/Shared_Storage_Contract.md`
- AI-DLC 문서: `aidlc-docs/`
- UOW 공개 계약: `aidlc-docs/construction/*/code/public-contracts.md`
