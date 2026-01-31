# Mickey 1 Session Log
Date: 2026-01-30 00:02 ~ 01:34

## Session Goal
AgentCore 기반 DevOps Agent PoC 구현 (Week 1)

## Initial Setup
- ✅ 프로젝트 디렉토리 확인
- ✅ 요구사항 분석 완료
- ✅ AgentCore 문서 조사 완료
- ✅ 계획서 작성 완료

## Progress

### Completed (Week 1 전체 완료)
1. **Day 1-2: 인프라 구축**
   - CDK 프로젝트 설정
   - IAM 역할 생성 (DevOpsAgentRole)
   - DynamoDB 테이블 (incident-tickets, execution-logs)
   - S3 버킷 (devops-agent-kb-965037532757)

2. **Day 3-4: Agent 도구 구현**
   - get_cloudwatch_metrics: CloudWatch 메트릭 조회
   - get_ec2_status: EC2 인스턴스 상태 조회
   - get_stack_events, list_stacks: CloudFormation 스택 이벤트/목록
   - create_incident_ticket, get_incident_tickets: 장애 티켓 생성/조회

3. **Day 5: 배포 및 UI**
   - AgentCore 배포 완료
   - Chainlit UI 구현

### Test Results
- ✅ CloudFormation 스택 목록 조회
- ✅ CloudFormation 스택 이벤트 조회
- ✅ 장애 티켓 생성 (ToadstoneGame)
- ✅ 장애 티켓 목록 조회
- ✅ EC2 인스턴스 상태 조회
- ✅ Chainlit UI 실행 확인

## Key Decisions

### Decision 1: 프레임워크 선택
- Chosen: AgentCore + Strands Agents
- Reasoning: AWS 공식 지원, 요구사항 대부분 충족

### Decision 2: 챗봇 UI
- Chosen: Chainlit
- Reasoning: LLM 챗봇 특화, 스트리밍 기본 지원

### Decision 3: A2A 아키텍처
- PoC: AgentCore Multi-Agent Collaboration
- Phase 3: Kafka Hub-Spoke 도입 검토

## Files Created/Modified
```
ai-developer-mickey-agents/
├── infra/
│   ├── app.py
│   ├── cdk.json
│   └── stacks/devops_agent_stack.py
├── src/
│   ├── tools/
│   │   ├── cloudwatch_tools.py
│   │   ├── ec2_tools.py
│   │   ├── cloudformation_tools.py
│   │   └── ticket_tools.py
│   └── agent/devops_agent.py
├── app.py (Chainlit UI)
├── agentcore_app.py (AgentCore entry point)
├── Dockerfile
├── requirements.txt
├── PROJECT-PLAN.md
├── PROJECT-OVERVIEW.md
├── ENVIRONMENT.md
└── .bedrock_agentcore.yaml
```

## AWS Resources Deployed
- **IAM Role**: DevOpsAgentRole, AmazonBedrockAgentCoreSDKRuntime-us-east-1-5ba3d94a1e
- **DynamoDB**: incident-tickets, execution-logs
- **S3**: devops-agent-kb-965037532757
- **ECR**: bedrock-agentcore-devops_agent
- **AgentCore**: devops_agent-y4RU5ICATL
- **Memory**: devops_agent_mem-ddKjc73Yny

## Lessons Learned
- AgentCore는 2025년 7월 Preview, us-east-1 지원
- Docker Hub rate limit → ECR Public 이미지 사용 필요
- AgentCore 자동 생성 IAM 역할에 도구 권한 별도 추가 필요
- Chainlit config.toml 버전 호환성 주의

## Context Window
- Usage at end: ~35%
- Status: Safe

## Next Steps (Week 2)
1. Day 6: Knowledge Base 설정 + 문서 업로드 + Agent 연동
2. Day 7: 데이터분석 Agent 도구 구현
3. Day 8: Supervisor Agent (Multi-Agent 협업)
4. Day 9: 실행 기록 저장 로직
5. Day 10: 테스트 + 버그 수정

---
Session Completed: 2026-01-30 01:34
