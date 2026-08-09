# 공유 저장소 규약

이 문서는 여러 커뮤니티 스크래퍼가 하나의 S3 호환 객체 저장소와 하나의 PostgreSQL 저장소를 공유할 때 지켜야 할 저장소 규약을 정의합니다.

목표는 저장소 인프라를 공유하되, 각 스크래퍼의 결과물, 체크포인트, Job 상태, 장애 기록이 서로 충돌하지 않도록 논리적 namespace를 명확히 분리하는 것입니다.

## 핵심 결론

공유 저장소는 아래 원칙을 따릅니다.

- S3 호환 저장소는 여러 스크래퍼가 공유할 수 있습니다.
- PostgreSQL 저장소도 여러 스크래퍼가 공유할 수 있습니다.
- 공유는 물리 인프라 공유를 의미합니다.
- 논리 데이터는 `environment`, `site_id`, `job_id`, `run_id`로 반드시 분리합니다.
- object key와 DB primary key는 전역 충돌이 나지 않게 설계합니다.
- 스크래퍼별 API query, parser, source option은 저장소 규약에 들어가지 않습니다.
- 원본 JSONL은 커뮤니티별 schema를 유지합니다.
- 공통 분석 테이블은 별도 정규화 단계에서 생성합니다.

가장 중요한 규칙은 이것입니다.

```text
같은 S3 bucket과 같은 PostgreSQL database를 쓰더라도,
다른 스크래퍼가 같은 object key나 같은 checkpoint key를 쓰면 안 됩니다.
```

## 현재 호환 규약과 목표 규약

현재 구현은 아래 레이아웃을 사용합니다.

```text
outputs/<job_id>/<run_id>/posts.jsonl
outputs/<job_id>/<run_id>/failures.jsonl
outputs/<job_id>/<run_id>/report.json
outputs/<job_id>/<run_id>/media/...
```

이 레이아웃은 이미 동작하므로 유지합니다. 다만 여러 스크래퍼가 같은 bucket을 공유하려면 `job_id`가 전역적으로 고유해야 합니다.

현재 호환 규약:

```text
outputs/<job_id>/<run_id>/...
```

현재 호환 모드에서의 필수 조건:

```text
job_id 안에 environment와 site_id를 포함한다.
```

예:

```text
prod-site-a-board-search-20260809T120000Z-a1b2c3
prod-site-b-direct-post-20260809T121500Z-d4e5f6
```

장기 목표 규약:

```text
outputs/<environment>/<site_id>/<job_id>/<run_id>/...
```

목표 규약이 더 명확하지만, 현재 구현과 호환하려면 우선 `job_id` namespace 규칙을 강제하는 방식으로 시작합니다. 이후 저장소 어댑터가 `environment/site_id` prefix를 직접 지원하면 목표 규약으로 이동합니다.

## 식별자 규약

### `environment`

실행 환경입니다.

권장 값:

```text
local
dev
staging
prod
test
```

규칙:

- 소문자만 사용합니다.
- 공백을 사용하지 않습니다.
- 운영 데이터는 반드시 `prod`로 분리합니다.
- 개발/테스트 Job이 운영 prefix나 운영 DB row를 쓰면 안 됩니다.

### `site_id`

대상 커뮤니티 식별자입니다.

규칙:

- 소문자 slug를 사용합니다.
- 공백을 사용하지 않습니다.
- URL domain 전체를 그대로 쓰지 않습니다.
- 사람이 알아볼 수 있고 안정적인 값을 사용합니다.
- 한 번 정한 `site_id`는 변경하지 않습니다.

권장 문자:

```text
a-z
0-9
-
_
```

정규식:

```text
^[a-z0-9][a-z0-9_-]{1,48}[a-z0-9]$
```

### `source_type`

수집 시작 방식입니다.

권장 공통 값:

```text
direct-post
board-search
integrated-search
deep-search
no-keyword-range
realtime-keyword
realtime-all
parser-failure-retry
```

커뮤니티별 query 구조가 달라도 `source_type`은 공통 기능명을 사용합니다.

### `job_id`

Job의 전역 식별자입니다.

현재 호환 모드에서는 `job_id`가 S3 object key와 PostgreSQL checkpoint key 충돌을 막는 핵심입니다.

권장 형식:

```text
<environment>-<site_id>-<source_type>-<YYYYMMDDTHHMMSSZ>-<short_id>
```

