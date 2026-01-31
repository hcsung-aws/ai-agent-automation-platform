# Agent Builder Guide

## 목적
자연어 명령으로 새 Agent를 생성하고 Supervisor에 연결

## 워크플로우

```
사용자: "HR Agent 만들어줘. 휴가 신청, 직원 조회 기능으로"
                    ↓
1. 도구 파일 생성: src/tools/{name}_tools.py
2. Agent 파일 생성: src/agent/{name}_agent.py
3. Supervisor 수정: supervisor_agent.py
4. 테스트 안내
```

---

## 도구 템플릿

```python
"""[Name] Tools - [Description]."""
from strands import tool

@tool
def tool_name(param: str) -> str:
    """도구 설명.
    
    Args:
        param: 파라미터 설명
    
    Returns:
        반환값 설명
    """
    # 구현
    return "결과"
```

**규칙:**
- `@tool` 데코레이터 필수
- docstring에 Args, Returns 명시 (Agent가 도구 선택 시 참조)
- 반환값은 항상 `str`

---

## Agent 템플릿

```python
"""[Name] Agent - [Description]."""
from strands import Agent
from strands.models import BedrockModel

from src.tools.{name}_tools import tool1, tool2

SYSTEM_PROMPT = """당신은 [역할] 전문가 AI 에이전트입니다.

주요 역할:
1. [역할 1]
2. [역할 2]

응답 원칙:
- 한국어로 응답
- [추가 원칙]
"""

def create_{name}_agent() -> Agent:
    """Create and return [Name] Agent instance."""
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
    )
    
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[tool1, tool2],
    )
```

---

## Supervisor 연결

### 1. Import 추가
```python
from src.agent.{name}_agent import create_{name}_agent
```

### 2. Lazy initialization 추가
```python
_{name}_agent = None

def _get_{name}_agent():
    global _{name}_agent
    if _{name}_agent is None:
        _{name}_agent = create_{name}_agent()
    return _{name}_agent
```

### 3. Tool 함수 추가
```python
@tool
def ask_{name}_agent(query: str) -> str:
    """[Name] 전문가 에이전트에게 질문합니다.
    
    [담당 영역 설명]
    
    Args:
        query: [Name] 관련 질문 또는 요청
    
    Returns:
        [Name] Agent의 응답
    """
    global _current_sub_agents
    _current_sub_agents.append("{name}")
    agent = _get_{name}_agent()
    response = agent(query)
    return str(response)
```

### 4. tools 배열에 추가
```python
agent = Agent(
    ...
    tools=[
        ask_devops_agent,
        ask_analytics_agent,
        ask_{name}_agent,  # 추가
    ],
)
```

### 5. SYSTEM_PROMPT에 설명 추가
```
### [Name] Agent (ask_{name}_agent)
담당 영역:
- [영역 1]
- [영역 2]
```

---

## 체크리스트

생성 완료 후 확인:
- [ ] src/tools/{name}_tools.py 생성됨
- [ ] src/agent/{name}_agent.py 생성됨
- [ ] supervisor_agent.py에 import 추가됨
- [ ] supervisor_agent.py에 _get_{name}_agent() 추가됨
- [ ] supervisor_agent.py에 ask_{name}_agent() 추가됨
- [ ] supervisor_agent.py의 tools 배열에 추가됨
- [ ] supervisor_agent.py의 SYSTEM_PROMPT에 설명 추가됨

---

## 테스트 명령어

```bash
# Agent 실행
chainlit run app.py --port 8000

# 테스트 질문
"[Name] Agent에게 [테스트 질문]"
```

---

## 참고 파일

기존 구현 참고:
- src/agent/devops_agent.py
- src/agent/analytics_agent.py
- src/agent/supervisor_agent.py
- src/tools/cloudwatch_tools.py
