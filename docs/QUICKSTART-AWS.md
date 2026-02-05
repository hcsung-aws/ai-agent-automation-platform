# ☁️ AWS 배포 빠른 시작 (30분)

이 가이드를 따라 AWS에 AgentCore 기반 AIOps 환경을 배포합니다.

## 사전 요구사항

- AWS 계정 (관리자 권한 권장)
- AWS CLI 설정 완료
- Node.js 18+ (CDK용)
- Docker (컨테이너 빌드용)

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Cloud                            │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  AgentCore      │  │  AgentCore      │                  │
│  │  Runtime        │──│  Gateway        │                  │
│  │  (Agent 호스팅) │  │  (도구 연결)    │                  │
│  └────────┬────────┘  └────────┬────────┘                  │
│           │                    │                            │
│  ┌────────▼────────┐  ┌────────▼────────┐                  │
│  │  AgentCore      │  │  Lambda         │                  │
│  │  Memory         │  │  (도구 구현)    │                  │
│  │  (컨텍스트)     │  │                 │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  ECR            │  │  KMS            │                  │
│  │  (컨테이너)     │  │  (암호화)       │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## 1단계: 저장소 클론 (1분)

```bash
git clone https://github.com/your-org/aiops-starter-kit.git
cd aiops-starter-kit/templates/aws
```

## 2단계: 배포 스크립트 실행 (10분)

```bash
./deploy.sh
```

배포 스크립트가 자동으로:
1. AWS 자격증명 확인
2. CDK Bootstrap (최초 1회)
3. 인프라 스택 배포 (ECR, IAM, KMS)
4. AgentCore 스택 배포 (Memory, Gateway)

## 3단계: Agent 컨테이너 빌드 및 푸시 (5분)

```bash
# 환경 변수 설정
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1

# 로컬 템플릿으로 컨테이너 빌드
cd ../local
docker build -t aiops-agent .

# ECR 로그인
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# 태그 및 푸시
docker tag aiops-agent:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/aiops-agents:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/aiops-agents:latest
```

## 4단계: AgentCore Runtime 생성 (10분)

```bash
# Agent 생성
aws bedrock create-agent \
  --agent-name aiops-supervisor \
  --agent-resource-role-arn arn:aws:iam::$ACCOUNT_ID:role/AIOpsInfrastructure-AgentCoreRole \
  --foundation-model anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --instruction "당신은 AI Agent 팀의 Supervisor입니다. 사용자 요청을 분석하여 적절한 Agent에게 위임합니다."

# Agent ID 확인
AGENT_ID=$(aws bedrock list-agents --query "agentSummaries[?agentName=='aiops-supervisor'].agentId" --output text)
echo "Agent ID: $AGENT_ID"
```

## 5단계: Gateway에 도구 연결 (5분)

```bash
# 도구 Lambda ARN 확인
TOOL_LAMBDA_ARN=$(aws cloudformation describe-stacks \
  --stack-name AIOpsAgentCore \
  --query "Stacks[0].Outputs[?OutputKey=='ToolLambdaArn'].OutputValue" \
  --output text)

# Action Group 생성
aws bedrock create-agent-action-group \
  --agent-id $AGENT_ID \
  --agent-version DRAFT \
  --action-group-name tools \
  --action-group-executor lambdaArn=$TOOL_LAMBDA_ARN \
  --api-schema '{"type": "FUNCTION_SCHEMA", "functions": [{"name": "echo", "description": "메시지 반환", "parameters": {"message": {"type": "string", "description": "반환할 메시지"}}}]}'
```

## 6단계: Agent 준비 및 테스트

```bash
# Agent 준비
aws bedrock prepare-agent --agent-id $AGENT_ID

# 테스트
aws bedrock-agent-runtime invoke-agent \
  --agent-id $AGENT_ID \
  --agent-alias-id TSTALIASID \
  --session-id test-session \
  --input-text "안녕하세요"
```

---

## 7단계: Knowledge Base 생성 (선택)

> ⚠️ **주의**: Bedrock Knowledge Base는 CDK/CloudFormation으로 완전 자동화가 어렵습니다.
> 데이터 소스 동기화, 임베딩 모델 설정 등 수동 단계가 필요합니다.

Agent가 문서를 검색하여 답변하려면 Knowledge Base를 생성해야 합니다.

### 7-1. S3에 문서 업로드

