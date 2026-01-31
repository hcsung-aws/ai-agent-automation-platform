# Project Context for Mickey Agents

## Environment
- OS: Linux (WSL2)
- Region: us-east-1
- 주요 서비스: Bedrock AgentCore, Knowledge Bases, DynamoDB, S3

## Goal
조직 업무를 AI Agent 기반으로 전환하는 플랫폼 구축
- 점진적 학습 + A2A 협업 + 자기 개선

## Constraints
- 2주 PoC 일정
- AWS Bedrock 기반
- 초기 Agent 2개 (DevOps, 데이터분석)

## Key Decisions

### 2026-01-30: 프레임워크 선택
- Chosen: AgentCore + Strands Agents
- Reasoning: AWS 공식 지원, 요구사항 대부분 충족

### 2026-01-30: 챗봇 UI
- Chosen: Chainlit
- Reasoning: LLM 챗봇 특화, 스트리밍 기본 지원

### 2026-01-30: A2A 아키텍처
- PoC: AgentCore Multi-Agent Collaboration (HTTP 기반)
- Phase 3: Kafka Hub-Spoke 도입 검토 (확장성 필요 시)

## Known Issues
- Docker Hub rate limit → ECR Public 이미지 사용
- AgentCore IAM 역할에 도구 권한 별도 추가 필요

## Lessons Learned

### Mickey 1: AgentCore 배포
- Problem: Docker Hub rate limit으로 빌드 실패
- Cause: CodeBuild에서 Docker Hub 이미지 pull 제한
- Solution: `public.ecr.aws/docker/library/python:3.10-slim` 사용
- Avoid: Docker Hub 이미지 직접 사용

### Mickey 1: IAM 권한
- Problem: Agent 도구 실행 시 권한 오류
- Cause: AgentCore 자동 생성 역할에 도구 권한 없음
- Solution: `DevOpsAgentToolsPolicy` 인라인 정책 추가
- Avoid: 자동 생성 역할만 의존

## File Locations
- Source: src/ (예정)
- Infrastructure: infra/ (예정)
- Tests: tests/ (예정)
- Docs: docs/ (예정)

## Common Commands
```bash
# (구현 후 추가 예정)
```

## Last Updated
Mickey 1 - 2026-01-30
