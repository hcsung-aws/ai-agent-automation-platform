#!/bin/bash
# AIOps 스타터 킷 - AWS 배포 스크립트
# 사용법: ./deploy.sh

set -e

echo "🚀 AIOps 스타터 킷 AWS 배포를 시작합니다..."
echo ""

# 1. AWS 자격증명 확인
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
cd cdk
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q aws-cdk-lib constructs

# 4. CDK Bootstrap (최초 1회)
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
echo ""
echo "배포할 스택:"
echo "  - AIOpsInfrastructure (ECR, IAM, KMS)"
echo "  - AIOpsAgentCore (Runtime, Gateway, Memory)"
echo ""
read -p "계속하시겠습니까? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cdk deploy --all --require-approval never
    
    echo ""
    echo "=========================================="
    echo "✅ 배포 완료!"
    echo "=========================================="
    echo ""
    echo "다음 단계:"
    echo ""
    echo "1. ECR에 Agent 컨테이너 푸시:"
    echo "   docker build -t aiops-agent ../../../templates/local"
    echo "   docker tag aiops-agent:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/aiops-agents:latest"
    echo "   aws ecr get-login-password | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
    echo "   docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/aiops-agents:latest"
    echo ""
    echo "2. AgentCore Runtime 생성:"
    echo "   aws bedrock create-agent --agent-name aiops-supervisor ..."
    echo ""
    echo "3. Agent Builder 연결:"
    echo "   kiro chat --agent agent-builder"
    echo ""
    echo "=========================================="
else
    echo "배포가 취소되었습니다."
fi