예:

```text
prod-site-a-board-search-20260809T120000Z-a1b2c3
dev-site-b-direct-post-20260809T121500Z-d4e5f6
```

규칙:

- 전역 고유해야 합니다.
- `environment`를 포함해야 합니다.
- `site_id`를 포함해야 합니다.
- `source_type`을 포함해야 합니다.
- UTC timestamp를 포함해야 합니다.
- 마지막에 6자 이상의 짧은 난수 또는 hash를 붙입니다.
- 같은 `job_id`를 서로 다른 스크래퍼가 사용하면 안 됩니다.

금지:

```text
job-1
test
latest
scrape
20260809
```

이런 값은 공유 저장소에서 충돌 가능성이 높습니다.

### `run_id`

하나의 Job 실행 시도 식별자입니다.

권장 형식:

```text
<YYYYMMDDTHHMMSSZ>-<short_id>
```

예:

```text
20260809T120000Z-8f13ad
```

규칙:

- 같은 `job_id`를 resume하면 새 `run_id`를 생성합니다.
- 기존 `run_id` 디렉터리에 다시 쓰지 않습니다.
- `run_id`는 Job 내부에서만 고유해도 되지만, 전역 고유에 가깝게 만드는 것이 좋습니다.

### `worker_id`

컨테이너, 프로세스, 또는 워커 인스턴스 식별자입니다.

권장 형식:

```text
<site_id>-worker-<hostname>-<pid>
```

운영 시스템이 container id 또는 pod name을 제공하면 그것을 사용해도 됩니다.

## S3 호환 저장소 규약

### Bucket 전략

권장 순서:

1. 환경별 bucket 분리
2. 단일 bucket + environment prefix

권장:

```text
community-scraper-dev
community-scraper-staging
community-scraper-prod
```

bucket을 하나만 써야 한다면:

```text
dev/outputs/...
staging/outputs/...
prod/outputs/...
```

운영 권장:

- 운영 bucket과 개발 bucket은 분리합니다.
- access key도 환경별로 분리합니다.
- 운영 writer key를 개발 환경에 넣지 않습니다.

### 현재 호환 object key

현재 구현과 호환되는 표준 object key입니다.

```text
outputs/<job_id>/<run_id>/posts.jsonl
outputs/<job_id>/<run_id>/failures.jsonl
outputs/<job_id>/<run_id>/report.json
outputs/<job_id>/<run_id>/media/<board_id>/<post_id_or_number>/<media_type>/<filename>
```

이 구조에서는 `job_id`가 namespace 역할을 합니다.

필수:

```text
job_id = <environment>-<site_id>-<source_type>-<timestamp>-<short_id>
```

### 목표 object key

저장소 어댑터가 environment/site prefix를 지원하면 아래 구조를 사용합니다.

```text
outputs/<environment>/<site_id>/<job_id>/<run_id>/posts.jsonl
outputs/<environment>/<site_id>/<job_id>/<run_id>/failures.jsonl
outputs/<environment>/<site_id>/<job_id>/<run_id>/report.json
outputs/<environment>/<site_id>/<job_id>/<run_id>/media/<board_id>/<post_id_or_number>/<media_type>/<filename>
```

장점:

- prefix 검색이 쉽습니다.
- site별 lifecycle 정책 적용이 쉽습니다.
- site별 권한 분리가 쉽습니다.
- `job_id` 실수에 대한 방어력이 커집니다.

### Reserved prefixes

아래 prefix는 공통 규약에서 예약합니다.

```text
outputs/
manifests/
normalized/
exports/
tmp/
locks/
_system/
```

의미:

| Prefix | 용도 |
| --- | --- |
| `outputs/` | 원본 수집 결과 |
| `manifests/` | Job/run manifest |
| `normalized/` | 공통 스키마 정규화 결과 |
| `exports/` | 외부 분석/배포용 export |
| `tmp/` | 임시 업로드 |
| `locks/` | object storage 기반 lock이 필요할 때 |
| `_system/` | 저장소 버전, marker, 운영 metadata |

스크래퍼는 예약 prefix를 임의 용도로 사용하지 않습니다.

### JSONL object 규칙

`posts.jsonl`:

