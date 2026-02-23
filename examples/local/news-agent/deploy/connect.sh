#!/bin/bash
# connect.sh - News Agent SSM 포트포워딩 접속 스크립트
# 사용법: ./connect.sh [로컬포트] [리전]
set -e

LOCAL_PORT="${1:-8080}"
REGION="${2:-us-west-2}"
STACK_NAME="NewsAgentStack"

echo "🔍 스택 정보 조회 중..."
ALB_DNS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='InternalURL'].OutputValue" \
  --output text --region $REGION | sed 's|http://||')

CLUSTER=$(aws ecs list-clusters \
  --query "clusterArns[?contains(@,'NewsAgent')]|[0]" \
  --output text --region $REGION)

TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER \
  --query "taskArns[0]" --output text --region $REGION)

TASK_ID=$(echo $TASK_ARN | awk -F'/' '{print $NF}')
CLUSTER_NAME=$(echo $CLUSTER | awk -F'/' '{print $NF}')

RUNTIME_ID=$(aws ecs describe-tasks --cluster $CLUSTER --tasks $TASK_ARN \
  --query "tasks[0].containers[0].runtimeId" \
  --output text --region $REGION)

TARGET="ecs:${CLUSTER_NAME}_${TASK_ID}_${RUNTIME_ID}"

echo ""
echo "✅ 접속 정보:"
echo "   ALB:    $ALB_DNS"
echo "   Target: $TARGET"
echo ""
echo "🔗 포트포워딩 시작: http://localhost:$LOCAL_PORT"
echo "   종료: Ctrl+C"
echo ""

aws ssm start-session \
  --target "$TARGET" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"host\":[\"$ALB_DNS\"],\"portNumber\":[\"80\"],\"localPortNumber\":[\"$LOCAL_PORT\"]}" \
  --region $REGION
