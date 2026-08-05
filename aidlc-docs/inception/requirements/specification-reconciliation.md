# Specification Reconciliation

**Timestamp**: 2026-08-05T11:03:45Z

기능 명세서 수정으로 기존 승인 질문지 일부 답변이 낡았습니다. AI-DLC는 롤백하지 않고, 기존 승인 이력은 보존한 상태에서 아래 델타를 최신 결정으로 적용합니다.

## Source Of Truth

- 최신 기능 기준: `docs/Function_Specification.md`
- 기존 질문지 답변은 감사 이력으로 유지
- 이후 Application Design부터는 이 문서의 델타를 함께 적용

## Superseded Answers

- Requirements Verification Q3: 기존 1차 수집 진입점은 직접 URL, 갤러리 내 검색, 통합 검색이었으나, 최신 범위는 노키워드 기간/글번호 범위 수집, 심층검색, 실시간 키워드 수집, 실시간 전체 수집을 포함한다.
- Requirements Verification Q10: 기존 중단점 저장은 작업 중단/오류/CAPTCHA 중심이었으나, 최신 정책은 게시글 10개 저장마다 checkpoint를 저장하고 수동 중단, 오류, CAPTCHA 감지 시 즉시 최종 checkpoint를 저장한다.
- Requirements Verification Q13: 기존 User-Agent 파일명은 `User-Agent.txt`였으나, 최신 파일명은 `user-agents.txt`다. 한 줄에 하나의 User-Agent를 저장하고, 빈 줄은 무시하며, 기본 교체 주기는 요청 10회마다 1회다. 컨테이너 이미지에는 해당 txt 파일을 포함한다.
- Requirements Verification Q14, Requirement Clarification Q3/Q4: 기존 Proxy 저장 파일은 `Proxy-Profile.txt`였으나, 최신 저장 방식은 실행 파일과 같은 위치의 평문 `.env`다. 사용자가 Proxy 옵션을 켠 경우 우선 적용하고, 옵션이 없더라도 `.env`가 있으면 자동 사용한다.
- Container storage: 기존 컨테이너 JSONL 저장소 후보였던 MinIO는 Garage 기반 S3 호환 오브젝트 스토리지로 대체한다. SeaweedFS는 대량 미디어/소파일 저장, FUSE, Iceberg 요구가 생길 때 대체 저장소로 검토한다.

## Added Functional Scope

- FR-029: 노키워드 기간 및 글번호 범위 스크래핑
- FR-030: 실시간 키워드 및 실시간 전체 스크래핑
- FR-031: 심층검색
- US-006A: 기간/글번호 범위 기반 노키워드 수집
- US-006B: 통합검색 120페이지 제한을 우회하기 위한 심층검색

## Resume Decision

- Requirements, User Stories, Workflow Planning 문서는 최신 명세 변경을 반영한 것으로 본다.
- Application Design 질문지는 최신 델타를 기준으로 답변 검증을 재개한다.
- 빈 답변이 남은 설계 질문은 별도 확정 후 다음 AI-DLC 단계로 진행한다.