- 한 줄에 게시글 하나입니다.
- UTF-8입니다.
- 줄 끝은 `\n`입니다.
- JSON object만 허용합니다.
- 빈 줄을 쓰지 않습니다.
- schema version을 각 row에 포함합니다.
- 원본 community schema를 유지합니다.

`failures.jsonl`:

- 한 줄에 실패 하나입니다.
- 민감정보를 제거한 safe failure만 저장합니다.
- proxy password, access key, cookie, authorization header를 저장하지 않습니다.
- 실패 stage, reason, retryable 여부를 포함합니다.
- parser-stage 게시글 실패 재처리의 입력으로 사용할 수 있으므로 원본 파일을 직접 수정하지 않습니다.
- 재처리 결과는 새 run의 `posts.jsonl`, `failures.jsonl`, `report.json`으로 남기고, 원본 failure row는 감사와 재현을 위해 보존합니다.

`report.json`:

- run 종료 시 한 번 씁니다.
- Job 전체 요약입니다.
- `success_count`, `failure_count`, `deduped_count`, `filtered_count`, `status`를 포함합니다.
- parser-stage 실패 재처리 Job이면 `metadata.parser_failure_retry`에 입력 failure 수, 제외 수, 선택 수, 성공 수, 남은 실패 수를 포함합니다.
- `report.json`이 없으면 run이 비정상 종료되었을 수 있습니다.

### Parser-stage 실패 재처리 run 규약

재처리 Job은 원본 수집 Job의 산출물을 직접 수정하지 않습니다.

입력:

- 원본 `failures.jsonl`
- 선택적으로 기존 성공 `posts.jsonl`
- 선택적으로 로컬 output root의 `posts.jsonl` 자동 탐색 결과

저장:

- 재처리 결과는 새 `job_id` 또는 새 run 아래의 `posts.jsonl`, `failures.jsonl`, `report.json`에 저장합니다.
- 원본 `failures.jsonl` row는 감사와 재현을 위해 그대로 둡니다.
- S3 호환 저장소 입력은 `s3://bucket/key` 명시 object ref만 사용합니다.
- S3 prefix listing 기반 자동 탐색은 기본 저장소 계약에 포함하지 않습니다.
- 로컬 `--existing-posts-root` 같은 directory scan 편의 기능은 로컬 실행 전용입니다.

재처리 후보 key:

```text
(site_id, board_id|gallery_id, post_id)
```

운영자는 원본 Job과 재처리 Job의 관계를 `job_id`, `run_id`, `report.metadata.parser_failure_retry.retry_source_failure_refs`로 추적합니다.

### Manifest 규약

장기 목표에서는 run별 manifest를 둡니다.

권장 key:

```text
manifests/<environment>/<site_id>/<job_id>/<run_id>/manifest.json
```

Manifest 예시:

```json
{
  "schema_version": "community_scraper.run_manifest.v1",
  "environment": "prod",
  "site_id": "site-a",
  "job_id": "prod-site-a-board-search-20260809T120000Z-a1b2c3",
  "run_id": "20260809T120000Z-8f13ad",
  "source_type": "board-search",
  "status": "completed",
  "started_at": "2026-08-09T12:00:00Z",
  "finished_at": "2026-08-09T12:30:00Z",
  "objects": {
    "posts": "outputs/prod/site-a/prod-site-a-board-search-20260809T120000Z-a1b2c3/20260809T120000Z-8f13ad/posts.jsonl",
    "failures": "outputs/prod/site-a/prod-site-a-board-search-20260809T120000Z-a1b2c3/20260809T120000Z-8f13ad/failures.jsonl",
    "report": "outputs/prod/site-a/prod-site-a-board-search-20260809T120000Z-a1b2c3/20260809T120000Z-8f13ad/report.json"
  }
}
```

현재 구현은 `report.json`을 우선 사용합니다. manifest는 여러 스크래퍼 통합 운영 단계에서 추가합니다.

### Media object 규칙

권장 key:

```text
outputs/<environment>/<site_id>/<job_id>/<run_id>/media/<board_id>/<post_id>/<media_type>/<filename>
```

현재 호환 key:

```text
outputs/<job_id>/<run_id>/media/<board_id>/<post_id_or_number>/<media_type>/<filename>
```

규칙:

- filename은 path traversal이 불가능하도록 sanitize합니다.
- 원본 URL query 전체를 filename에 넣지 않습니다.
- 같은 게시글의 같은 media가 중복될 수 있으면 media hash 또는 media id를 filename에 포함합니다.
- media metadata는 게시글 JSONL 안에도 저장합니다.
- media object key에는 secret, signed URL token, cookie 값을 넣지 않습니다.

### Content-Type 규칙

권장 content type:

| Object | Content-Type |
| --- | --- |
| `posts.jsonl` | `application/x-ndjson` |
| `failures.jsonl` | `application/x-ndjson` |
| `report.json` | `application/json` |
| `manifest.json` | `application/json` |
| image | 실제 MIME 또는 `application/octet-stream` |
| video | 실제 MIME 또는 `application/octet-stream` |

### Upload 원자성

현재 구현은 로컬 spool에 JSONL을 쌓고 object를 다시 업로드하는 방식입니다.

운영 규칙:

- 같은 `posts.jsonl` object에 여러 프로세스가 동시에 쓰면 안 됩니다.
- 한 `job_id/run_id`는 한 프로세스만 writer가 됩니다.
- resume은 새 `run_id`에 씁니다.
- 이전 run의 object를 덮어쓰지 않습니다.
- `report.json`은 run 종료 marker로 봅니다.

### Lifecycle 규칙

권장 보존:

| 데이터 | 권장 보존 |
| --- | --- |
| 원본 `posts.jsonl` | 장기 보존 |
| `failures.jsonl` | 재처리 가능 기간 이상 |
| `report.json` | 장기 보존 |
| `manifest.json` | 장기 보존 |
| media | 저장 비용에 따라 정책 분리 |
| `tmp/` | 짧게 보존 후 삭제 |
| normalized output | 재생성 가능하면 중기 보존 |

운영 bucket lifecycle 예:

```text
tmp/                         7일 후 삭제
outputs/*/*/*/*/media/       비용에 따라 30~365일
outputs/*/*/*/*/posts.jsonl  장기 보존
manifests/                   장기 보존
```

## PostgreSQL 저장소 규약

PostgreSQL은 checkpoint와 운영 metadata를 저장합니다.

### 현재 호환 checkpoint 규약

현재 구현은 checkpoint를 `job_id` primary key로 upsert하는 구조입니다.

공유 DB에서 현재 구조를 사용할 경우 필수 조건:

- `job_id`가 전역 고유해야 합니다.
- `job_id` 안에 `environment`와 `site_id`를 포함해야 합니다.
- 서로 다른 스크래퍼가 같은 `job_id`를 만들면 안 됩니다.

이 방식은 지금 바로 사용할 수 있지만, 장기적으로는 `(environment, site_id, job_id)` composite key를 갖는 공통 checkpoint table을 권장합니다.

### 목표 PostgreSQL schema

공유 DB에서는 전용 schema를 권장합니다.

```sql
create schema if not exists community_scraper;
```

이 schema 아래에 공통 table을 둡니다.

### `community_scraper.checkpoints`

목표 checkpoint table입니다.

```sql
create table if not exists community_scraper.checkpoints (
  environment text not null,
  site_id text not null,
  job_id text not null,
  updated_at timestamptz not null,
  status text not null,
  reason text null,
  worker_id text null,
  lease_until timestamptz null,
  checkpoint_json jsonb not null,
  primary key (environment, site_id, job_id)
);
```

권장 index:

```sql
create index if not exists checkpoints_updated_at_idx
on community_scraper.checkpoints (updated_at desc);

create index if not exists checkpoints_site_status_idx
on community_scraper.checkpoints (environment, site_id, status, updated_at desc);

create index if not exists checkpoints_lease_idx
on community_scraper.checkpoints (lease_until)
where lease_until is not null;
```

규칙:

- checkpoint 원본은 `checkpoint_json`에 보존합니다.
- 자주 조회하는 값은 별도 column으로 승격합니다.
- `checkpoint_json`은 community-specific field를 포함할 수 있습니다.
- resume은 `(environment, site_id, job_id)`로 조회합니다.
- 최신 checkpoint 조회는 environment와 site_id scope를 반드시 포함합니다.

금지:

```sql
select checkpoint_json
from community_scraper.checkpoints
order by updated_at desc
limit 1;
```

이 쿼리는 다른 site의 checkpoint를 잘못 가져올 수 있습니다.

권장:

```sql
select checkpoint_json
from community_scraper.checkpoints
where environment = $1
  and site_id = $2
order by updated_at desc
limit 1;
```

