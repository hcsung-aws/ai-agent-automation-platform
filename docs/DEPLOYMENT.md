# 배포 가이드

## 개요

Game Ops Multi-Agent 시스템의 AWS 인프라 배포 가이드입니다.
CDK 또는 Terraform 중 선택하여 배포할 수 있습니다.

> **Note**: Knowledge Base는 콘솔에서 수동 생성이 필요합니다 (S3 Vectors 타입).

## 사전 요구사항

- AWS CLI 설정 완료
- Python 3.10+
- Node.js 18+ (CDK 사용 시)
- Terraform 1.0+ (Terraform 사용 시)

## 배포 리소스

| 리소스 | 용도 |
|--------|------|
| S3 Bucket | 데이터 저장, Athena 결과 |
| DynamoDB (incident-tickets) | 장애 티켓 |
| DynamoDB (execution-logs) | 실행 기록 |
| Glue Database (game_logs) | 분석 테이블 메타데이터 |
| IAM Role | Agent 실행 권한 |

---

## Option 1: CDK 배포

### 1. 의존성 설치
```bash
cd infra
pip install aws-cdk-lib constructs
npm install -g aws-cdk
```

### 2. CDK 부트스트랩 (최초 1회)
```bash
cdk bootstrap aws://ACCOUNT_ID/us-east-1
```

### 3. 배포
```bash
cdk deploy
```

### 4. 삭제
```bash
cdk destroy
```

---

## Option 2: Terraform 배포

### 1. 초기화
```bash
cd infra/terraform
terraform init
```

### 2. 계획 확인
```bash
terraform plan
```

### 3. 배포
```bash
terraform apply
```

### 4. 삭제
```bash
terraform destroy
```

---

## 배포 후 설정

### 1. 샘플 데이터 생성
```bash
cd ..  # 프로젝트 루트로 이동
source .venv/bin/activate
python scripts/setup_mmorpg_tables.py
```

### 2. Knowledge Base 생성 (콘솔)

1. AWS 콘솔 → Bedrock → Knowledge bases
2. "Create knowledge base" 클릭
3. 설정:
   - Name: `game-ops-kb`
   - Embedding model: Titan Text Embeddings V2
   - Vector store: Quick create (S3 Vectors)
4. Data source 추가:
   - S3 URI: `s3://game-ops-agent-{ACCOUNT_ID}/kb-docs/`
5. Sync 실행

### 3. 환경 변수 설정 (선택)
```bash
export AWS_REGION=us-east-1
export KNOWLEDGE_BASE_ID=<KB_ID>  # 콘솔에서 확인
```

---

## 로컬 실행

### Chainlit UI
```bash
chainlit run app.py
# http://localhost:8000
```

### 로그 조회 API
```bash
python logs_api.py
# http://localhost:8001
```

---

## 비용 예상 (PoC 기준)

| 서비스 | 예상 비용 |
|--------|----------|
| Bedrock (Claude) | ~$10-50/월 (사용량 기반) |
| DynamoDB | ~$1/월 (On-demand) |
| S3 | ~$1/월 |
| Athena | ~$5/월 (쿼리당 과금) |
| Glue | 무료 (카탈로그만 사용) |

---

## 트러블슈팅

### CDK 배포 실패
```bash
# 캐시 삭제 후 재시도
rm -rf cdk.out
cdk deploy
```

### Terraform state 문제
```bash
# state 새로고침
terraform refresh
```

### Athena 쿼리 실패
- S3 버킷 권한 확인
- Glue 테이블 파티션 확인: `MSCK REPAIR TABLE table_name`
