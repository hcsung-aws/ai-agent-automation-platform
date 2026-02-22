#!/bin/bash
# News Agent 배포 (격리된 CDK 스택)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 News Agent 배포 시작..."
echo "   리전: ${CDK_DEPLOY_REGION:-us-west-2}"
echo ""

# CDK 의존성 확인
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK CLI가 필요합니다: npm install -g aws-cdk"
    exit 1
fi

# Python 의존성 설치 (CDK용)
pip install -q aws-cdk-lib constructs

# CDK bootstrap (최초 1회)
cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/${CDK_DEPLOY_REGION:-us-west-2}

# 배포
cdk deploy --require-approval never

echo ""
echo "✅ 배포 완료! 위 URL로 접속하세요."
echo "   제거: ./destroy.sh"