```bash
# 문서용 S3 버킷 생성
aws s3 mb s3://aiops-kb-docs-$ACCOUNT_ID-$REGION

# 문서 업로드 (예: docs 폴더)
aws s3 sync ./docs s3://aiops-kb-docs-$ACCOUNT_ID-$REGION/docs/
```

### 7-2. Knowledge Base 생성 (콘솔)

AWS 콘솔에서 생성하는 것이 가장 안정적입니다:

1. **Bedrock 콘솔** → Knowledge bases → Create
2. **이름**: `aiops-knowledge-base`
3. **IAM 역할**: 새로 생성 또는 기존 역할 선택
4. **임베딩 모델**: Titan Embeddings G1 - Text 선택
5. **벡터 데이터베이스**: Quick create (OpenSearch Serverless 자동 생성)
6. **데이터 소스**: S3 선택 → `s3://aiops-kb-docs-$ACCOUNT_ID-$REGION` 입력
7. **Create** 클릭

### 7-3. 데이터 동기화

```bash
# KB ID 확인
KB_ID=$(aws bedrock-agent list-knowledge-bases \
  --query "knowledgeBaseSummaries[?name=='aiops-knowledge-base'].knowledgeBaseId" \
  --output text)

# 데이터 소스 ID 확인
DS_ID=$(aws bedrock-agent list-data-sources \
  --knowledge-base-id $KB_ID \
  --query "dataSourceSummaries[0].dataSourceId" \
  --output text)

# 동기화 실행
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID

# 동기화 상태 확인
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID
```

### 7-4. Agent에 KB 연결

```bash
# Agent에 Knowledge Base 연결
aws bedrock-agent associate-agent-knowledge-base \
  --agent-id $AGENT_ID \
  --agent-version DRAFT \
  --knowledge-base-id $KB_ID \
  --description "AIOps 프로젝트 문서"

# Agent 재준비
aws bedrock-agent prepare-agent --agent-id $AGENT_ID
```

### 7-5. 환경 변수 설정

`.env` 파일에 KB 정보 추가:

```bash
# Bedrock Knowledge Base
KNOWLEDGE_BASE_ID=your-kb-id        # 위에서 확인한 $KB_ID
KB_DATA_SOURCE_ID=your-ds-id        # 위에서 확인한 $DS_ID
KB_S3_BUCKET=aiops-kb-docs-xxx      # 문서 업로드한 S3 버킷
KB_S3_PREFIX=docs                   # S3 내 문서 경로
```

### 7-6. KB 검색 테스트

```bash
# KB 직접 검색 테스트
aws bedrock-agent-runtime retrieve \
  --knowledge-base-id $KB_ID \
  --retrieval-query '{"text": "Agent Builder 사용법"}'
```

---

## 보안 원칙

이 템플릿은 AWS 보안 모범 사례를 따릅니다:

| 원칙 | 구현 |
|------|------|
| 최소 권한 | IAM 역할에 필요한 권한만 부여 |
| 암호화 | KMS로 저장 데이터 암호화 |
| 로깅 | CloudWatch Logs로 모든 활동 기록 |
| 네트워크 | VPC 엔드포인트 지원 (선택) |
| 컨테이너 보안 | ECR 이미지 스캔 활성화 |

---

## 비용 예상

| 서비스 | 예상 비용 (월) |
|--------|---------------|
| AgentCore Runtime | 사용량 기반 |
| Bedrock Claude 3.5 | ~$3/1M 토큰 |
| Lambda | 프리티어 내 |
| S3 (Memory) | ~$0.023/GB |
| ECR | ~$0.10/GB |

---

## 트러블슈팅

### CDK Bootstrap 실패

```bash
cdk bootstrap aws://ACCOUNT_ID/REGION --trust ACCOUNT_ID
```

### ECR 푸시 권한 오류

```bash
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
```

### Bedrock 모델 접근 오류

AWS 콘솔 → Bedrock → Model access에서 Claude 3.5 Sonnet 활성화

---

## 다음 단계

1. **Agent Builder 연결**: `kiro chat --agent agent-builder`로 새 Agent 생성
2. **도구 추가**: Lambda 함수로 새 도구 구현 후 Gateway 연결
3. **Memory 활용**: 대화 컨텍스트 유지로 더 자연스러운 대화

---

**이전:** [로컬 배포 가이드](QUICKSTART-LOCAL.md)
