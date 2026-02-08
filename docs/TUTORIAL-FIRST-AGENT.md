# 튜토리얼: 자연어로 첫 Agent 만들기

이 튜토리얼에서는 **코드를 직접 작성하지 않고** Agent Builder를 활용하여 Agent를 만듭니다.

예상 소요 시간: 30분

---

## 사전 준비

### 로컬 환경 실행 확인

```bash
cd templates/local
source .venv/bin/activate
chainlit run app.py --port 8000
```

→ 아직 안 했다면 [QUICKSTART-LOCAL.md](QUICKSTART-LOCAL.md) 먼저 진행

### Agent Builder란?

Kiro CLI에서 동작하는 커스텀 Agent로, 자연어 명령을 받아 Agent 코드를 자동 생성합니다.

```
사용자: "HR Agent 만들어줘"
    ↓
Agent Builder가 자동으로:
1. agents/hr_agent.py 생성 (도구 + Agent 포함)
2. agents/supervisor.py 수정 (연결)
```

### Agent Builder 실행

프로젝트에 `templates/local/agent-builder.json`이 이미 포함되어 있습니다.

```bash
# 프로젝트 루트에서
kiro chat --agent agent-builder
```

---

## 시나리오

"휴가 잔여일을 조회하는 HR Agent"를 만들어봅니다.

최종 목표:
```
사용자: "내 휴가 잔여일 알려줘"
HR Agent: "홍길동님의 휴가 잔여일은 12일입니다."
```

---

## Step 1: 업무 정의 (5분)

Agent를 만들기 전에 **어떤 업무를 자동화할지** 명확히 합니다.

### 좋은 첫 번째 업무의 조건

| 조건 | 설명 |
|------|------|
| ✅ 단순함 | 입력 → 조회 → 출력 형태 |
| ✅ 반복적 | 자주 발생하는 요청 |
| ✅ API 가능 | 프로그래밍으로 자동화 가능 |
| ✅ 저위험 | 실패해도 큰 영향 없음 |

### 예시

```
좋은 예:
- "휴가 잔여일 조회" → 단순 조회
- "CloudWatch 알람 목록" → 단순 조회
- "오늘 DAU" → 단순 조회

나쁜 예 (나중에):
- "휴가 자동 승인" → 의사결정 포함
- "서버 자동 스케일링" → 위험한 작업
```

---

## Step 2: Agent Builder에게 요청 (10분)

### Agent Builder 시작

```bash
kiro chat --agent agent-builder
```

### 기본 요청

```
"HR Agent를 만들어줘. 휴가 잔여일 조회 기능이 필요해."
```

### Agent Builder의 응답

Agent Builder가 다음을 확인합니다:

```
HR Agent를 만들겠습니다.

확인 사항:
1. 휴가 잔여일은 어디서 조회하나요?
   - HR 시스템 API
   - 데이터베이스
   - 임시로 하드코딩 (테스트용)

2. 직원 식별은 어떻게 하나요?
   - 직원 ID 입력
   - 이름으로 검색

어떤 방식으로 진행할까요?
```

### 상세 요청

```
"테스트용으로 하드코딩해줘. 직원 ID를 입력받아서 조회하는 방식으로."
```

### Agent Builder의 계획 제시

```
HR Agent 생성 계획:

생성할 파일:
- templates/local/agents/hr_agent.py (도구 + Agent)

수정할 파일:
- templates/local/agents/supervisor.py (Supervisor 연결)

진행할까요?
```

---

## Step 3: 생성된 코드 확인 (5분)

Agent Builder가 생성한 파일을 확인합니다.

### Agent 파일 (`templates/local/agents/hr_agent.py`)

도구와 Agent가 하나의 파일에 정의됩니다 (guide_agent.py와 동일한 패턴):

```python
"""HR Agent - 인사 업무 전문가."""
from strands import Agent, tool
from strands.models import BedrockModel

# 테스트용 데이터
LEAVE_DATA = {
    "E001": {"name": "홍길동", "remaining": 12},
    "E002": {"name": "김철수", "remaining": 8},
    "E003": {"name": "이영희", "remaining": 15},
}


@tool
def get_leave_balance(employee_id: str) -> str:
    """직원의 휴가 잔여일을 조회합니다.
    
    Args:
        employee_id: 직원 ID (예: E001)
    
    Returns:
        휴가 잔여일 정보
    """
    if employee_id in LEAVE_DATA:
        data = LEAVE_DATA[employee_id]
        return f"{data['name']}님의 휴가 잔여일은 {data['remaining']}일입니다."
    return f"직원 ID '{employee_id}'를 찾을 수 없습니다."


SYSTEM_PROMPT = """당신은 HR 업무를 담당하는 AI 에이전트입니다.

주요 역할:
1. 휴가 잔여일 조회 - get_leave_balance 도구 사용

응답 원칙:
- 한국어로 응답
- 직원 ID가 없으면 요청
- 친절하고 명확하게 안내
"""


def create_hr_agent() -> Agent:
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
    )
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_leave_balance],
    )
```

