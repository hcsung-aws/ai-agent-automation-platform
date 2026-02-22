# Project Overview

## Project Name
AIOps 스타터 킷 - AI Agent 기반 운영 자동화 플랫폼

## 🎯 궁극적 목표

**조직이 AI Agent 기반 운영 자동화(AIOps)를 쉽고 빠르게 도입할 수 있도록 돕는 것**

이 프로젝트는:
1. **로컬 환경**에서 5분 만에 Agent 시스템을 실행하고
2. **Agent Builder**로 자연어로 새 Agent를 만들고
3. **AWS AgentCore**에 30분 만에 프로덕션 배포할 수 있는

**완전한 스타터 킷**을 제공합니다.

## Goal
- 개별 Agent: 챗봇 + A2A 협업
- 점진적 학습: 지식 누적 + 행동 패턴 기반 지침 생성
- 자기 개선: 실행 기록 → 사람 검토 → 개선
- **쉬운 배포**: 로컬/AWS 원클릭 배포 템플릿

## Scope
- In scope:
  - 로컬 배포 템플릿 (setup.sh, Chainlit UI)
  - AWS 배포 템플릿 (CDK, AgentCore)
  - Agent Builder (Kiro CLI 연동)
  - Multi-Agent 협업 (Supervisor)
  - 실행 기록 저장 및 검토 UI
  - 지식 베이스 연동 (RAG)
- Out of scope (향후):
  - 행동 패턴 자동 분석
  - 도구 자동 업데이트 제안

## Constraints
- Technical: AWS Bedrock 기반, AgentCore 활용
- Time: 로컬 5분, AWS 30분 배포 목표
- Resources: 최소 비용으로 시작 가능

## Success Criteria
- [x] 로컬 원클릭 설치 (setup.sh)
- [x] AWS CDK 배포 템플릿
- [x] Agent Builder (Kiro CLI) 연동
- [x] 프로젝트 가이드 챗봇 (guide_agent)
- [x] Multi-Agent Supervisor 템플릿
- [x] QUICKSTART 문서 (로컬/AWS)

## Current Status
- Session: Mickey 24
- Progress: v1.8 KB 자동 생성 + Sync ✅ 완료
- AWS 배포: ✅ E2E 검증 완료 (us-east-1)
- 로컬 환경: ✅ 동작 확인
- 테스트: ✅ 15/15 통과
- 문서: ✅ QUICKSTART x2, TUTORIAL x3, BEST-PRACTICES, TROUBLESHOOTING
- 사례 학습: ✅ save_case 도구 + 피드백 기반 사례 제안 (로컬)
- 리팩토링: ✅ 모델 ID 10곳 + region 20곳 → config/환경변수 추출 완료

## Roadmap

```
v1.3 자동 개선              ████████████ 100% ✅
스타터 킷 패키징            ████████████ 100% ✅
AWS 배포 E2E                ████████████ 100% ✅
코드 리팩토링               ████████████ 100% ✅
v1.4 Kiro CLI Agent 체계화  ████████████ 100% ✅
v1.5 MCP 연동 지원          ████████████ 100% ✅
v1.6 Template UI 개선       ████████████ 100% ✅
v1.7 AWS 배포 기반+매뉴얼   ████████████ 100% ✅
v1.8 KB 자동 생성+Sync      ████████████ 100% ✅
v2.0 스케줄러/알림           ░░░░░░░░░░░░   0%
```

### v1.4 - Kiro CLI Agent 체계화 (1-2일)
- deployment-agent + review-agent 생성
- agent-builder 개선 (delegate 패턴: 배포 요청 시 review → deployment)
- Kiro CLI use_subagent로 Agent 간 위임

### v1.5 - MCP 연동 지원 (2-3일)
- 기존 Python 도구 유지 + MCP 연동 패턴 추가
- AgentCore Gateway MCP 예시, TUTORIAL-MCP-AGENT.md
- Agent Builder가 MCP 연동 Agent도 생성 가능하게

### v1.6 - Template UI 개선 (완료)
- 추론 과정 표시 (Strands Hooks → ToolCallTracker)
- 피드백 버튼 (cl.Action → 로컬 JSON / AWS DynamoDB)
- 동적 환영 메시지 (supervisor의 ask_*_agent 자동 감지)
- 뉴스 Agent 시나리오 + 튜토리얼
- URL/링크 보존 3계층 원칙

### v1.7 - AWS 배포 기반 + 배포 워크플로 매뉴얼 (2-3일)

로컬에서 만든 agent를 AWS에 배포할 수 있는 기반과, agent-builder/스크립트로 배포하는 방법 및 매뉴얼을 만든다.

사용자 시나리오:
1. 리포 클론 → agent-builder로 로컬에서 agent 생성/활용
2. 프로덕션 준비되면 agent-builder 또는 스크립트로 AWS 배포
3. AWS 환경에서도 agent-builder로 새 agent 생성

#### 1단계: AWS template 개선
- feedback_store.py: 환경변수(`FEEDBACK_STORAGE`)로 로컬 JSON / DynamoDB 자동 전환
- CDK infrastructure_stack.py: DynamoDB 피드백 테이블 추가
- CDK agentcore_stack.py: 환경변수 추가 (FEEDBACK_STORAGE, FEEDBACK_TABLE)
- deploy.sh: agent 코드 경로를 유연하게 (기본 template + 커스텀 agent 지원)

#### 2단계: agent-builder 배포 워크플로 구축
- agent-builder.json: AWS template 참조 리소스 추가, 배포 관련 지침 보강
- agent-builder-guide.md: AWS 배포 섹션 추가 (로컬→AWS 전환 가이드)
- deployment-agent.json: 새 agent 추가 배포 시나리오 지원
- deployment-guide.md: 새 agent 추가 배포 절차 추가

#### 3단계: 매뉴얼 작성
- QUICKSTART-AWS.md 업데이트
- "로컬 agent → AWS 배포" 튜토리얼 (news-agent를 예시로)
- agent-builder를 통한 AWS 배포 시나리오 문서

#### 4단계: 검증
- 매뉴얼대로 agent-builder로 news-agent AWS 배포 시나리오 테스트
- 발견된 이슈 수정

### v1.8 - KB 자동 생성 + Sync 파이프라인 (3-5일)

처음 접하는 사용자가 KB를 수동 생성 없이 Agent를 AWS에 바로 배포할 수 있도록 한다.
(참고: https://aws.amazon.com/ko/blogs/tech/agentic-ai-foundation-platform-part1/)

#### KB 자동 생성
- CreateKnowledgeBase + CreateDataSource API 활용
- IAM Role 자동 생성 (CDK)
- 벡터 스토어 설정 (OpenSearch Serverless 또는 S3 Vectors)
- 임베딩 모델 설정
- deploy.sh에 KB 생성 단계 추가

#### 자동 Sync 파이프라인
- S3 PUT 이벤트 → SQS → Lambda → StartIngestionJob
- CDK 스택에 SQS + Lambda 리소스 추가

#### Agent Builder 연동
- Agent 생성 시 KB 자동 생성 옵션
- KB ID 자동 연결

### v2.0 - 스케줄러/알림
- EventBridge + Lambda 스케줄러
- Slack/이메일 알림 연동

## Last Updated
Mickey 24 - 2026-02-21
