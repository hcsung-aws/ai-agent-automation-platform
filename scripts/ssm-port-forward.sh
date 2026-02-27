#!/bin/bash
# SSM 포트포워딩으로 ECS Fargate UI에 로컬 브라우저 접속
# 사용법: ./scripts/ssm-port-forward.sh [리전] [로컬포트]
# 예시:   ./scripts/ssm-port-forward.sh us-west-2 8000

REGION="${1:-us-west-2}"
LOCAL_PORT="${2:-8000}"
CONTAINER_PORT="8000"

CLUSTER=$(aws ecs list-clusters --region "$REGION" \
  --query "clusterArns[?contains(@,'AIOpsUI')]|[0]" --output text)
TASK=$(aws ecs list-tasks --cluster "$CLUSTER" --region "$REGION" \
  --desired-status RUNNING --query "taskArns[0]" --output text)

if [ "$TASK" = "None" ] || [ -z "$TASK" ]; then
  echo "❌ 실행 중인 태스크가 없습니다." && exit 1
fi

CNAME=$(echo "$CLUSTER" | awk -F/ '{print $2}')
TID=$(echo "$TASK" | awk -F/ '{print $3}')
RID=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK" --region "$REGION" \
  --query "tasks[0].containers[0].runtimeId" --output text)

echo "🔗 http://localhost:${LOCAL_PORT} → ECS container:${CONTAINER_PORT}"
echo "   Region: ${REGION}, Task: ${TID}"
echo "   Ctrl+C로 종료"
echo ""

aws ssm start-session \
  --target "ecs:${CNAME}_${TID}_${RID}" \
  --document-name AWS-StartPortForwardingSession \
  --parameters "{\"portNumber\":[\"${CONTAINER_PORT}\"],\"localPortNumber\":[\"${LOCAL_PORT}\"]}" \
  --region "$REGION"
