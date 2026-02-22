# ☁️ AWS 배포 빠른 시작 (30분)

이 가이드를 따라 AWS AgentCore에 Agent를 배포합니다.
CDK가 Docker 빌드 → ECR 푸시 → Runtime 생성을 자동으로 처리합니다.

## 사전 요구사항

- AWS 계정 (관리자 권한 권장)
- AWS CLI 설정 완료 (`aws configure`)
- Node.js 18+ (CDK용)
- Docker 실행 중
- Bedrock Claude 모델 접근 활성화 (AWS 콘솔 → Bedrock → Model access)

## 아키텍처 개요

```
┌─ AIOpsInfrastructure Stack ─────────────────────────────┐
│  ECR (컨테이너) │ KMS (암호화) │ S3 (KB) │ DynamoDB    │
│  S3 Vectors + Bedrock KB (자동 생성)                    │
│  SQS + Lambda (KB 자동 Sync 파이프라인)                 │
└─────────────────────────────────────────────────────────┘
┌─ AIOpsAgentCore Stack ──────────────────────────────────┐
│  AgentCore Runtime (Supervisor Agent, ARM64 컨테이너)   │
│  AgentCore Memory (대화 컨텍스트)                       │
└─────────────────────────────────────────────────────────┘
```

---

## Step 1: 저장소 클론 (1분)

```bash
git clone https://github.com/hcsung-aws/ai-agent-automation-platform.git
cd ai-agent-automation-platform
```

## Step 2: 배포 (15분)

```bash
cd templates/aws
./deploy.sh
```

deploy.sh가 자동으로 수행하는 작업:
1. AWS 자격증명 확인
2. CDK 설치 확인
3. Python 의존성 설치
4. CDK Bootstrap (최초 1회)
5. **2개 스택 배포** (Infrastructure + AgentCore)
   - Docker 이미지 빌드 (ARM64) → ECR 푸시 → Runtime 생성 포함

### 커스텀 Agent 배포

기본 template 대신 별도 프로젝트를 배포할 때:

```bash
./deploy.sh /path/to/my-project
```

프로젝트 구조 요구사항:
```
my-project/
├── config.py             ← 필수 (MODEL_ID, REGION_NAME)
├── agents/
│   ├── Dockerfile        ← 필수
│   ├── main.py           ← 필수 (AgentCore HTTP 엔트리포인트)
│   ├── supervisor.py     ← 필수
│   └── requirements.txt  ← 필수
└── .dockerignore         ← 권장
```

## Step 3: KB 동기화 (선택, 5분)

CDK가 Bedrock Knowledge Base를 자동 생성합니다. KB 문서를 S3에 동기화하면 자동 Sync 파이프라인이 ingestion을 실행합니다.

```bash
# KB S3 버킷 확인
KB_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name AIOpsInfrastructure \
  --query "Stacks[0].Outputs[?OutputKey=='KBBucketName'].OutputValue" \
  --output text)

# 로컬 KB를 S3에 동기화
aws s3 sync knowledge-base/ s3://$KB_BUCKET/knowledge-base/
# → 자동 Sync: S3 이벤트 → SQS → Lambda → StartIngestionJob
```

이후 문서를 추가할 때도 S3에 업로드만 하면 자동으로 ingestion이 실행됩니다.

## Step 4: 배포 검증 (5분)

```bash
REGION=us-east-1
STACK_PREFIX=AIOps

# 1. Runtime ID 확인
RUNTIME_ID=$(aws bedrock-agentcore list-agent-runtimes \
  --query "agentRuntimeSummaries[?agentRuntimeName=='aiops_supervisor'].agentRuntimeId" \
  --output text --region $REGION)
echo "Runtime ID: $RUNTIME_ID"

# 2. Runtime 상태 확인 (ACTIVE면 정상)
aws bedrock-agentcore get-agent-runtime \
  --agent-runtime-id $RUNTIME_ID --region $REGION \
  --query '{Status: agentRuntimeStatus, Name: agentRuntimeName}'

# 3. 테스트 호출
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-id $RUNTIME_ID --region $REGION \
  --runtime-session-id $(python3 -c "import uuid; print(str(uuid.uuid4()))") \
  --payload '{"prompt": "안녕하세요"}' /dev/stdout
```

