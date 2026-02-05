# AWS 배포 가이드

## 사전 요구사항

- AWS CLI 설정 완료
- Node.js 18+ (CDK용)
- Docker

## 배포 실행

```bash
cd templates/aws
./deploy.sh
```

## 배포 구성요소

1. **Infrastructure Stack**
   - ECR (컨테이너 레지스트리)
   - IAM 역할
   - KMS 암호화 키

2. **AgentCore Stack**
   - Runtime (Agent 호스팅)
   - Gateway (도구 연결)
   - Memory (대화 컨텍스트)

## Knowledge Base 생성

AWS 콘솔에서 수동 생성 필요:
1. Bedrock → Knowledge bases → Create
2. S3 데이터 소스 연결
3. 동기화 실행
4. Agent에 KB 연결

자세한 내용: docs/QUICKSTART-AWS.md 참고
