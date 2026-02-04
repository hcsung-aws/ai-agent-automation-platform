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

### Mickey 9: LLM 응답에 메타데이터 의존 금지
- Problem: 테스트 모드 표시를 LLM 응답에 포함시켰으나 Supervisor가 생략
- Cause: LLM은 "중요하지 않다"고 판단한 내용을 요약/생략함
- Solution: 코드 레벨에서 플래그 관리 (`IS_TEST_MODE` + 튜플 반환)
- Avoid: 중요한 메타데이터를 LLM 응답 텍스트에 의존

### Mickey 9: 테스트 모드 Agent 패턴
- Pattern: `IS_TEST_MODE = True` 플래그 + `create_agent() -> (agent, is_test_mode)` 튜플 반환
- app.py에서 플래그 확인 후 경고 배너 자동 출력
- 실제 API 연동 시 `IS_TEST_MODE = False`로 변경

### Mickey 9: app.py 수정 시 9개 항목 체크
- import 추가
- agent 변수 추가
- ask_{name}_agent 도구 함수 추가
- SYSTEM_PROMPT에 Agent 설명 추가
- tools 리스트에 추가
- 시작 메시지에 Agent 영역 추가
- 처리 과정 표시에 emoji/label 추가
- 상세 보기 버튼 label 추가
- 상세 보기 title 추가

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
Mickey 9 - 2026-02-04