### `community_scraper.jobs`

장기 운영에서 권장하는 Job registry table입니다.

```sql
create table if not exists community_scraper.jobs (
  environment text not null,
  site_id text not null,
  job_id text not null,
  source_type text not null,
  status text not null,
  current_run_id text null,
  output_prefix text null,
  config_json jsonb not null,
  report_json jsonb null,
  created_at timestamptz not null,
  updated_at timestamptz not null,
  started_at timestamptz null,
  finished_at timestamptz null,
  primary key (environment, site_id, job_id)
);
```

용도:

- 운영 UI에서 Job 목록 표시
- 같은 Job 중복 실행 방지
- 현재 run 추적
- report summary 조회
- 스케줄러와 워커 간 계약

현재 구현에는 필수는 아닙니다. 여러 스크래퍼를 같은 운영 시스템에서 관리할 때 추가합니다.

### `community_scraper.runs`

장기 운영에서 권장하는 run registry table입니다.

```sql
create table if not exists community_scraper.runs (
  environment text not null,
  site_id text not null,
  job_id text not null,
  run_id text not null,
  status text not null,
  worker_id text null,
  output_prefix text not null,
  posts_object_key text null,
  failures_object_key text null,
  report_object_key text null,
  manifest_object_key text null,
  success_count integer null,
  failure_count integer null,
  deduped_count integer null,
  filtered_count integer null,
  started_at timestamptz not null,
  finished_at timestamptz null,
  updated_at timestamptz not null,
  primary key (environment, site_id, job_id, run_id)
);
```

용도:

- resume마다 새 run이 생기는 구조 추적
- 같은 Job의 여러 run 비교
- `report.json` 없는 비정상 종료 run 찾기
- S3 object key 빠른 조회

### `community_scraper.failures`

장기 운영에서 선택적으로 둘 수 있는 failure summary table입니다.

```sql
create table if not exists community_scraper.failures (
  environment text not null,
  site_id text not null,
  job_id text not null,
  run_id text not null,
  failure_id text not null,
  board_id text null,
  post_id text null,
  post_number bigint null,
  stage text not null,
  reason text not null,
  retryable boolean not null default false,
  failure_json jsonb not null,
  created_at timestamptz not null,
  primary key (environment, site_id, job_id, run_id, failure_id)
);
```

용도:

- 실패 게시글 재처리
- DLQ 도입
- parser 장애 추적
- site별 장애율 분석

현재는 `failures.jsonl`을 source of truth로 둡니다. 이 table은 운영 검색과 재처리를 위해 추가합니다. 실사이트 smoke test에서 `post title missing` 같은 parser-stage 실패가 재시도 시 회수되는 사례가 확인되었으므로, failure summary table을 도입하더라도 원본 `failures.jsonl`과 재처리 run의 관계를 추적할 수 있어야 합니다.

## Checkpoint 규칙

### 저장 시점

checkpoint는 아래 시점에 저장합니다.

- Job 시작
- 일정 개수의 게시글 처리 후
- 게시글 저장 성공 후
- 실패 기록 저장 후
- graceful stop
- CAPTCHA/차단 감지 후
- timeout 후
- 정상 완료 후

핵심 순서:

```text
post output 저장 성공
  -> checkpoint advance
```

checkpoint를 먼저 advance하면 결과 파일에 없는 게시글을 완료 처리할 수 있으므로 금지합니다.

### Resume 규칙

resume은 checkpoint를 기준으로 합니다.

규칙:

- 같은 `job_id`를 사용합니다.
- 새 `run_id`를 생성합니다.
- completed key는 skip합니다.
- remaining queue가 있으면 복원합니다.
- 이전 run output을 덮어쓰지 않습니다.
- S3에 `report.json`이 없어도 checkpoint가 있으면 resume할 수 있습니다.

### 최신 checkpoint 조회

공유 DB에서 `load_latest`는 위험합니다.

허용 조건:

- environment scope가 있어야 합니다.
- site_id scope가 있어야 합니다.
- 가능하면 source_type 또는 worker group scope도 둡니다.

권장:

```text
load_latest(environment, site_id)
```

비권장:

```text
load_latest()
```

이유:

