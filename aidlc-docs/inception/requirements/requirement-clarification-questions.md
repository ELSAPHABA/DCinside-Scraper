# Requirement Clarification Questions

기존 답변은 모두 확인했습니다. 아래 항목은 선택지 문자 없이 설명으로 답한 항목, 또는 활성화한 확장 규칙과 충돌하는 항목만 정리한 추가 질문입니다.

각 질문의 `[Answer]:` 뒤에 선택지 문자만 적어 주세요. 선택지가 맞지 않으면 마지막 `X) 기타`를 고르고 설명을 적어 주세요.

## Question 1
Q7 디시콘 수집 방식은 최종적으로 어떻게 확정할까요?

A) Job 실행 전 터미널 옵션으로 선택하게 하고, 선택에 따라 메타데이터만 저장하거나 파일까지 다운로드

B) 항상 디시콘 이미지/영상 URL과 alt/title/conalt 메타데이터만 저장

C) 항상 디시콘 파일까지 다운로드

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A

## Question 2
Q9 이미지 저장 구조는 최종적으로 어떻게 확정할까요?

A) Job 실행 전 터미널 옵션으로 선택하게 하고, 선택에 따라 URL만 저장하거나 `images/<gallery_id>/<post_no>/` 아래에 저장

B) 항상 URL만 저장

C) 항상 `images/<gallery_id>/<post_no>/` 아래에 저장

D) 항상 `images/<job_id>/<gallery_id>/<post_no>/` 아래에 저장

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
Q14 Proxy 설정은 `Proxy-Profile.txt`가 있을 때 자동 사용해야 하나요?

A) 기본 비활성화. `Proxy-Profile.txt`가 있어도 사용자가 Proxy 옵션을 켠 경우에만 사용

B) `Proxy-Profile.txt`가 있으면 자동 사용하고, 없으면 Proxy 비활성화

C) 실행할 때마다 Proxy 사용 여부를 터미널에서 확인

X) 기타 (please describe after [Answer]: tag below)

[Answer]: B

[Superseded/Delta 2026-08-05]: 최신 Proxy 저장 방식은 `Proxy-Profile.txt`가 아니라 실행 파일과 같은 위치의 평문 `.env`입니다. 사용자가 Proxy 옵션을 켠 경우 우선 적용하고, 옵션이 없더라도 `.env`가 있으면 자동 사용합니다.

## Question 4
Security Baseline을 적용하면 Proxy ID/PW 평문 저장은 보안 예외가 됩니다. 어떻게 처리할까요?

A) 보안 우선. `Proxy-Profile.txt`에는 host만 저장하고 ID/PW는 실행 시 터미널에서 입력

B) 편집 편의 우선. `Proxy-Profile.txt`에 host/ID/PW를 평문 저장하되 `.gitignore` 포함과 터미널 경고를 필수로 함

C) 인증 Proxy는 1차 구현에서 제외

X) 기타 (please describe after [Answer]: tag below)

[Answer]: B

[Superseded/Delta 2026-08-05]: 평문 저장 예외는 유지하되 저장 대상은 `Proxy-Profile.txt`가 아니라 `.env`입니다. 환경 변수명은 `DCINSIDE_PROXY_HOST`, `DCINSIDE_PROXY_ID`, `DCINSIDE_PROXY_PW`를 사용합니다.

## Question 5
Q19 테스트 기준은 PBT 확장 규칙 적용 답변과 충돌합니다. 최종 테스트 기준은 무엇인가요?

A) fixture 기반 파싱 테스트 + Hypothesis PBT + 선택적 live smoke test

B) 수동 live smoke test만 사용하고 PBT 확장은 비활성화

C) fixture 기반 파싱 테스트 + 선택적 live smoke test만 사용하고 PBT 확장은 비활성화

D) Hypothesis PBT는 JSON 직렬화와 순수 파서 함수에만 부분 적용

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A

## Question 6
Resiliency Baseline 적용을 위해 RTO/RPO와 DR 전략을 정해야 합니다. 목표는 무엇인가요?

A) RPO/RTO: 수 시간. Backup & Restore 전략

B) RPO/RTO: 수십 분. Pilot Light 전략

C) RPO/RTO: 수 분. Warm Standby 전략

D) RPO/RTO: 거의 실시간. Multi-site Active/Active 전략

E) 단일 리전 또는 로컬 실행으로 충분. 별도 DR 불필요

X) 기타 (please describe after [Answer]: tag below)

[Answer]: E

## Question 7
운영 변경 관리는 어떻게 할까요?

A) 기존 조직의 변경 관리 프로세스를 사용

B) 아직 formal process가 없으므로 lightweight change record + approval + rollback note를 사용

C) 개인/내부 도구이므로 formal change management는 제외하고 사유만 문서화

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A

## Question 8
CI/CD는 어떻게 구성할까요?

A) 기존 CI/CD 파이프라인을 사용

B) GitHub Actions 기반으로 새 파이프라인을 작성

C) 1차 구현에서는 로컬 실행/테스트 명령만 문서화하고 CI/CD는 제외

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A

## Question 9
배포 실패 시 rollback 방식은 무엇으로 할까요?

A) 이전 Git tag 또는 이전 컨테이너 이미지 버전 재배포

B) blue/green 환경 전환

C) canary 배포 후 health/metric 이상 시 자동 rollback

D) 1차 구현에서는 배포하지 않으므로 rollback은 문서화만 함

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A

## Question 10
배포 전략은 무엇으로 할까요?

A) 직접 배포 또는 컨테이너 재시작

B) rolling 배포

C) blue/green 배포

D) canary 배포

E) 1차 구현에서는 배포하지 않고 로컬/컨테이너 실행까지만 지원

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A

## Question 11
지역/가용성 구성은 어떻게 할까요?

A) 로컬 실행과 단일 컨테이너 실행만 지원

B) 단일 리전, 다중 가용 영역 배포를 목표로 문서화

C) 멀티 리전 active-passive 배포를 목표로 문서화

D) 멀티 리전 active-active 배포를 목표로 문서화

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A, 차후 멀티 리전 active-passive 배포를 목표로 문서화

## Question 12
장애 대응 프로세스는 어떻게 할까요?

A) 기존 조직의 incident response 프로세스를 사용

B) formal process가 없으므로 lightweight incident log + 원인 분석 + 재발 방지 항목을 사용

C) 개인/내부 도구이므로 별도 incident response는 제외하고 오류 로그만 저장

X) 기타 (please describe after [Answer]: tag below)

[Answer]: A
