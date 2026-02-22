#!/bin/bash
# News Agent 완전 제거
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🗑️  News Agent 스택 제거 중..."
cdk destroy --force
echo "✅ 완전 제거 완료."
