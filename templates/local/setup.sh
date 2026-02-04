#!/bin/bash
# AIOps 스타터 킷 - 로컬 환경 설치 스크립트
# 사용법: ./setup.sh

set -e

echo "🚀 AIOps 스타터 킷 설치를 시작합니다..."
echo ""

# 1. Python 버전 확인
echo "1️⃣ Python 버전 확인..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.10 이상이 필요합니다. 현재: $PYTHON_VERSION"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION"

# 2. 가상환경 생성
echo ""
echo "2️⃣ 가상환경 생성..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ .venv 생성 완료"
else
    echo "✅ .venv 이미 존재"
fi

# 3. 가상환경 활성화
echo ""
echo "3️⃣ 가상환경 활성화..."
source .venv/bin/activate
echo "✅ 활성화 완료"

# 4. 의존성 설치
echo ""
echo "4️⃣ 의존성 설치..."
pip install --upgrade pip -q
pip install strands-agents chainlit boto3 -q
echo "✅ 설치 완료"

# 5. AWS 자격증명 확인
echo ""
echo "5️⃣ AWS 자격증명 확인..."
if aws sts get-caller-identity &>/dev/null; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo "✅ AWS 계정: $ACCOUNT_ID"
else
    echo "⚠️  AWS 자격증명이 설정되지 않았습니다."
    echo "   다음 명령으로 설정하세요:"
    echo "   aws configure"
    echo ""
fi

# 6. 완료 메시지
echo ""
echo "=========================================="
echo "✅ 설치 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo ""
echo "1. 서버 실행:"
echo "   source .venv/bin/activate"
echo "   chainlit run app.py --port 8000"
echo ""
echo "2. 브라우저에서 접속:"
echo "   http://localhost:8000"
echo ""
echo "3. Agent Builder로 새 Agent 만들기:"
echo "   kiro chat --agent agent-builder"
echo ""
echo "=========================================="
