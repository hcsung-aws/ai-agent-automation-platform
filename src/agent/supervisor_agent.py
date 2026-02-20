"""Supervisor Agent - Multi-Agent orchestration using Agents-as-Tools pattern."""
import time
from strands import Agent, tool
from strands.models import BedrockModel

from src.config import MODEL_ID, REGION_NAME
from src.agent.devops_agent import create_devops_agent
from src.agent.analytics_agent import create_analytics_agent
from src.agent.godot_review_agent import create_godot_review_agent
from src.agent.monitoring_agent import create_monitoring_agent
from src.tools.feedback_analysis_tools import analyze_negative_feedback
from src.tools.kb_tools import search_common_knowledge, add_kb_document, trigger_kb_sync
from src.utils.execution_logger import log_execution, generate_session_id

# Sub-agents (lazy initialization)
_devops_agent = None
_analytics_agent = None
_godot_review_agent = None
_monitoring_agent = None
_current_tools_used = []
_current_sub_agents = []


def _get_devops_agent():
    global _devops_agent
    if _devops_agent is None:
        _devops_agent = create_devops_agent()
    return _devops_agent


def _get_analytics_agent():
    global _analytics_agent
    if _analytics_agent is None:
        _analytics_agent = create_analytics_agent()
    return _analytics_agent


def _get_godot_review_agent():
    global _godot_review_agent
    if _godot_review_agent is None:
        _godot_review_agent = create_godot_review_agent()
    return _godot_review_agent


def _get_monitoring_agent():
    global _monitoring_agent
    if _monitoring_agent is None:
        _monitoring_agent = create_monitoring_agent()
    return _monitoring_agent


@tool
def ask_devops_agent(query: str) -> str:
    """DevOps 전문가 에이전트에게 질문합니다.
    
    인프라 모니터링, EC2 상태, CloudWatch 메트릭, CloudFormation 배포,
    장애 티켓 관리, 운영 가이드 검색 등의 작업을 수행합니다.
    
    Args:
        query: DevOps 관련 질문 또는 요청
    
    Returns:
        DevOps Agent의 응답
    """
    global _current_sub_agents
    _current_sub_agents.append("devops")
    agent = _get_devops_agent()
    response = agent(query)
    return str(response)


@tool
def ask_analytics_agent(query: str) -> str:
    """데이터 분석 전문가 에이전트에게 질문합니다.
    
    게임 데이터 분석, DAU/MAU, 가챠 확률, 재화 흐름, 퀘스트 완료율,
    레벨 분포, 출석 현황 등의 분석을 수행합니다.
    
    Args:
        query: 데이터 분석 관련 질문 또는 요청
    
    Returns:
        Analytics Agent의 응답
    """
    global _current_sub_agents
    _current_sub_agents.append("analytics")
    agent = _get_analytics_agent()
    response = agent(query)
    return str(response)


@tool
def ask_godot_review_agent(query: str) -> str:
    """Godot/GDScript 전문가 에이전트에게 질문합니다.
    
    GDScript 코드 리뷰, 베스트 프랙티스 검증, 성능 최적화,
    시그널/노드 구조 분석, 리플레이 시스템 구현 등을 수행합니다.
    
    Args:
        query: Godot/GDScript 관련 질문 또는 요청
    
    Returns:
        Godot Review Agent의 응답
    """
    global _current_sub_agents
    _current_sub_agents.append("godot_review")
    agent = _get_godot_review_agent()
    response = agent(query)
    return str(response)


@tool
def ask_monitoring_agent(query: str) -> str:
    """CloudWatch 알람 모니터링 전문가 에이전트에게 질문합니다.
    
    CloudWatch 알람 현황 조회, 알람 히스토리 분석, 이슈 진단,
    알람 기반 장애 예측 및 대응 방안 제시 등을 수행합니다.
    
    Args:
        query: CloudWatch 알람 모니터링 관련 질문 또는 요청
    
    Returns:
        Monitoring Agent의 응답
    """
    global _current_sub_agents
    _current_sub_agents.append("monitoring")
    agent = _get_monitoring_agent()
    response = agent(query)
    return str(response)


