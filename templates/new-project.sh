#!/bin/bash
# 새 Agent 프로젝트 생성 스크립트
# Usage: ./templates/new-project.sh <template> <project-name>
#   template: local | aws

set -e

TEMPLATE="$1"
PROJECT_NAME="$2"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -z "$TEMPLATE" ] || [ -z "$PROJECT_NAME" ]; then
  echo "Usage: $0 <template> <project-name>"
  echo "  template: local, aws"
  echo ""
  echo "Examples:"
  echo "  $0 local news-agent"
  echo "  $0 aws news-agent"
  exit 1
fi

SOURCE_DIR="$SCRIPT_DIR/$TEMPLATE"
TARGET_DIR="$REPO_ROOT/examples/$TEMPLATE/$PROJECT_NAME"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "❌ 템플릿이 없습니다: templates/$TEMPLATE"
  exit 1
fi

if [ -d "$TARGET_DIR" ]; then
  echo "❌ 이미 존재합니다: examples/$TEMPLATE/$PROJECT_NAME"
  exit 1
fi

echo "📁 examples/$TEMPLATE/$PROJECT_NAME 생성 중..."
mkdir -p "$TARGET_DIR"
cp -r "$SOURCE_DIR/"* "$TARGET_DIR/"

echo "✅ 생성 완료: examples/$TEMPLATE/$PROJECT_NAME"
echo ""
echo "다음 단계:"
echo "  cd examples/$TEMPLATE/$PROJECT_NAME"
if [ "$TEMPLATE" = "local" ]; then
  echo "  source ../../../.venv/bin/activate"
  echo "  kiro chat --agent agent-builder"
elif [ "$TEMPLATE" = "aws" ]; then
  echo "  ./deploy.sh"
fi