---

## Knowledge Base (자동 생성)

CDK 배포 시 다음이 자동으로 생성됩니다:
- **S3 Vectors** 벡터 스토어 (Titan V2 Embeddings, 1024 dim)
- **Bedrock Knowledge Base** + DataSource (S3 연결)
- **자동 Sync 파이프라인** (S3 PUT → SQS → Lambda → StartIngestionJob)

Agent의 `KNOWLEDGE_BASE_ID` 환경변수도 자동 설정되므로, 별도 KB 생성 작업은 불필요합니다.

### 문서 추가

```bash
# S3에 업로드만 하면 자동 ingestion
aws s3 cp my-doc.md s3://$KB_BUCKET/knowledge-base/devops/
```

---

## 새 Agent 추가 후 재배포

1. `templates/local/agents/`에 새 agent 파일 생성
2. `supervisor.py`에 연결
3. `requirements.txt`에 새 패키지 추가 (필요 시)
4. 재배포:
   ```bash
   cd templates/aws && ./deploy.sh
   ```

CDK가 변경을 감지하여 자동으로 Docker 재빌드 → ECR 푸시 → Runtime 업데이트합니다.

---

## 환경 변수 커스터마이징

`agentcore_stack.py`의 `environment_variables`에서 설정:

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `KNOWLEDGE_BASE_ID` | Bedrock KB ID | (CDK 자동 설정) |
| `KB_S3_BUCKET` | KB S3 버킷 | (자동 설정) |
| `KB_S3_PREFIX` | S3 내 KB 경로 | `knowledge-base` |
| `FEEDBACK_STORAGE` | 피드백 저장소 | `dynamodb` |
| `FEEDBACK_TABLE` | DynamoDB 테이블명 | (자동 설정) |

---

## 보안 원칙

| 원칙 | 구현 |
|------|------|
| 최소 권한 | IAM 역할에 필요한 권한만 부여 |
| 암호화 | KMS로 저장 데이터 암호화 |
| 로깅 | CloudWatch Logs (KMS 암호화, 1개월 보관) |
| 컨테이너 보안 | ECR 이미지 스캔 활성화 |

## 비용 예상

| 서비스 | 예상 비용 (월) |
|--------|---------------|
| AgentCore Runtime | 사용량 기반 |
| Bedrock Claude 3.5 | ~$3/1M 토큰 |
| S3 (KB) | ~$0.023/GB |
| ECR | ~$0.10/GB |
| DynamoDB (피드백) | 프리티어 내 |

자세한 비용 예측은 [AWS Pricing Calculator](https://calculator.aws)를 참고하세요.

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| CDK Bootstrap 실패 | 권한 부족 | 관리자 권한으로 `cdk bootstrap` |
| Docker 빌드 실패 (ARM64) | buildx 미설정 | `docker buildx create --use` |
| Bedrock 모델 접근 오류 | 모델 미활성화 | 콘솔 → Bedrock → Model access |
| AccessDeniedException | inference-profile 누락 | CDK 스택에 이미 포함 (재배포) |
| Runtime FAILED | 컨테이너 에러 | CloudWatch Logs 확인 |
| config import 에러 | config.py 누락 | build context가 local/인지 확인 |

### 로그 확인

```bash
# 최근 로그
aws logs filter-log-events \
  --log-group-name "/aws/bedrock-agentcore/runtimes/${RUNTIME_ID}-DEFAULT" \
  --start-time $(($(date +%s) - 3600))000 --limit 30 --region $REGION

# 에러만
aws logs filter-log-events \
  --log-group-name "/aws/bedrock-agentcore/runtimes/${RUNTIME_ID}-DEFAULT" \
  --filter-pattern "ERROR" --limit 20 --region $REGION
```

---

## 다음 단계

1. **Agent Builder로 새 Agent 생성**: `kiro chat --agent agent-builder`
2. **KB 문서 추가**: S3에 .md 파일 업로드 → 자동 ingestion
3. **피드백 수집**: DynamoDB에 자동 저장되는 👍/👎 피드백 활용

---

**이전:** [로컬 배포 가이드](QUICKSTART-LOCAL.md)