SYSTEM_PROMPT = """당신은 게임 운영 총괄 AI 에이전트(Supervisor)입니다.

## 역할
사용자의 요청을 분석하여 적절한 전문가 에이전트에게 작업을 위임합니다.

## 전문가 에이전트

### DevOps Agent (ask_devops_agent)
담당 영역:
- 인프라 모니터링 (CloudWatch 메트릭)
- EC2 인스턴스 상태 확인
- CloudFormation 배포 이력
- 장애 티켓 생성/조회
- 운영 매뉴얼 검색

### Analytics Agent (ask_analytics_agent)
담당 영역:
- 게임 지표 분석 (DAU, MAU, 리텐션)
- 가챠/뽑기 확률 분석
- 재화 흐름 분석 (획득/소비)
- 퀘스트/업적 완료율
- 레벨 분포, 출석 현황

### Godot Review Agent (ask_godot_review_agent)
담당 영역:
- GDScript 코드 품질 검토
- Godot 베스트 프랙티스 검증
- 성능 이슈 탐지 및 최적화
- 시그널/노드 구조 분석
- 리플레이/테스트 시스템 리뷰

### Monitoring Agent (ask_monitoring_agent)
담당 영역:
- CloudWatch 알람 현황 조회
- 알람 히스토리 분석
- 알람 기반 이슈 진단
- 장애 예측 및 대응 방안 제시

### 피드백 분석 (analyze_negative_feedback)
담당 영역:
- 부정 피드백(👎) 조회 및 분석
- 실패 패턴 파악
- KB 문서 및 System Prompt 개선 제안

### KB 관리 (add_kb_document, trigger_kb_sync)
담당 영역:
- KB에 새 문서 추가 (add_kb_document)
- KB 동기화 실행 (trigger_kb_sync)
- 피드백 분석 결과를 KB 문서로 저장

## 작업 위임 원칙

1. **단일 영역**: 한 에이전트로 해결 가능하면 해당 에이전트에게 위임
2. **복합 영역**: 여러 영역이 필요하면 순차적으로 각 에이전트에게 위임
3. **결과 종합**: 여러 에이전트 결과를 종합하여 인사이트 제공

## 예시

- "서버 상태 확인해줘" → DevOps Agent
- "오늘 DAU 알려줘" → Analytics Agent
- "GDScript 코드 리뷰해줘" → Godot Review Agent
- "알람 현황 확인해줘" → Monitoring Agent
- "서버 장애가 매출에 영향을 줬는지 분석해줘" → DevOps + Analytics 순차 호출
- "피드백 분석해서 개선점 알려줘" → analyze_negative_feedback
- "피드백 분석해서 KB에 저장해줘" → analyze_negative_feedback → add_kb_document → trigger_kb_sync

## 응답 원칙
- 한국어로 응답
- 조직/정책/에스컬레이션 관련 질문 → search_common_knowledge() 먼저 호출
- 어떤 에이전트에게 위임했는지 명시
- 결과를 종합하여 명확한 인사이트 제공
- 추가 분석이 필요하면 제안
"""


def create_supervisor_agent() -> Agent:
    """Create and return Supervisor Agent instance."""
    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=REGION_NAME,
    )
    
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            ask_devops_agent,
            ask_analytics_agent,
            ask_godot_review_agent,
            ask_monitoring_agent,
            analyze_negative_feedback,
            search_common_knowledge,
            add_kb_document,
            trigger_kb_sync,
        ],
    )
    
    return agent


class LoggingSupervisorAgent:
    """Supervisor Agent with execution logging."""
    
    def __init__(self):
        self.agent = create_supervisor_agent()
        self.session_id = generate_session_id()
    
    def __call__(self, user_input: str) -> str:
        global _current_sub_agents
        _current_sub_agents = []
        
        start_time = time.time()
        status = "success"
        error = None
        
        try:
            response = self.agent(user_input)
            response_text = str(response)
        except Exception as e:
            status = "error"
            error = str(e)
            response_text = f"오류 발생: {error}"
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        log_execution(
            session_id=self.session_id,
            agent_type="supervisor",
            user_input=user_input,
            agent_response=response_text,
            tools_used=["ask_devops_agent", "ask_analytics_agent", "ask_godot_review_agent", "ask_monitoring_agent"] if _current_sub_agents else [],
            sub_agents=list(set(_current_sub_agents)),
            execution_time_ms=execution_time_ms,
            status=status,
            error=error,
        )
        
        return response_text


if __name__ == "__main__":
    agent = create_supervisor_agent()
    
    print("Supervisor Agent 시작. 'quit'으로 종료.")
    print("DevOps + Analytics + Godot Review + Monitoring Agent를 조율합니다.")
    print("-" * 50)
    
    while True:
        user_input = input("\n사용자: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        if not user_input:
            continue
        
        response = agent(user_input)
        print(f"\nSupervisor: {response}")