- 다른 커뮤니티의 checkpoint를 잘못 resume할 수 있습니다.
- 개발 환경 Job을 운영 워커가 resume할 수 있습니다.
- 서로 다른 source_type Job이 섞일 수 있습니다.

현재 구현이 scope 없는 latest를 제공한다면 공유 저장소 운영에서는 `JOB_ID`를 명시하는 것을 원칙으로 합니다.

## Job 동시성 규칙

### 단일 writer 원칙

하나의 `(environment, site_id, job_id, run_id)`에는 하나의 writer만 존재합니다.

금지:

```text
worker-1 -> outputs/prod/site-a/job-1/run-1/posts.jsonl
worker-2 -> outputs/prod/site-a/job-1/run-1/posts.jsonl
```

허용:

```text
worker-1 -> outputs/prod/site-a/job-1/run-1/posts.jsonl
worker-2 -> outputs/prod/site-a/job-2/run-1/posts.jsonl
```

resume:

```text
worker-1 -> outputs/prod/site-a/job-1/run-1/posts.jsonl
worker-2 -> outputs/prod/site-a/job-1/run-2/posts.jsonl
```

### Lease 규칙

장기 운영에서는 checkpoint 또는 jobs table에 lease를 둡니다.

필드:

```text
worker_id
lease_until
```

규칙:

- worker는 Job 시작 시 lease를 획득합니다.
- 실행 중 주기적으로 lease를 갱신합니다.
- 다른 worker는 lease가 살아 있는 Job을 실행하지 않습니다.
- lease가 만료된 Job은 resume 대상이 될 수 있습니다.

현재 구현에 lease가 완전히 연결되지 않은 경우:

- 같은 `job_id`를 동시에 실행하지 않도록 스케줄러에서 막습니다.
- `JOB_ID`를 수동으로 재사용할 때는 기존 프로세스가 죽었는지 확인합니다.

## 권한 규약

### S3 권한

권장:

- 환경별 access key 분리
- 가능하면 site별 prefix 권한 분리
- writer와 reader 권한 분리
- 운영 writer key는 운영 worker에만 주입

Writer 최소 권한:

```text
PutObject
GetObject
ListBucket with prefix scope
```

Reader 최소 권한:

```text
GetObject
ListBucket with prefix scope
```

삭제 권한:

- 기본 worker에는 부여하지 않습니다.
- lifecycle 관리 또는 운영 관리자에게만 부여합니다.

### PostgreSQL 권한

권장 role:

```text
scraper_migrator
scraper_writer
scraper_reader
```

`scraper_migrator`:

- schema/table 생성
- migration 실행

`scraper_writer`:

- checkpoint upsert
- job/run row insert/update
- 필요한 select

`scraper_reader`:

- 운영 UI와 분석 조회

Worker에는 가능하면 `scraper_writer`만 부여합니다.

## Secret 규약

저장하면 안 되는 값:

- S3 secret key
- DB password
- Proxy password
- Cookie
- Authorization header
- signed URL token
- raw request header 전체

저장해도 되는 값:

- `site_id`
- `job_id`
- `run_id`
- safe proxy label
- user-agent hash 또는 redacted label
- HTTP status
- retryable 여부
- stage
- reason

Failure record와 checkpoint metadata에는 secret을 넣지 않습니다.

## 백업/복구 규약

### 백업 단위

반드시 함께 백업:

- S3 bucket 또는 prefix
- PostgreSQL checkpoint table
- Job/run registry table이 있다면 해당 table
- 운영 env/secret manager 설정
- User-Agent 파일

S3만 있고 PostgreSQL이 없으면 resume이 어렵습니다.

PostgreSQL만 있고 S3 output이 없으면 completed checkpoint와 실제 결과가 불일치할 수 있습니다.

### 복구 순서

1. PostgreSQL을 복구합니다.
2. S3 bucket/prefix를 복구합니다.
3. registry table이 있다면 job/run row를 확인합니다.
4. checkpoint의 `updated_at`, `status`, `reason`을 확인합니다.
5. 같은 `environment`, `site_id`, `job_id`로 resume합니다.
6. 새 `run_id`의 `report.json`을 확인합니다.

### 부분 복구

`posts.jsonl`은 있지만 checkpoint가 없을 때:

- 자동 resume은 어렵습니다.
- JSONL을 분석해 completed key를 재구성하는 별도 복구 도구가 필요합니다.

checkpoint는 있지만 `posts.jsonl`이 없을 때:

- checkpoint를 그대로 신뢰하면 데이터 누락이 발생할 수 있습니다.
- 해당 Job은 처음부터 다시 실행하거나 수동 복구합니다.

`report.json`만 없을 때:

- run이 비정상 종료되었을 가능성이 큽니다.
- checkpoint 기준으로 resume합니다.

## Retention 규약

권장 retention:

| 대상 | 권장 |
| --- | --- |
| 원본 posts JSONL | 장기 보존 |
| failures JSONL | 재처리 기간 이상 |
| report JSON | 장기 보존 |
| manifest JSON | 장기 보존 |
| checkpoint running/stopped | resume 가능 기간 동안 보존 |
| checkpoint completed | 검증 완료 후 일정 기간 보존 |
| media | 비용 정책에 따라 별도 보존 |
| tmp object | 7일 이하 |

삭제 전 확인:

- 해당 Job이 completed인지
- normalized table에 반영됐는지
- LLM/RAG 인덱스에 반영됐는지
- 재처리 가능 기간이 지났는지
- 백업이 존재하는지

## 정규화 저장소 규약

원본 저장과 정규화 저장은 분리합니다.

원본:

```text
outputs/...
```

정규화:

```text
normalized/<environment>/<schema_version>/<site_id>/<partition>/...
```

예:

```text
normalized/prod/community_common.posts.v1/site-a/date=2026-08-09/posts.parquet
normalized/prod/community_common.comments.v1/site-a/date=2026-08-09/comments.parquet
```

규칙:

- 원본 JSONL은 수정하지 않습니다.
- 정규화 결과는 재생성 가능해야 합니다.
- 정규화 table에는 `site_id`, `job_id`, `run_id`, `source_object_key`를 포함합니다.
- 댓글은 게시글과 분리합니다.
- content block과 media도 필요하면 별도 table로 분리합니다.

## LLM/RAG 사용 규약

LLM/RAG 입력에 원본 JSONL을 사용할 수 있습니다.

권장:

- 원본 JSONL을 바로 수정하지 않습니다.
- LLM 입력용 projection을 별도 생성합니다.
- 너무 큰 content는 chunking합니다.
- 개인정보와 민감정보 제거 단계를 둡니다.
- `site_id`, `post_id`, `source_object_key`를 metadata로 유지합니다.

권장 object prefix:

```text
exports/<environment>/llm/<site_id>/<job_id>/<run_id>/documents.jsonl
exports/<environment>/rag/<site_id>/<index_name>/<partition>/chunks.jsonl
```

## 운영 점검 쿼리

목표 schema 기준 예시입니다.

최근 checkpoint:

```sql
select environment, site_id, job_id, status, reason, updated_at
from community_scraper.checkpoints
where environment = 'prod'
order by updated_at desc
limit 50;
```

site별 running Job:

```sql
select environment, site_id, job_id, worker_id, lease_until, updated_at
from community_scraper.checkpoints
where environment = 'prod'
  and status = 'running'
order by updated_at desc;
```

멈춘 Job:

```sql
select environment, site_id, job_id, reason, updated_at
from community_scraper.checkpoints
where environment = 'prod'
  and status = 'stopped'
order by updated_at desc;
```

lease 만료 의심:

```sql
select environment, site_id, job_id, worker_id, lease_until
from community_scraper.checkpoints
where environment = 'prod'
  and lease_until is not null
  and lease_until < now();
```

## 장애 대응 규약

### Object key 충돌

증상:

- 서로 다른 Job 결과가 같은 `posts.jsonl`에 섞임
- report count와 JSONL row 수가 맞지 않음
- resume 시 completed key가 이상함

원인:

- `job_id`가 전역 고유하지 않음
- 같은 `run_id` 재사용
- 두 worker가 같은 Job을 동시에 실행

조치:

1. 해당 Job을 중단합니다.
2. S3 object key를 확인합니다.
3. checkpoint row를 확인합니다.
4. 충돌한 Job 결과는 수동 분리하거나 폐기합니다.
5. `job_id` 생성 규칙을 수정합니다.
6. scheduler에서 중복 실행 방지를 추가합니다.

### 다른 site checkpoint를 resume

증상:

- source config가 현재 worker와 맞지 않음
- parser validation 오류
- 이상한 board/post URL로 요청

원인:

