# Deployment Guide (Agent용)

이 문서는 deployment-agent가 따라갈 배포 절차입니다. 각 Step을 순서대로 실행하세요.

## 사전 조건 확인

배포 시작 전 반드시 확인:

```bash
# 1. AWS 자격증명
aws sts get-caller-identity
# → 실패 시: "aws configure 먼저 실행하세요" 안내 후 중단

# 2. Docker 실행 가능 여부
docker info
# → 실패 시: "Docker Desktop 실행하세요" 안내 후 중단

# 3. CDK 설치 여부
cdk --version
# → 실패 시: npm install -g aws-cdk 실행

# 4. 환경 변수 설정
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_DEFAULT_REGION:-us-east-1}
STACK_PREFIX=${STACK_PREFIX:-AIOps}
```

## Step 1: CDK 인프라 배포

```bash
cd templates/aws/cdk

# venv 설정
python3 -m venv .venv
source .venv/bin/activate
pip install -q aws-cdk-lib constructs

# Bootstrap (최초 1회 - 이미 있으면 스킵)
aws cloudformation describe-stacks --stack-name CDKToolkit 2>/dev/null || \
  cdk bootstrap aws://$ACCOUNT_ID/$REGION

# 스택 배포
STACK_PREFIX=$STACK_PREFIX cdk deploy --all --require-approval never
```

**분기 조건:**
- `CDKToolkit` 스택이 이미 있으면 bootstrap 스킵
- 배포 실패 시 에러 메시지 확인 → 권한 문제면 IAM 정책 안내

**배포되는 리소스:**
- `${STACK_PREFIX}Infrastructure`: ECR, IAM Role, KMS Key, KB S3 Bucket
- `${STACK_PREFIX}AgentCore`: AgentCore Runtime, Memory

## Step 2: Docker 이미지 빌드 및 ECR 푸시

```bash
cd templates/local

# ARM64 이미지 빌드 (AgentCore는 ARM64 전용)
docker build --platform linux/arm64 -t aiops-agent .

# ECR 로그인
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# 태그 및 푸시
ECR_URI=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/${STACK_PREFIX,,}-agents
docker tag aiops-agent:latest $ECR_URI:latest
docker push $ECR_URI:latest
```

**주의사항:**
- 반드시 `--platform linux/arm64` 사용 (AgentCore Runtime은 ARM64 전용)
- ECR 리포지토리명은 STACK_PREFIX를 소문자로 변환: `${STACK_PREFIX,,}-agents`

**오류 대응:**
- `no matching manifest for linux/arm64`: Docker buildx 설정 필요
  ```bash
  docker buildx create --use
  docker buildx build --platform linux/arm64 -t aiops-agent --load .
  ```
- `denied: Your authorization token has expired`: ECR 로그인 재실행

## Step 3: AgentCore Runtime 업데이트

CDK가 AgentCore Runtime을 자동 생성하므로, ECR 이미지 푸시 후 Runtime이 새 이미지를 사용하도록 업데이트합니다.

```bash
# Runtime ID 확인
RUNTIME_ID=$(aws bedrock-agentcore list-agent-runtimes \
  --query "agentRuntimeSummaries[?agentRuntimeName=='${STACK_PREFIX,,}_supervisor'].agentRuntimeId" \
  --output text --region $REGION)

echo "Runtime ID: $RUNTIME_ID"

# Runtime 상태 확인
aws bedrock-agentcore get-agent-runtime \
  --agent-runtime-id $RUNTIME_ID \
  --region $REGION \
  --query 'agentRuntimeStatus'
```

**분기 조건:**
- Runtime 상태가 `ACTIVE`면 정상
- `FAILED`면 로그 확인:
  ```bash
  aws logs filter-log-events \
    --log-group-name "/aws/bedrock-agentcore/runtimes/${RUNTIME_ID}-DEFAULT" \
    --filter-pattern "ERROR" --limit 20 --region $REGION
  ```

## Step 4: KB 동기화 (선택)

Knowledge Base가 설정된 경우에만 실행합니다.

```bash
# KB S3 버킷 확인
KB_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name ${STACK_PREFIX}Infrastructure \
  --query "Stacks[0].Outputs[?OutputKey=='KBBucketName'].OutputValue" \
  --output text --region $REGION)

# 로컬 KB를 S3에 동기화
aws s3 sync knowledge-base/ s3://$KB_BUCKET/knowledge-base/ --region $REGION

# Bedrock KB Sync (KB ID가 있는 경우)
# KNOWLEDGE_BASE_ID와 DATA_SOURCE_ID는 사용자에게 확인
```

## Step 5: 배포 검증

```bash
# 1. Runtime 상태 확인
aws bedrock-agentcore get-agent-runtime \
  --agent-runtime-id $RUNTIME_ID \
  --region $REGION \
  --query '{Status: agentRuntimeStatus, Name: agentRuntimeName}'

# 2. 최근 로그 확인 (정상 기동 여부)
aws logs filter-log-events \
  --log-group-name "/aws/bedrock-agentcore/runtimes/${RUNTIME_ID}-DEFAULT" \
  --start-time $(($(date +%s) - 300))000 --limit 10 --region $REGION

# 3. 헬스체크 (AgentCore Runtime invoke)
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-id $RUNTIME_ID \
  --region $REGION \
  --runtime-session-id $(python3 -c "import uuid; print(str(uuid.uuid4()))") \
  --payload '{"prompt": "ping"}' \
  /dev/stdout
```

**성공 기준:**
- Runtime 상태: `ACTIVE`
- 로그에 `ERROR` 없음
- invoke 응답에 `"status": "success"` 포함

## 자주 발생하는 오류

| 오류 | 원인 | 해결 |
|------|------|------|
| AccessDeniedException (Bedrock) | IAM에 inference-profile 누락 | `arn:aws:bedrock:*:*:inference-profile/*` 추가 |
| ARM64 이미지 오류 | x86_64로 빌드 | `--platform linux/arm64` 사용 |
| KMS 권한 오류 | CloudWatch Logs 서비스 권한 없음 | KMS 키 정책에 logs 서비스 추가 |
| ECR 인증 만료 | 토큰 12시간 유효 | `aws ecr get-login-password` 재실행 |
| IAM description 오류 | 한글 사용 | description은 영어로 작성 |
