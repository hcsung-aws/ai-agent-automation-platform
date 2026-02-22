# NewsAgentStack 보안 개선 TODO

> 작성일: 2026-02-22 | 스택: `NewsAgentStack` (us-west-2)
> 파일: `examples/local/news-agent/deploy/stack.py`

## ✅ 해결 완료

| # | 항목 | 해결 방법 |
|---|------|-----------|
| 1 | ALB 0.0.0.0/0 개방 | `open_listener=False` + 본인 IP만 허용 (`ALLOWED_IP` 환경변수) |
| 2 | Fargate Public IP 노출 | Private Subnet + NAT Gateway로 전환, `assign_public_ip=False` |
| 3 | VPC Flow Logs 미설정 | `vpc.add_flow_log()` → CloudWatch Logs로 전체 트래픽 기록 |

## 🟡 미해결 항목 (심각도순)

### 1. HTTP 평문 통신 (HTTPS 미적용)

- 현재: ALB 리스너가 HTTP:80만 사용
- 위험: 브라우저 ↔ ALB 구간 대화 내용이 암호화되지 않음
- 해결:
  - ACM 인증서 발급 (도메인 필요)
  - ALB 리스너를 HTTPS:443으로 변경
  - HTTP:80 → HTTPS:443 리다이렉트 추가
- 코드 변경 위치: `stack.py` → `service` 생성 부분

```python
from aws_cdk import aws_certificatemanager as acm

certificate = acm.Certificate(self, "Cert",
    domain_name="your-domain.com",
    validation=acm.CertificateValidation.from_dns(),
)

# service 생성 시 추가
service = ecs_patterns.ApplicationLoadBalancedFargateService(
    ...
    certificate=certificate,
    redirect_http=True,  # HTTP → HTTPS 자동 리다이렉트
)
```

### 2. Bedrock IAM 정책 Resource: *

- 현재: `bedrock:InvokeModel` 권한이 모든 모델(`*`)에 적용
- 위험: 의도하지 않은 고비용 모델 호출 가능
- 해결: 사용 중인 모델 ARN으로 제한

```python
# stack.py 수정
service.task_definition.task_role.add_to_policy(
    iam.PolicyStatement(
        actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
        resources=[
            f"arn:aws:bedrock:us-east-1::foundation-model/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            # cross-region inference profile ARN도 추가 필요할 수 있음
            f"arn:aws:bedrock:us-east-1:{self.account}:inference-profile/*",
        ],
    )
)
```

### 3. CloudWatch Logs KMS 암호화 없음

- 현재: `kmsKeyId: null` (AWS 기본 암호화만)
- 위험: Agent 대화 내용이 로그에 포함될 수 있음
- 해결:

```python
from aws_cdk import aws_kms as kms

log_key = kms.Key(self, "LogKey",
    enable_key_rotation=True,
    removal_policy=RemovalPolicy.DESTROY,
)

# log_driver에서 사용하는 LogGroup을 직접 생성
log_group = logs.LogGroup(self, "AgentLogs",
    retention=logs.RetentionDays.THREE_DAYS,
    encryption_key=log_key,
    removal_policy=RemovalPolicy.DESTROY,
)
```

### 4. ECR 이미지 스캔 비활성화

- 현재: `imageScanOnPush: false`
- 위험: 컨테이너 이미지 취약점이 탐지되지 않음
- 해결: CDK Bootstrap ECR 리포지토리는 직접 수정 불가 → AWS CLI로 설정

```bash
aws ecr put-image-scanning-configuration \
  --region us-west-2 \
  --repository-name cdk-hnb659fds-container-assets-965037532757-us-west-2 \
  --image-scanning-configuration scanOnPush=true
```

### 5. ALB Access Logs 비활성화

- 현재: `access_logs.s3.enabled: false`
- 위험: 접근 기록이 없어 보안 사고 시 추적 어려움
- 해결:

```python
from aws_cdk import aws_s3 as s3

access_log_bucket = s3.Bucket(self, "ALBLogs",
    removal_policy=RemovalPolicy.DESTROY,
    auto_delete_objects=True,
)

service.load_balancer.log_access_logs(access_log_bucket)
```

## 참고

- 현재 NAT Gateway 비용 ~$32/월 발생 중. 테스트 완료 후 `./destroy.sh` 실행
- IP 변경 시: `ALLOWED_IP=x.x.x.x/32 cdk deploy`
- 전체 제거: `cd deploy && ./destroy.sh`
