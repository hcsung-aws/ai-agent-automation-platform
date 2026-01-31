# Mickey 1 Handoff Document

## Quick Start for Mickey 2

### 1. Current Status
- **Week 1 완료**: DevOps Agent PoC 구현 및 배포 완료
- **테스트 완료**: 모든 도구 정상 동작 확인
- **다음**: Week 2 작업 시작

### 2. Immediate Next Steps
1. Day 6: Knowledge Base 설정 + 문서 업로드 + Agent 연동
2. Day 7: 데이터분석 Agent 도구 구현 (Athena, QuickSight)
3. Day 8: Supervisor Agent (Multi-Agent 협업)

### 3. Important Context

**배포된 Agent 정보**:
```
Agent ARN: arn:aws:bedrock-agentcore:us-east-1:965037532757:runtime/devops_agent-y4RU5ICATL
Memory ID: devops_agent_mem-ddKjc73Yny
ECR: 965037532757.dkr.ecr.us-east-1.amazonaws.com/bedrock-agentcore-devops_agent
```

**IAM 역할**:
- `DevOpsAgentRole`: CDK로 생성, 도구용 권한
- `AmazonBedrockAgentCoreSDKRuntime-us-east-1-5ba3d94a1e`: AgentCore 실행 역할
  - `DevOpsAgentToolsPolicy` 추가됨 (CloudWatch, EC2, CloudFormation, DynamoDB)

**DynamoDB 테이블**:
- `incident-tickets`: 장애 티켓 (game-index GSI)
- `execution-logs`: 실행 로그

**S3 버킷**:
- `devops-agent-kb-965037532757`: Knowledge Base 문서용

### 4. Useful Commands
```bash
# 프로젝트 디렉토리
cd /home/hcsung/ai-developer-mickey-agents
source .venv/bin/activate

# AgentCore 테스트
agentcore invoke '{"prompt": "질문 내용"}'

# AgentCore 상태 확인
agentcore status

# Chainlit UI 실행
chainlit run app.py --port 8000

# CDK 배포
cd infra && npx aws-cdk deploy

# 로그 확인
aws logs tail /aws/bedrock-agentcore/runtimes/devops_agent-y4RU5ICATL-DEFAULT --follow
```

### 5. Known Issues
- Docker Hub rate limit → Dockerfile에서 `public.ecr.aws` 이미지 사용
- AgentCore 자동 생성 IAM 역할에 도구 권한 별도 추가 필요
- Chainlit config.toml 버전 호환성 → 삭제 후 재생성

### 6. Project Structure
```
ai-developer-mickey-agents/
├── infra/                    # CDK 인프라
├── src/
│   ├── tools/               # Agent 도구 (6개)
│   └── agent/               # Strands Agent
├── app.py                   # Chainlit UI
├── agentcore_app.py         # AgentCore entry point
├── Dockerfile
├── requirements.txt
├── PROJECT-PLAN.md          # 상세 계획서
└── .bedrock_agentcore.yaml  # AgentCore 설정
```

### 7. Context Window
- Usage at end: ~35%
- Status: Safe

---
Mickey 1 → Mickey 2
2026-01-30 01:34
