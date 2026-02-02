# AI Agent 기반 업무 자동화 플랫폼 구축 가이드

[English](#english-version) | 한국어

## 이 프로젝트는 무엇인가요?

**어떤 조직, 어떤 업무에도 적용 가능한 AI Agent 시스템 구축 템플릿**입니다.

이 가이드를 따라하면:
- 자연어로 업무를 지시할 수 있는 AI Agent를 만들 수 있습니다
- 여러 전문 Agent가 협업하는 Multi-Agent 시스템을 구축할 수 있습니다
- 실행 기록을 바탕으로 Agent를 점진적으로 개선할 수 있습니다

> **PoC 예시**: 이 저장소에는 게임 운영(DevOps + 데이터분석) Agent가 예시로 포함되어 있습니다. 이를 참고하여 여러분의 업무에 맞는 Agent를 만들어보세요.

---

## 핵심 아이디어: 점진적 자동화

```
┌─────────────────────────────────────────────────────────────────┐
│                    점진적 자동화 사이클                           │
│                                                                 │
│   1. 사람이 Agent에게 업무 지시                                  │
│          ↓                                                      │
│   2. Agent가 도구를 활용하여 업무 수행                           │
│          ↓                                                      │
│   3. 실행 기록 저장 및 사람의 검토                               │
│          ↓                                                      │
│   4. 검토 결과를 Knowledge Base/지침/도구로 반영                 │
│          ↓                                                      │
│   5. 개선된 Agent가 더 나은 업무 수행 (1번으로 반복)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 왜 이 방식인가?

| 기존 자동화 | Agent 기반 자동화 |
|------------|------------------|
| 모든 케이스를 미리 정의 | 자연어로 유연하게 지시 |
| 변경 시 코드 수정 필요 | Knowledge Base 업데이트로 대응 |
| 예외 상황 처리 어려움 | LLM이 맥락 파악하여 판단 |
| 초기 구축 비용 높음 | 점진적으로 확장 가능 |

---

## 나만의 Agent 만들기 (5단계)

### Step 1: 업무 영역 정의

먼저 Agent가 담당할 업무 영역을 정의합니다.

```
예시:
- HR Agent: 휴가 신청, 급여 문의, 채용 프로세스
- 재무 Agent: 비용 승인, 예산 조회, 결산 리포트
- 고객지원 Agent: FAQ 응답, 티켓 분류, 에스컬레이션
- DevOps Agent: 서버 모니터링, 배포 관리, 장애 대응 (PoC 예시)
```

### Step 2: 도구(Tool) 구현

Agent가 사용할 도구를 Python 함수로 구현합니다.

```python
# src/tools/my_tools.py
from strands import tool

@tool
def get_employee_info(employee_id: str) -> str:
    """직원 정보를 조회합니다.
    
    Args:
        employee_id: 직원 ID
    
    Returns:
        직원 정보 (이름, 부서, 직급)
    """
    # 실제 HR 시스템 API 호출
    return f"직원 {employee_id}: 홍길동, 개발팀, 선임"

@tool
def submit_leave_request(employee_id: str, start_date: str, end_date: str, reason: str) -> str:
    """휴가를 신청합니다.
    
    Args:
        employee_id: 직원 ID
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        reason: 휴가 사유
    
    Returns:
        신청 결과
    """
    # 실제 휴가 시스템 API 호출
    return f"휴가 신청 완료: {start_date} ~ {end_date}"
```

> **Tip**: 도구의 docstring이 중요합니다. Agent는 이 설명을 보고 어떤 도구를 사용할지 결정합니다.

### Step 3: Agent 생성

도구를 조합하여 Agent를 만듭니다.

```python
# src/agent/hr_agent.py
from strands import Agent
from strands.models import BedrockModel
from src.tools.my_tools import get_employee_info, submit_leave_request

SYSTEM_PROMPT = """당신은 HR 업무를 담당하는 AI 에이전트입니다.

주요 역할:
1. 직원 정보 조회
2. 휴가 신청 처리
3. HR 정책 안내

응답 원칙:
- 한국어로 응답
- 개인정보는 본인 확인 후 제공
- 불확실한 내용은 HR팀 문의 안내
"""

def create_hr_agent() -> Agent:
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
    )
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_employee_info, submit_leave_request],
    )
```

### Step 4: Multi-Agent 구성 (선택)

여러 Agent가 협업하도록 Supervisor를 구성합니다.

```python
# src/agent/supervisor_agent.py
from strands import Agent, tool

@tool
def ask_hr_agent(query: str) -> str:
    """HR 관련 질문을 HR Agent에게 전달합니다."""
    agent = create_hr_agent()
    return str(agent(query))

