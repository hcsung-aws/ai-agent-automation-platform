# News Agent AWS 배포 가이드

로컬에서 개발한 News Agent를 AWS에 배포하고 확인하는 전체 플로우입니다.

## 사전 준비

- AWS CLI v2 + 자격 증명 설정
- Docker Desktop (로그인 완료)
- AWS CDK v2 (`npm install -g aws-cdk`)
- Session Manager 플러그인 ([설치](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html))
- Python 3.12+

## 1단계: 로컬 테스트

```bash
cd examples/local/news-agent
source .venv/bin/activate   # 또는 python -m venv .venv && pip install -r deploy/requirements.txt
chainlit run app.py --port 8000
```

http://localhost:8000 에서 동작 확인 후 다음 단계로 진행합니다.

## 2단계: CDK 배포

```bash
cd deploy

# CDK 부트스트랩 (최초 1회)
cdk bootstrap

# 배포
cdk deploy --require-approval never
```

배포 완료 시 출력값:
```
NewsAgentStack.InternalURL = http://internal-NewsAg-...elb.amazonaws.com
NewsAgentStack.VpcId = vpc-0xxxxxxxxx
NewsAgentStack.FeedbackBucketName = newsagentstack-feedbackbucket-xxxxx
```

### Docker Desktop 로그인 문제 시

WSL에서 ECR push 시 Docker Desktop 로그인이 깨지는 경우, ECR credential helper를 설정합니다:

```bash
# 설치
sudo apt-get install -y amazon-ecr-credential-helper

# ~/.docker/config.json 설정
{
    "credsStore": "desktop.exe",
    "credHelpers": {
        "<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com": "ecr-login-wrapper",
        "public.ecr.aws": "ecr-login-wrapper"
    }
}
```

`ecr-login-wrapper`는 `docker login`의 store 명령을 no-op으로 처리하는 래퍼입니다.

## 3단계: 접속 확인

ALB가 Internal이므로 SSM 포트포워딩으로 접속합니다.

### 방법 A: 스크립트 사용 (권장)

```bash
# Bash (WSL/Linux/Mac) - Session Manager 플러그인 필요
./deploy/connect.sh

# PowerShell (Windows)
.\deploy\connect.ps1
```

### 방법 B: 수동 실행

```powershell
# 1. 태스크 정보 조회
$Cluster = aws ecs list-clusters --query "clusterArns[?contains(@,'NewsAgent')]|[0]" --output text --region us-west-2
$TaskArn = aws ecs list-tasks --cluster $Cluster --query "taskArns[0]" --output text --region us-west-2
$TaskId = ($TaskArn -split "/")[-1]
$ClusterName = ($Cluster -split "/")[-1]
$RuntimeId = aws ecs describe-tasks --cluster $Cluster --tasks $TaskArn --query "tasks[0].containers[0].runtimeId" --output text --region us-west-2

# 2. 포트포워딩
aws ssm start-session `
  --target "ecs:${ClusterName}_${TaskId}_${RuntimeId}" `
  --document-name AWS-StartPortForwardingSessionToRemoteHost `
  --parameters '{\"host\":[\"<InternalURL의 호스트명>\"],\"portNumber\":[\"80\"],\"localPortNumber\":[\"8080\"]}' `
  --region us-west-2
```

브라우저에서 http://localhost:8080 접속

## 4단계: E2E 테스트

1. 챗봇에 질문: "오늘 뉴스 검색해줘"
2. 응답 확인 후 👍/👎 피드백 남기기
3. S3에 피드백 저장 확인:

```bash
aws s3 ls s3://<FeedbackBucketName>/feedback/ --region us-west-2
```

## 5단계: 정리 (선택)

```bash
cd deploy
cdk destroy
```

모든 리소스(VPC, ECS, ALB, S3 등)가 삭제됩니다.

## 배포 아키텍처

```
┌─ NewsAgentStack ──────────────────────────────┐
│                                               │
│  VPC (Public + Private Subnets, NAT GW)       │
│                                               │
│  ┌─ Private Subnet ────────────────────────┐  │
│  │                                         │  │
│  │  Internal ALB (:80)                     │  │
│  │       │                                 │  │
│  │  ECS Fargate (Chainlit :8000)           │  │
│  │    ├── Supervisor Agent                 │  │
│  │    │     ├── News Agent                 │  │
│  │    │     ├── News Analysis Agent        │  │
│  │    │     ├── Guide Agent                │  │
│  │    │     └── MCP Agent                  │  │
│  │    ├── ECS Exec (SSM) 활성화           │  │
│  │    └── → Amazon Bedrock (us-east-1)     │  │
│  │                                         │  │
│  └─────────────────────────────────────────┘  │
│                                               │
│  S3 Bucket (피드백 저장)                      │
│  CloudWatch Logs (3일 보관)                   │
│                                               │
│  접속: SSM 포트포워딩 → localhost:8080        │
└───────────────────────────────────────────────┘
```

## 트러블슈팅

| 증상 | 해결 |
|------|------|
| `TargetNotConnected` | ECS 서비스 강제 재배포: `aws ecs update-service --cluster <cluster> --service <service> --enable-execute-command --force-new-deployment --region us-west-2` |
| `SessionManagerPlugin not found` | Session Manager 플러그인 설치 필요 (Windows: .exe 설치, Linux: apt/yum) |
| PowerShell JSON 파싱 에러 | `'{\"key\":[\"value\"]}'` 형식으로 백슬래시 이스케이프 |
| Docker push 실패 | Docker Desktop 로그인 확인 + ECR credential helper 설정 |
| Target Group 충돌 | `cdk destroy` 후 `cdk deploy`로 클린 재배포 |
