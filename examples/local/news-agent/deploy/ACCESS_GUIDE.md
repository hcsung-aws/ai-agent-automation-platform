# News Agent 접속 가이드 (SSM 포트포워딩)

ALB가 Internal이므로 외부에서 직접 접근할 수 없습니다.
SSM Session Manager 포트포워딩을 통해 로컬에서 접속합니다.

## 사전 준비

1. AWS CLI v2 + Session Manager 플러그인 설치:
```bash
# Session Manager 플러그인 (Linux)
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb
```

2. CDK 배포 후 출력값 확인:
```bash
cd deploy && cdk deploy
# 출력 예시:
# NewsAgentStack.InternalURL = http://internal-NewsA-Servi-XXXXX.us-west-2.elb.amazonaws.com
# NewsAgentStack.VpcId = vpc-0abc123def456
```

## 접속 방법

### Step 1: VPC 내 Private 서브넷 ID 확인
```bash
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=<VpcId>" "Name=tag:Name,Values=*Private*" \
  --query "Subnets[0].SubnetId" --output text \
  --region us-west-2
```

### Step 2: ALB DNS에서 IP 확인
```bash
# Internal ALB의 Private IP 확인
aws ec2 describe-network-interfaces \
  --filters "Name=description,Values=*NewsAgent*" "Name=vpc-id,Values=<VpcId>" \
  --query "NetworkInterfaces[0].PrivateIpAddress" --output text \
  --region us-west-2
```

또는 ALB DNS 이름으로 직접 확인:
```bash
# InternalURL 출력값에서 호스트명 추출 후
nslookup <ALB_DNS_NAME>
```

### Step 3: SSM 포트포워딩 시작
```bash
aws ssm start-session \
  --target <ECS_TASK_OR_INSTANCE_ID> \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"host\":[\"<ALB_PRIVATE_IP_OR_DNS>\"],\"portNumber\":[\"80\"],\"localPortNumber\":[\"8080\"]}" \
  --region us-west-2
```

> **참고**: ECS Fargate 태스크에 직접 SSM 세션을 열려면 ECS Exec이 활성화되어 있어야 합니다.
> 대안으로 VPC 내에 EC2 Bastion을 사용하거나, 아래 간편 스크립트를 사용하세요.

### Step 4: 브라우저에서 접속
```
http://localhost:8080
```

## 간편 접속 스크립트

아래 스크립트를 사용하면 한 번에 접속할 수 있습니다:

```bash
#!/bin/bash
# connect.sh - News Agent SSM 포트포워딩 접속
REGION="us-west-2"
STACK_NAME="NewsAgentStack"
LOCAL_PORT="${1:-8080}"

# 1. VPC ID 조회
VPC_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='VpcId'].OutputValue" \
  --output text --region $REGION)

# 2. ALB DNS 조회
ALB_DNS=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='InternalURL'].OutputValue" \
  --output text --region $REGION | sed 's|http://||')

# 3. Private 서브넷 ID 조회
SUBNET_ID=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=*Private*" \
  --query "Subnets[0].SubnetId" --output text --region $REGION)

# 4. ECS 태스크 ID 조회
CLUSTER_ARN=$(aws ecs list-clusters \
  --query "clusterArns[?contains(@, 'NewsAgent')]|[0]" \
  --output text --region $REGION)
TASK_ARN=$(aws ecs list-tasks \
  --cluster $CLUSTER_ARN \
  --query "taskArns[0]" --output text --region $REGION)

echo "🔗 포트포워딩 시작: localhost:$LOCAL_PORT → $ALB_DNS:80"
echo "   브라우저에서 http://localhost:$LOCAL_PORT 으로 접속하세요"
echo "   종료: Ctrl+C"
echo ""

aws ssm start-session \
  --target "ecs:${CLUSTER_ARN##*/}_${TASK_ARN##*/}_$(aws ecs describe-tasks \
    --cluster $CLUSTER_ARN --tasks $TASK_ARN \
    --query "tasks[0].containers[0].runtimeId" \
    --output text --region $REGION)" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"host\":[\"$ALB_DNS\"],\"portNumber\":[\"80\"],\"localPortNumber\":[\"$LOCAL_PORT\"]}" \
  --region $REGION
```

사용법:
```bash
chmod +x connect.sh
./connect.sh        # 기본 포트 8080
./connect.sh 3000   # 포트 3000 사용
```

## ECS Exec 활성화 (필요 시)

SSM 포트포워딩에 ECS Exec이 필요한 경우, CDK 스택에 다음을 추가합니다:

```python
# stack.py에 추가
service.service.enable_execute_command = True
```

그리고 태스크 역할에 SSM 권한을 추가합니다:

```python
service.task_definition.task_role.add_to_policy(
    iam.PolicyStatement(
        actions=[
            "ssmmessages:CreateControlChannel",
            "ssmmessages:CreateDataChannel",
            "ssmmessages:OpenControlChannel",
            "ssmmessages:OpenDataChannel",
        ],
        resources=["*"],
    )
)
```

## 트러블슈팅

| 증상 | 해결 |
|------|------|
| `TargetNotConnected` | ECS Exec 활성화 확인, 태스크 재배포 |
| `Session Manager 플러그인 없음` | 위 사전 준비 참고 |
| `Connection refused` | ALB 헬스체크 상태 확인: `aws elbv2 describe-target-health` |
| 타임아웃 | Security Group에서 VPC CIDR → 포트 80 허용 확인 |
