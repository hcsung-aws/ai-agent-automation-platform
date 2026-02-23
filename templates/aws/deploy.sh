#!/bin/bash
# AIOps 스타터 킷 - AWS 배포 스크립트 (Hybrid Architecture)
# 사용법: ./deploy.sh [AGENT_PATH]
#   AGENT_PATH: agent 프로젝트 루트 (config.py + agents/ 포함, 기본: ../local)
#   환경변수:
#     STACK_PREFIX: 스택 접두사 (기본: AIOps)
#     AWS_DEFAULT_REGION: 배포 리전 (기본: us-east-1)

set -e

echo "🚀 AIOps 스타터 킷 AWS 배포를 시작합니다..."
echo "   아키텍처: Infrastructure + AgentCore + UI (Fargate)"
echo ""

# Agent 프로젝트 경로
AGENT_PATH=${1:-${AGENT_PATH:-$(dirname "$0")/../local}}
AGENT_PATH=$(cd "$AGENT_PATH" 2>/dev/null && pwd || echo "$AGENT_PATH")

if [ ! -d "$AGENT_PATH/agents" ]; then
    echo "❌ Agent 프로젝트 경로를 찾을 수 없습니다: $AGENT_PATH"
    echo "   agents/ 디렉토리와 config.py가 포함된 경로를 지정하세요."
    echo "   사용법: ./deploy.sh /path/to/project"
    exit 1
fi
echo "📁 Agent 프로젝트 경로: $AGENT_PATH"

# 1. AWS 자격증명 확인
echo ""
echo "1️⃣ AWS 자격증명 확인..."
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS 자격증명이 설정되지 않았습니다."
    echo "   aws configure 명령으로 설정하세요."
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_DEFAULT_REGION:-us-east-1}
echo "✅ AWS 계정: $ACCOUNT_ID, 리전: $REGION"

# 2. CDK 설치 확인
echo ""
echo "2️⃣ CDK 설치 확인..."
if ! command -v cdk &>/dev/null; then
    echo "CDK 설치 중..."
    npm install -g aws-cdk
fi
echo "✅ CDK $(cdk --version)"

# 3. Python 의존성 설치
echo ""
echo "3️⃣ Python 의존성 설치..."
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR/cdk"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q aws-cdk-lib constructs

# 4. CDK Bootstrap
echo ""
echo "4️⃣ CDK Bootstrap 확인..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit &>/dev/null; then
    echo "CDK Bootstrap 실행 중..."
    cdk bootstrap aws://$ACCOUNT_ID/$REGION
fi
echo "✅ Bootstrap 완료"

# 5. 스택 배포
echo ""
echo "5️⃣ 스택 배포..."
STACK_PREFIX=${STACK_PREFIX:-AIOps}
echo ""
echo "스택 접두사: $STACK_PREFIX"
echo "Agent 경로: $AGENT_PATH"
echo ""
echo "배포할 스택 (3개):"
echo "  1. ${STACK_PREFIX}Infrastructure (ECR, IAM, KMS, KB, S3 Vectors, DynamoDB)"
echo "  2. ${STACK_PREFIX}AgentCore (Runtime, Memory)"
echo "  3. ${STACK_PREFIX}UI (Fargate + Chainlit → AgentCore API 호출)"
echo ""
read -p "계속하시겠습니까? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    STACK_PREFIX=$STACK_PREFIX cdk deploy --all --require-approval never -c agent_path=$AGENT_PATH

    echo ""
    echo "=========================================="
    echo "✅ CDK 배포 완료!"
    echo "=========================================="
    echo ""

    # 스택 출력 조회
    KB_BUCKET=$(aws cloudformation describe-stacks --stack-name ${STACK_PREFIX}Infrastructure \
        --query "Stacks[0].Outputs[?OutputKey=='KBBucketName'].OutputValue" --output text 2>/dev/null)
    KB_ID=$(aws cloudformation describe-stacks --stack-name ${STACK_PREFIX}Infrastructure \
        --query "Stacks[0].Outputs[?OutputKey=='KnowledgeBaseId'].OutputValue" --output text 2>/dev/null)
    DS_ID=$(aws cloudformation describe-stacks --stack-name ${STACK_PREFIX}Infrastructure \
        --query "Stacks[0].Outputs[?OutputKey=='DataSourceId'].OutputValue" --output text 2>/dev/null)
    UI_URL=$(aws cloudformation describe-stacks --stack-name ${STACK_PREFIX}UI \
        --query "Stacks[0].Outputs[?OutputKey=='InternalURL'].OutputValue" --output text 2>/dev/null)

    echo "📋 배포 정보:"
    echo "  KB S3 버킷: $KB_BUCKET"
    echo "  KB ID: $KB_ID"
    echo "  UI URL (Internal): $UI_URL"
    echo ""
    echo "📌 다음 단계:"
    echo ""
    echo "1. KB 문서를 S3에 업로드:"
    echo "   aws s3 sync knowledge-base/ s3://$KB_BUCKET/knowledge-base/"
    echo ""
    echo "2. KB Ingestion 실행:"
    echo "   aws bedrock-agent start-ingestion-job \\"
    echo "     --knowledge-base-id $KB_ID \\"
    echo "     --data-source-id $DS_ID \\"
    echo "     --region $REGION"
    echo ""
    echo "3. UI 접속 (SSM 포트포워딩):"
    echo "   # 클러스터/태스크 정보 조회 후:"
    echo "   aws ssm start-session \\"
    echo "     --target ecs:<cluster>_<task-id>_<container-runtime-id> \\"
    echo "     --document-name AWS-StartPortForwardingSession \\"
    echo "     --parameters '{\"portNumber\":[\"8000\"],\"localPortNumber\":[\"8000\"]}'"
    echo "   # 브라우저에서 http://localhost:8000 접속"
    echo ""
    echo "=========================================="
else
    echo "배포가 취소되었습니다."
fi