### Supervisor 연결 (`templates/local/agents/supervisor.py`)

Agent Builder가 supervisor.py에 다음을 추가합니다:

```python
# 추가된 부분
_hr_agent = None

def _get_hr_agent():
    global _hr_agent
    if _hr_agent is None:
        from hr_agent import create_hr_agent
        _hr_agent = create_hr_agent()
    return _hr_agent

@tool
def ask_hr_agent(query: str) -> str:
    """HR 관련 질문을 HR Agent에게 전달합니다.
    
    휴가 잔여일, 직원 정보 등 인사 관련 질문에 사용합니다.
    
    Args:
        query: HR 관련 질문
    """
    agent = _get_hr_agent()
    return str(agent(query))

# tools 배열에 ask_hr_agent 추가
# SYSTEM_PROMPT에 HR Agent 설명 추가
```

---

## Step 4: 테스트 (5분)

### 실행

```bash
cd templates/local
chainlit run app.py --port 8000
```

### 테스트 질문

```
"E001 직원의 휴가 잔여일 알려줘"
```

### 예상 응답

```
HR Agent에게 확인했습니다.
홍길동님의 휴가 잔여일은 12일입니다.
```

---

## Step 5: 기능 확장 (자연어로)

Agent Builder를 다시 실행하여 기능을 확장합니다.

### 도구 추가 요청

```
"HR Agent에 직원 목록 조회 기능도 추가해줘"
```

Agent Builder가 `hr_agent.py`에 새 도구를 추가합니다:

```python
@tool
def list_employees() -> str:
    """전체 직원 목록을 조회합니다."""
    result = "직원 목록:\n"
    for emp_id, data in LEAVE_DATA.items():
        result += f"- {emp_id}: {data['name']}\n"
    return result
```

### 시스템 프롬프트 개선 요청

```
"HR Agent가 직원 ID 없이 이름만 말해도 찾을 수 있게 해줘"
```

Agent Builder가 도구와 프롬프트를 수정합니다.

---

## Step 6: 실제 시스템 연동 (선택)

테스트가 완료되면 실제 HR 시스템과 연동합니다.

### 연동 요청

```
"HR Agent의 휴가 조회를 실제 HR API와 연동해줘.
API 엔드포인트는 https://hr-api.company.com/leave/{employee_id} 이고,
Authorization 헤더에 Bearer 토큰이 필요해."
```

Agent Builder가 도구를 수정합니다:

```python
@tool
def get_leave_balance(employee_id: str) -> str:
    """직원의 휴가 잔여일을 조회합니다."""
    import requests
    import os
    
    token = os.environ.get("HR_API_TOKEN")
    response = requests.get(
        f"https://hr-api.company.com/leave/{employee_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        return f"{data['name']}님의 휴가 잔여일은 {data['remaining']}일입니다."
    return f"조회 실패: {response.status_code}"
```

---

## 핵심 포인트

### 파일 구조 패턴

```
templates/local/agents/
├── supervisor.py      # Supervisor (Agent 조율)
├── guide_agent.py     # 프로젝트 가이드 (기본 제공)
└── hr_agent.py        # ← Agent Builder가 생성
```

하나의 Agent 파일에 **도구 + Agent**가 함께 정의됩니다.

### 자연어로 할 수 있는 것

| 작업 | 예시 요청 |
|------|----------|
| Agent 생성 | "HR Agent 만들어줘" |
| 도구 추가 | "직원 검색 기능 추가해줘" |
| 도구 수정 | "API 연동으로 바꿔줘" |
| 프롬프트 개선 | "더 친절하게 응답하게 해줘" |
| KB 연동 | "HR 정책 문서를 KB로 연결해줘" |

### 직접 해야 하는 것

| 작업 | 이유 |
|------|------|
| 환경 변수 설정 | 보안상 자동화 불가 |
| AWS 리소스 생성 | 권한/비용 문제 |

---

## Agent Builder 활용 팁

### 1. 구체적으로 요청하기

```
❌ "Agent 만들어줘"
✅ "CloudWatch 알람을 조회하고 심각도별로 분류하는 Monitoring Agent 만들어줘"
```

### 2. 단계별로 진행하기

```
1단계: "기본 조회 기능만 있는 Agent 만들어줘"
2단계: "필터링 기능 추가해줘"
3단계: "실제 API 연동해줘"
```

### 3. 기존 패턴 참조 요청

```
"guide_agent.py 패턴을 참고해서 만들어줘"
```

### 4. 테스트 후 개선 요청

```
"테스트해봤는데 직원 ID가 없을 때 에러가 나. 예외 처리 추가해줘"
```

---

## 다음 단계

Agent가 동작하면 **피드백 루프**를 설정하여 지속적으로 개선합니다.

→ [TUTORIAL-FEEDBACK.md](TUTORIAL-FEEDBACK.md)
