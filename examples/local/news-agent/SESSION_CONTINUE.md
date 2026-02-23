# 세션 이어하기 가이드 (2026-02-23 22:38 기준)

## 완료된 작업

### 보안 알림 해소
- ALB를 Public → Internal로 전환하여 DyePack 보안 알림 해소
- `deploy/stack.py`: `public_load_balancer=False`, ECS Exec 활성화, S3 피드백 버킷 추가
- `cdk diff` 결과: CDK 코드와 배포된 인프라 완전 일치 확인

### Docker Desktop 로그인 충돌 해결
- 원인: `credsStore: desktop.exe`에서 ECR `docker login` 시 IPC 타임아웃 → Docker Desktop 세션 무효화
- 해결: `ecr-login-wrapper` credential helper 생성 (store를 no-op 처리)
- `~/.docker/config.json`에 `credHelpers` 설정 적용

### 피드백 S3 저장
- `feedback_store.py`에 S3 저장 방식 추가 (`FEEDBACK_STORAGE=s3`)
- `stack.py`에 S3 버킷 생성 + 환경변수/권한 설정
- E2E 테스트 완료: positive 1건, negative 1건 S3 저장 확인
- 버킷: `newsagentstack-feedbackbucket5ec91a3b-tcncjhkvsems`

### 최종 정리 TODO (ID: 1771852947246) - 3/6 완료
- [x] CDK 코드와 배포된 인프라 상태 비교 → 일치 확인
- [x] SSM 접속 스크립트 생성 (`deploy/connect.sh` + `connect.ps1`)
- [x] AWS 배포 매뉴얼 작성 (`deploy/DEPLOY_GUIDE.md`)
- [ ] 배포된 Agent 아키텍처 확인 → README 다이어그램 정합성 검증/수정
- [ ] README 아키텍처 다이어그램 개선 (로컬 + AWS 모두)
- [ ] README에 AWS 배포 가이드 링크/설명 반영

## 미해결 핵심 이슈: AgentCore vs ECS Fargate

### 현재 상태
- 실제 배포: **ECS Fargate + Internal ALB + Chainlit UI** (`deploy/stack.py`)
- README 다이어그램: **AgentCore** 아키텍처로 되어 있음 → 불일치
- `templates/aws/` 에 AgentCore CDK 스택이 별도로 존재하지만 사용하지 않음

### 불일치 원인
- AgentCore는 API 전용 (`POST /invocations` on :8080) → Chainlit 웹 UI 서빙 불가
- news-agent는 Chainlit UI (`app.py` on :8000)를 포함한 데모용 배포
- 두 Dockerfile이 다름: AgentCore용 (ARM64, main.py) vs 현재 배포용 (x86, app.py)

### 결정 필요 사항

**방안 A: AgentCore 배포 (복잡도 높음)**
- 프론트엔드(Chainlit/ECS) + 백엔드(AgentCore API) 분리 필요
- Bedrock KB + AgentCore Memory 활용 가능
- 작업: AgentCore 스택 수정, app.py를 API 클라이언트로 변경, KB 설정

**방안 B: 현재 ECS Fargate 유지 + KB 강화 (권장, 복잡도 낮음)**
- 현재 구조에 Bedrock KB만 추가
- CDK에 Bedrock KB 리소스 추가 + `KNOWLEDGE_BASE_ID` 환경변수 설정
- guide_agent.py의 KB 폴백 체인이 자동 동작

→ 사용자가 방향 결정 후 진행 예정

## 남은 작업 (방향 결정 후)

1. README 아키텍처 다이어그램을 실제 배포 구조에 맞게 수정
   - 로컬: Supervisor → News Agent, News Analysis Agent, Guide Agent, save_case
   - AWS: 결정된 방안에 따라 (ECS Fargate 또는 AgentCore)
2. 다이어그램 텍스트 줄맞춤 개선 (폰트 독립적인 형식으로)
3. README에 AWS 배포 가이드 링크 반영
4. (방안 B 선택 시) Bedrock KB CDK 리소스 추가

## 현재 배포 정보

- 리전: us-west-2
- 계정: 965037532757
- 스택: NewsAgentStack
- 클러스터: NewsAgentStack-ClusterEB0386A7-6hm52qzDhS48
- Internal ALB: internal-NewsAg-Servi-70Y0JT54SjZi-1967236828.us-west-2.elb.amazonaws.com
- VPC: vpc-04fac64c8bfc5d60f
- S3 피드백 버킷: newsagentstack-feedbackbucket5ec91a3b-tcncjhkvsems

## SSM 접속 방법 (Windows PowerShell)

```powershell
# 스크립트 사용
.\deploy\connect.ps1

# 또는 수동 (태스크 재배포 시 target 값 변경됨)
# connect.ps1이 자동으로 최신 target을 조회합니다
```

## 수정된 파일 목록

- `deploy/stack.py` - Internal ALB + ECS Exec + S3 피드백 버킷
- `feedback_store.py` - S3 저장 방식 추가
- `deploy/connect.sh` - SSM 포트포워딩 스크립트 (Bash)
- `deploy/connect.ps1` - SSM 포트포워딩 스크립트 (PowerShell)
- `deploy/DEPLOY_GUIDE.md` - AWS 배포 매뉴얼
- `deploy/ACCESS_GUIDE.md` - SSM 접속 가이드 (이전 버전, DEPLOY_GUIDE.md로 통합됨)
- `~/.docker/config.json` - ECR credential helper 설정