@tool
def ask_finance_agent(query: str) -> str:
    """재무 관련 질문을 Finance Agent에게 전달합니다."""
    agent = create_finance_agent()
    return str(agent(query))

# Supervisor Agent 생성
supervisor = Agent(
    model=model,
    system_prompt="사용자 요청을 분석하여 적절한 전문 Agent에게 위임합니다.",
    tools=[ask_hr_agent, ask_finance_agent],
)
```

### Step 5: 실행 및 개선

```bash
# Agent 실행
chainlit run app.py

# 실행 기록 확인
python logs_api.py
```

---

## 프로젝트 구조

```
ai-agent-platform/
├── app.py                      # Chainlit UI 진입점
├── logs_api.py                 # 실행 기록 조회 API
├── src/
│   ├── agent/
│   │   ├── supervisor_agent.py # Supervisor (Multi-Agent 조율)
│   │   └── [your]_agent.py     # 전문가 Agent
│   ├── tools/
│   │   └── [your]_tools.py     # 업무별 도구
│   └── utils/
│       └── execution_logger.py # 실행 기록
├── scripts/                    # 설정 스크립트
├── infra/
│   ├── stacks/                 # CDK 스택
│   └── terraform/              # Terraform 설정
└── docs/
    ├── DEPLOYMENT.md           # 배포 가이드
    ├── ROADMAP.md              # 로드맵
    └── kb/                     # Knowledge Base 문서
```

---

## 설치 및 실행

### 사전 요구사항

- Python 3.10+
- AWS CLI 설정 완료 (Bedrock 접근 권한 필요)
- AWS 계정 (us-east-1 리전)

### 로컬 환경

```bash
# 1. 저장소 클론
git clone https://github.com/hcsung-aws/ai-agent-automation-platform.git
cd ai-agent-automation-platform

# 2. 가상환경 설정
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. Agent 실행 (PoC 예시)
chainlit run app.py
```

### AWS 환경 배포

```bash
# CDK 배포
cd infra && cdk deploy

# 또는 Terraform 배포
cd infra/terraform && terraform init && terraform apply
```

상세 가이드: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 점진적 개선 가이드

### Phase 1: 도입기

| 활동 | 설명 |
|------|------|
| 기본 질문 테스트 | 간단한 조회 업무부터 시작 |
| 실행 기록 검토 | 주 1회 로그 검토하여 개선점 파악 |
| KB 문서 작성 | 자주 묻는 질문에 대한 가이드 추가 |

**주의사항**:
- Agent 응답을 맹신하지 말고 검증 필요
- 중요한 작업은 확인 후 실행
- 민감한 정보는 KB에 포함하지 않기

### Phase 2: 확장기

| 활동 | 설명 |
|------|------|
| 새 도구 추가 | 반복 업무를 도구로 구현 |
| 지침 고도화 | System Prompt에 업무 규칙 추가 |
| 복합 시나리오 | 여러 Agent 협업 시나리오 구현 |

### Phase 3: 자동화기

| 활동 | 설명 |
|------|------|
| 스케줄 실행 | 정기 리포트 자동 생성 |
| 알림 연동 | Slack/이메일 알림 추가 |
| 승인 워크플로우 | 중요 작업은 사람 승인 후 실행 |

---

## PoC 예시: 게임 운영 Agent

이 저장소에는 게임 운영 시나리오의 PoC가 포함되어 있습니다.

### DevOps Agent (6개 도구)
- CloudWatch 메트릭 조회
- EC2 인스턴스 상태 확인
- CloudFormation 배포 이력
- 장애 티켓 생성/조회
- 운영 가이드 검색 (KB)

### Analytics Agent (10개 도구)
- Athena SQL 쿼리 실행
- 가챠 확률 분석
- 재화 흐름 분석
- 유저 리텐션 분석
- 퀘스트/출석 현황

### 테스트 방법

```bash
# 샘플 데이터 생성
python scripts/setup_mmorpg_tables.py

# Agent 실행
chainlit run app.py

