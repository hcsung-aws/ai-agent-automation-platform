# 빠른 시작 가이드 (30분)

이 가이드를 따라하면 30분 안에:
1. 환경 설정 완료
2. 샘플 Agent 실행
3. Agent Builder로 나만의 Agent 생성 시작

---

## 1. 환경 설정 (10분)

### 사전 요구사항
- Python 3.10+
- AWS CLI 설정 완료
- AWS Bedrock 접근 권한 (us-east-1)

### 설치

```bash
# 저장소 클론
git clone https://github.com/hcsung-aws/ai-agent-automation-platform.git
cd ai-agent-automation-platform

# 가상환경 설정
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### AWS 설정 확인

```bash
# Bedrock 접근 테스트
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[?contains(modelId, `claude`)].modelId' --output table
```

Claude 모델이 보이면 준비 완료!

---

## 2. 샘플 Agent 실행 (5분)

```bash
# Chainlit UI 실행
chainlit run app.py --port 8000
```

브라우저에서 `http://localhost:8000` 접속 후 테스트:

```
"안녕하세요"
"서버 상태 확인해줘"
"오늘 DAU 알려줘"
```

> 💡 DynamoDB 테이블이 없으면 일부 기능이 동작하지 않습니다. 
> 전체 기능 테스트는 [배포 가이드](DEPLOYMENT.md)를 참고하세요.

---

## 3. Agent Builder 소개 (5분)

이 프로젝트의 핵심은 **자연어로 Agent를 만드는 것**입니다.

### Agent Builder란?

코드를 직접 작성하지 않고, 자연어 명령으로 Agent를 생성/수정하는 도구입니다.

```
사용자: "HR Agent 만들어줘. 휴가 조회 기능으로"
    ↓
Agent Builder가 자동으로:
1. src/tools/hr_tools.py 생성
2. src/agent/hr_agent.py 생성
3. Supervisor에 연결
```

### Agent Builder 설정

Kiro CLI를 사용하는 경우, Agent Builder가 이미 설정되어 있습니다:
- 설정 파일: `~/.kiro/agents/agent-builder.json`
- 가이드 문서: `context_rule/agent-builder-guide.md`

---

## 4. 첫 번째 Agent 만들기 (10분)

### 예시: 간단한 조회 Agent

Kiro CLI에서 다음과 같이 요청합니다:

```
"CloudWatch 알람을 조회하는 간단한 Monitoring Agent를 만들어줘"
```

Agent Builder가 다음을 수행합니다:

1. **도구 생성** (`src/tools/monitoring_tools.py`)
```python
@tool
def get_cloudwatch_alarms() -> str:
    """CloudWatch 알람 목록을 조회합니다."""
    # AWS API 호출 코드
```

2. **Agent 생성** (`src/agent/monitoring_agent.py`)
```python
agent = Agent(
    model=model,
    system_prompt="당신은 모니터링 전문가입니다...",
    tools=[get_cloudwatch_alarms],
)
```

3. **Supervisor 연결**
```python
# supervisor_agent.py에 자동 추가
@tool
def ask_monitoring_agent(query: str) -> str:
    ...
```

### 테스트

```bash
chainlit run app.py --port 8000
```

```
"Monitoring Agent에게 알람 목록 보여달라고 해줘"
```

---

## 다음 단계

| 목표 | 가이드 |
|------|--------|
| 자연어로 Agent 만들기 상세 | [TUTORIAL-FIRST-AGENT.md](TUTORIAL-FIRST-AGENT.md) |
| 피드백 루프 설정 | [TUTORIAL-FEEDBACK.md](TUTORIAL-FEEDBACK.md) |
| Multi-Agent 구성 | [TUTORIAL-MULTI-AGENT.md](TUTORIAL-MULTI-AGENT.md) |
| 실패 사례와 교훈 | [BEST-PRACTICES.md](BEST-PRACTICES.md) |

---

## 핵심 원칙

```
"코드를 직접 작성하지 마세요. Agent Builder에게 시키세요."

1. 자연어로 원하는 기능 설명
2. Agent Builder가 코드 생성
3. 테스트 후 피드백
4. 피드백 기반으로 개선 요청
```

이 사이클을 반복하면 코드를 거의 건드리지 않고도 원하는 Agent를 만들 수 있습니다.