- scope 없는 latest checkpoint 조회
- `JOB_ID` 미지정 resume

조치:

1. 공유 저장소 운영에서는 `JOB_ID` 명시를 원칙으로 합니다.
2. 목표 schema에서는 `load_latest(environment, site_id)`만 허용합니다.
3. 현재 구현에서는 `job_id` prefix로 site를 구분합니다.

### S3는 성공, checkpoint 실패

증상:

- `posts.jsonl`에는 row가 있음
- checkpoint는 이전 상태
- resume 시 이미 저장한 게시글을 다시 수집할 수 있음

조치:

1. 중복 가능성을 허용하고 resume합니다.
2. 분석 단계에서 `(site_id, board_id, post_id)`로 dedupe합니다.
3. checkpoint 장애 원인을 먼저 해결합니다.

### checkpoint는 성공, S3 누락

이 상태는 원칙적으로 발생하면 안 됩니다.

원인:

- checkpoint advance 순서 위반
- 수동 DB 수정
- S3 object 삭제

조치:

1. checkpoint를 그대로 신뢰하지 않습니다.
2. S3 object 존재 여부를 확인합니다.
3. Job을 처음부터 재실행하거나 수동으로 checkpoint를 되돌립니다.

## 구현 체크리스트

새 스크래퍼가 공유 저장소에 붙기 전 확인합니다.

식별자:

- [ ] `site_id` 확정
- [ ] `environment` 확정
- [ ] `job_id` 생성 규칙에 environment 포함
- [ ] `job_id` 생성 규칙에 site_id 포함
- [ ] `run_id`가 resume마다 새로 생성됨
- [ ] dedupe key가 `(site_id, board_id, post_id)` 기준

S3:

- [ ] bucket 또는 prefix가 환경별로 분리됨
- [ ] object key가 표준 구조를 따름
- [ ] `posts.jsonl` content type이 `application/x-ndjson`
- [ ] `failures.jsonl` content type이 `application/x-ndjson`
- [ ] `report.json` content type이 `application/json`
- [ ] media key에 secret이 들어가지 않음
- [ ] lifecycle 정책이 정해짐

PostgreSQL:

- [ ] checkpoint key 충돌 방지 방식이 있음
- [ ] 공유 DB에서 `JOB_ID` 명시 resume을 사용함
- [ ] 목표 schema 전환 계획이 있음
- [ ] writer role 권한이 최소화됨
- [ ] backup 대상에 checkpoint table이 포함됨

운영:

- [ ] 같은 `job_id` 동시 실행 방지
- [ ] exit code 알림 설정
- [ ] stopped/failed checkpoint 알림 설정
- [ ] `report.json` 누락 감지
- [ ] S3와 PostgreSQL 백업이 같은 시점 기준으로 관리됨

## Migration 계획

### Phase 1. 현재 호환 공유

목표:

- 기존 저장소 어댑터 변경 없이 공유 bucket/DB 사용

필수:

- `job_id` 전역 고유화
- `JOB_ID` 명시 resume
- 환경별 bucket 또는 prefix 분리
- site별 운영 문서 작성

### Phase 2. Prefix 확장

목표:

- object key에 `environment/site_id` prefix 추가

변경:

- storage config에 `environment`
- storage config에 `site_id`
- `OutputRunLayout`에서 목표 key 지원
- 기존 key와 새 key를 모두 읽을 수 있는 migration helper

### Phase 3. 공통 PostgreSQL schema

목표:

- `(environment, site_id, job_id)` primary key 사용
- Job/run registry table 도입

변경:

- checkpoint store table configurable
- scoped `load_latest(environment, site_id)` 도입
- jobs/runs registry writer 도입

### Phase 4. 공통 운영 플랫폼

목표:

- 여러 스크래퍼의 Job 실행, 상태, 결과, 실패 재처리를 한 곳에서 관리

추가:

- 공통 Job queue
- DLQ/retry unit
- 공통 dashboard
- 정규화 파이프라인
- LLM/RAG export pipeline

## 관련 문서

- 프로젝트 README: `README.md`
- 배포/운영 가이드: `docs/Deployment_Operations.md`
- 커뮤니티 스크래퍼 표준 구조/기능 계승 가이드: `docs/Cross_Community_Scraper_Inheritance_Guide.md`
- 기능 명세서: `docs/Function_Specification.md`
