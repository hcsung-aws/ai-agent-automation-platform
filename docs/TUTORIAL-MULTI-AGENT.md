# 튜토리얼: Multi-Agent 구성

단일 Agent가 안정화되면 **여러 Agent가 협업하는 구조**로 확장합니다.

예상 소요 시간: 30분

---

## Multi-Agent 아키텍처

```
┌─────────────────────────────────────────┐
│              Supervisor                  │
│         (요청 분석 및 위임)              │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ↓             ↓             ↓
┌───────┐   ┌───────┐   ┌───────┐
│  HR   │   │DevOps │   │  ...  │
│ Agent │   │ Agent │   │ Agent │
└───────┘   └───────┘   └───────┘
```

### Supervisor 역할
- 사용자 요청 분석
- 적절한 전문 Agent에게 위임
- 여러 Agent 결과 종합

### 전문 Agent 역할
- 특정 영역의 도구 보유
- 해당 영역 질문에 응답

---

## Step 1: 두 번째 Agent 생성 (10분)

HR Agent가 있다고 가정하고, DevOps Agent를 추가합니다.

### Agent Builder에게 요청

```bash
kiro chat --agent agent-builder
```

```
"DevOps Agent를 만들어줘. CloudWatch 알람 조회, EC2 상태 확인 기능이 필요해."
```

### 생성 결과

```
생성 완료:
- src/tools/devops_tools.py
- src/agent/devops_agent.py
- src/agent/supervisor_agent.py (수정됨)
```

---

## Step 2: Supervisor 연결 확인 (5분)

Agent Builder가 자동으로 Supervisor를 수정하지만, 확인이 필요합니다.

### supervisor_agent.py 확인 사항

```python
# 1. Import 추가됨
from src.agent.hr_agent import create_hr_agent
from src.agent.devops_agent import create_devops_agent

# 2. 위임 도구 추가됨
@tool
def ask_hr_agent(query: str) -> str:
    """HR 관련 질문을 HR Agent에게 전달합니다."""
    ...

@tool
def ask_devops_agent(query: str) -> str:
    """DevOps 관련 질문을 DevOps Agent에게 전달합니다."""
    ...

# 3. tools 배열에 추가됨
tools=[ask_hr_agent, ask_devops_agent]

# 4. SYSTEM_PROMPT에 설명 추가됨
"""
### HR Agent (ask_hr_agent)
담당: 휴가 조회, 직원 정보

### DevOps Agent (ask_devops_agent)
담당: CloudWatch 알람, EC2 상태
"""
```

---

## Step 3: 테스트 (10분)

### 단일 Agent 질문

```
"E001 직원 휴가 잔여일 알려줘"
→ Supervisor가 HR Agent에게 위임
```

```
"CloudWatch 알람 목록 보여줘"
→ Supervisor가 DevOps Agent에게 위임
```

### 복합 질문

```
"서버 장애가 있는지 확인하고, 담당자 휴가 여부도 알려줘"
→ Supervisor가 DevOps Agent → HR Agent 순차 호출
```

---

## Step 4: Supervisor 프롬프트 최적화 (5분)

### 위임 규칙 명확화

Agent Builder에게 요청:

```
"Supervisor가 HR/DevOps 질문을 더 정확하게 구분하도록 프롬프트 개선해줘"
```

### 개선된 프롬프트 예시

```
## 위임 규칙

### HR Agent (ask_hr_agent)
키워드: 휴가, 직원, 급여, 인사, 채용
예시: "휴가 잔여일", "직원 정보", "급여 명세"

### DevOps Agent (ask_devops_agent)
키워드: 서버, 알람, EC2, 배포, 장애
예시: "서버 상태", "알람 목록", "배포 이력"

### 복합 요청
여러 영역이 필요하면 순차적으로 각 Agent 호출 후 결과 종합
```

---

## Multi-Agent 확장 패턴

### 패턴 1: 영역별 분리

```
Supervisor
├── HR Agent (인사)
├── DevOps Agent (인프라)
├── Analytics Agent (데이터)
└── Finance Agent (재무)
```

### 패턴 2: 기능별 분리

```
Supervisor
├── Query Agent (조회)
├── Action Agent (실행)
└── Report Agent (리포트)
```

### 패턴 3: 계층적 구조

```
Supervisor
├── Operations Supervisor
│   ├── DevOps Agent
│   └── Security Agent
└── Business Supervisor
    ├── HR Agent
    └── Finance Agent
```

---

## 주의사항

### 1. Agent 수 제한

- 권장: 3-5개
- 너무 많으면 Supervisor가 혼란

### 2. 영역 중복 방지

```
❌ HR Agent: 직원 정보 조회
   Admin Agent: 직원 정보 조회  (중복!)

✅ HR Agent: 휴가, 급여
   Admin Agent: 권한, 계정
```

### 3. 명확한 위임 규칙

```
❌ "적절한 Agent에게 위임"
✅ "휴가/급여 키워드 → HR Agent"
```

---

## 다음 단계

Multi-Agent가 안정화되면 **실패 사례와 교훈**을 정리합니다.

→ [BEST-PRACTICES.md](BEST-PRACTICES.md)