# 질문 예시
"장애 티켓 목록 보여줘"
"가챠 등급별 확률 분석해줘"
```

---

## 로드맵

상세 계획: [docs/ROADMAP.md](docs/ROADMAP.md)

### v1.0 - 기본 템플릿 ✅
- [x] Multi-Agent 협업 구조
- [x] 실행 기록 저장
- [x] CDK/Terraform 배포 스크립트
- [x] PoC 예시 (DevOps + Analytics)

### v1.1 - 피드백 수집 ✅
- [x] 👍/👎 피드백 버튼
- [x] 피드백 저장 (DynamoDB)
- [x] 피드백 조회 API + 대시보드
- [x] 중복 방지 + 변경 기능

### v1.2 - Agent Builder Agent ✅
- [x] Agent Builder Kiro Agent 구현 (`~/.kiro/agents/agent-builder.json`)
- [x] 생성 가이드 작성 (`context_rule/agent-builder-guide.md`)
- [x] 자연어로 Agent 생성 테스트 (Godot Review Agent)
- [x] 기존 Agent 수정 기능 (KB 연동 패턴 추가)
- [x] 상세 보기 버튼 (Supervisor 요약 + 전체 응답 확인)

### v1.3 - 자동 개선 제안 (피드백 축적 후)
- [ ] 실패 패턴 분석
- [ ] KB 문서 자동 제안
- [ ] System Prompt 개선 제안

### v2.0 - 자동화 워크플로우
- [ ] 스케줄러 (일/주간 자동 분석)
- [ ] 알림 연동 (Slack/이메일)

### v3.0 - 프로덕션
- [ ] 인증/권한 관리
- [ ] AgentCore 런타임 배포

---

## 기여 방법

1. 이슈 등록 또는 기존 이슈 확인
2. Fork 후 feature 브랜치 생성
3. 변경사항 커밋
4. Pull Request 생성

---

## 이 프로젝트는 어떻게 만들어졌나요?

이 프로젝트는 **AI 개발자 Mickey**를 활용하여 만들어졌습니다.

Mickey는 Kiro CLI용 커스텀 Agent로, 세션 간 지속성을 유지하며 점진적으로 개선되는 AI 개발 에이전트입니다. 저장소에 포함된 `MICKEY-*-SESSION.md` 파일들은 Mickey가 이 프로젝트를 개발하면서 남긴 세션 기록입니다.

Mickey에 대해 더 알아보기: [github.com/hcsung-aws/ai-developer-mickey](https://github.com/hcsung-aws/ai-developer-mickey)

---

## 라이선스

MIT License

---

# English Version

## What is this project?

**A template for building AI Agent systems applicable to any organization and any workflow.**

By following this guide, you can:
- Create AI Agents that accept natural language instructions
- Build Multi-Agent systems where specialists collaborate
- Gradually improve Agents based on execution logs

> **PoC Example**: This repository includes a game operations (DevOps + Analytics) Agent as an example. Use it as a reference to build Agents for your own workflows.

---

## Core Concept: Gradual Automation

```
┌─────────────────────────────────────────────────────────────────┐
│                 Gradual Automation Cycle                         │
│                                                                 │
│   1. Human instructs Agent on tasks                             │
│          ↓                                                      │
│   2. Agent performs tasks using tools                           │
│          ↓                                                      │
│   3. Execution logs saved & reviewed by humans                  │
│          ↓                                                      │
│   4. Feedback reflected in KB/guidelines/tools                  │
│          ↓                                                      │
│   5. Improved Agent performs better (repeat from 1)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Build Your Own Agent (5 Steps)

### Step 1: Define Scope
Define the business domain your Agent will handle.

### Step 2: Implement Tools
Create Python functions with `@tool` decorator.

```python
from strands import tool

@tool
def my_tool(param: str) -> str:
    """Tool description (Agent reads this to select tools)"""
    return result
```

### Step 3: Create Agent
Combine tools into an Agent with a system prompt.

### Step 4: Multi-Agent Setup (Optional)
Use Agents-as-Tools pattern for collaboration.

### Step 5: Run and Improve
```bash
chainlit run app.py
python logs_api.py  # Review execution logs
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/hcsung-aws/ai-agent-automation-platform.git
cd ai-agent-automation-platform

# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run
chainlit run app.py
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for AWS deployment.

---

## Roadmap

### v1.0 - Basic Template ✅
- [x] Multi-Agent collaboration
- [x] Execution logging
- [x] CDK/Terraform deployment
- [x] PoC example

### v1.1 - Feedback Collection ✅
- [x] 👍/👎 feedback buttons
- [x] Feedback storage (DynamoDB)
- [x] Feedback API + dashboard
- [x] Duplicate prevention + change feature

### v1.2 - Agent Builder Agent ✅
- [x] Agent Builder Kiro Agent (`~/.kiro/agents/agent-builder.json`)
- [x] Builder guide (`context_rule/agent-builder-guide.md`)
- [x] Test Agent creation (Godot Review Agent)
- [x] Modify existing Agent (KB integration pattern)
- [x] Detail view button (Supervisor summary + full response)

### v1.3 - Auto Improvement Suggestions (After feedback accumulation)
- [ ] Failure pattern analysis
- [ ] KB document suggestions
- [ ] System Prompt improvement suggestions

### v2.0 - Automation Workflow
- [ ] Scheduler (daily/weekly auto-analysis)
- [ ] Notifications (Slack/email)

### v3.0 - Production
- [ ] Authentication/Authorization
- [ ] AgentCore runtime deployment

---

## License

MIT License
