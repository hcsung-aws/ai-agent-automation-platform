#!/bin/bash
# AIOps 스타터 킷 - 로컬 환경 설치 스크립트
# 사용법: ./setup.sh

set -e

echo "🚀 AIOps 스타터 킷 설치를 시작합니다..."
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 에러 핸들러
error_exit() {
    echo -e "${RED}❌ 오류: $1${NC}" >&2
    echo ""
    echo "문제 해결:"
    echo "  - docs/QUICKSTART-LOCAL.md의 트러블슈팅 섹션 참고"
    echo "  - 또는 GitHub Issues에 문의"
    exit 1
}

# 1. Python 버전 확인
echo "1️⃣ Python 버전 확인..."
if ! command -v python3 &> /dev/null; then
    error_exit "python3가 설치되어 있지 않습니다.\n   설치: https://www.python.org/downloads/"
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    error_exit "Python 3.10 이상이 필요합니다. 현재: $PYTHON_VERSION"
fi
echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"

# 2. pip 확인
echo ""
echo "2️⃣ pip 확인..."
if ! python3 -m pip --version &> /dev/null; then
    error_exit "pip가 설치되어 있지 않습니다.\n   설치: python3 -m ensurepip --upgrade"
fi
echo -e "${GREEN}✅ pip 사용 가능${NC}"

# 3. 가상환경 생성
echo ""
echo "3️⃣ 가상환경 생성..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv || error_exit "가상환경 생성 실패"
    echo -e "${GREEN}✅ .venv 생성 완료${NC}"
else
    echo -e "${GREEN}✅ .venv 이미 존재${NC}"
fi

# 4. 가상환경 활성화
echo ""
echo "4️⃣ 가상환경 활성화..."
source .venv/bin/activate || error_exit "가상환경 활성화 실패"
echo -e "${GREEN}✅ 활성화 완료${NC}"

# 5. 의존성 설치
echo ""
echo "5️⃣ 의존성 설치..."
pip install --upgrade pip -q || error_exit "pip 업그레이드 실패"

# 필수 패키지 설치
PACKAGES="strands-agents chainlit boto3 python-dotenv"
for pkg in $PACKAGES; do
    echo "   설치 중: $pkg"
    pip install $pkg -q || error_exit "$pkg 설치 실패"
done
echo -e "${GREEN}✅ 의존성 설치 완료${NC}"

# 6. knowledge-base 디렉토리 확인
echo ""
echo "6️⃣ Knowledge Base 디렉토리 확인..."
if [ ! -d "knowledge-base" ]; then
    mkdir -p knowledge-base/{common,devops,analytics,monitoring}
    echo -e "${GREEN}✅ knowledge-base/ 디렉토리 생성${NC}"
else
    echo -e "${GREEN}✅ knowledge-base/ 이미 존재${NC}"
fi

# 7. .env 파일 확인
echo ""
echo "7️⃣ 환경 설정 파일 확인..."
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  .env 파일 생성됨 (필요시 수정하세요)${NC}"
elif [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env 파일 존재${NC}"
else
    echo -e "${YELLOW}⚠️  .env.example 파일이 없습니다${NC}"
fi

# 8. AWS 자격증명 확인
echo ""
echo "8️⃣ AWS 자격증명 확인..."
if command -v aws &> /dev/null; then
    if aws sts get-caller-identity &>/dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        echo -e "${GREEN}✅ AWS 계정: $ACCOUNT_ID${NC}"
    else
        echo -e "${YELLOW}⚠️  AWS 자격증명이 설정되지 않았습니다.${NC}"
        echo "   Bedrock 모델 호출에 필요합니다."
        echo "   설정: aws configure"
    fi
else
    echo -e "${YELLOW}⚠️  AWS CLI가 설치되어 있지 않습니다.${NC}"
    echo "   설치: https://aws.amazon.com/cli/"
fi

# 9. 완료 메시지
echo ""
echo "=========================================="
echo -e "${GREEN}✅ 설치 완료!${NC}"
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
echo "문제 발생 시:"
echo "   docs/QUICKSTART-LOCAL.md 트러블슈팅 참고"
echo ""
echo "=========================================="
