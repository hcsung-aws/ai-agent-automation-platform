"""Supervisor Agent 템플릿 - Multi-Agent 협업 조율.

이 템플릿은 여러 전문 Agent를 조율하는 Supervisor의 기본 구조입니다.
Agent Builder가 새 Agent를 추가하면 이 파일에 연결됩니다.
"""
from strands import Agent, tool
from strands.models import BedrockModel
from case_tools import save_case
from config import MODEL_ID, REGION_NAME

# Sub-agents (lazy initialization)
_guide_agent = None
_news_agent = None
_news_analysis_agent = None


def _get_guide_agent():
    """Guide Agent를 지연 초기화합니다."""
    global _guide_agent
    if _guide_agent is None:
        from guide_agent import create_guide_agent
        _guide_agent = create_guide_agent()
    return _guide_agent


def _get_news_agent():
    """News Agent를 지연 초기화합니다."""
    global _news_agent
    if _news_agent is None:
        from news_agent import create_news_agent
        _news_agent = create_news_agent()
    return _news_agent


def _get_news_analysis_agent():
    """News Analysis Agent를 지연 초기화합니다."""
    global _news_analysis_agent
    if _news_analysis_agent is None:
        from news_analysis_agent import create_news_analysis_agent
        _news_analysis_agent = create_news_analysis_agent()
    return _news_analysis_agent


# === Agent-as-Tool 패턴 ===
# 새 Agent 추가 시 이 패턴을 따라 도구로 등록

@tool
def ask_guide_agent(query: str) -> str:
    """프로젝트 가이드 Agent에게 질문합니다.
    
    프로젝트 사용법, Agent Builder 활용, 배포 방법 등을 안내합니다.
    
    Args:
        query: 프로젝트 관련 질문
    
    Returns:
        Guide Agent의 응답
    """
    agent = _get_guide_agent()
    return str(agent(query))


# === 새 Agent 추가 예시 ===
# @tool
# def ask_devops_agent(query: str) -> str:
#     """DevOps Agent에게 질문합니다."""
#     agent = _get_devops_agent()
#     return str(agent(query))


@tool
def ask_news_agent(query: str) -> str:
    """뉴스 크롤링 Agent에게 질문합니다.

    최신 뉴스 조회, 특정 키워드 뉴스 검색, 뉴스 요약 등을 처리합니다.

    Args:
        query: 뉴스 관련 질문

    Returns:
        News Agent의 응답
    """
    agent = _get_news_agent()
    return str(agent(query))


@tool
def ask_news_analysis_agent(query: str) -> str:
    """뉴스 분석 Agent에게 질문합니다.

    저장된 뉴스 데이터의 트렌드 분석, 키워드 분석, 소스 비교 등을 처리합니다.

    Args:
        query: 뉴스 분석 관련 질문

    Returns:
        News Analysis Agent의 응답
    """
    agent = _get_news_analysis_agent()
    return str(agent(query))


SYSTEM_PROMPT = """당신은 AI Agent 팀의 Supervisor입니다.

## 역할
사용자의 요청을 분석하여 적절한 전문 Agent에게 작업을 위임합니다.

## 현재 등록된 Agent

### Guide Agent (ask_guide_agent)
담당 영역:
- 프로젝트 사용법 안내
- Agent Builder 활용 방법
- 로컬/AWS 배포 가이드
- 트러블슈팅 지원

### News Agent (ask_news_agent)
담당 영역:
- 최신 뉴스 조회 (연합뉴스, Google News, TechCrunch, AWS News)
- 키워드 기반 뉴스 검색
- 뉴스 요약 및 트렌드 분석

### News Analysis Agent (ask_news_analysis_agent)
담당 영역:
- 저장된 뉴스 데이터 트렌드 분석
- 키워드 빈도 분석
- 소스별 보도 비중 비교
- 날짜 간 뉴스 흐름 비교

### 사례 저장 (save_case)
사용자가 '사례로 저장해줘', '이 대화 기록해줘' 등 요청 시:
- 현재 대화의 문제-해결 과정을 요약
- title, problem, resolution, tags를 추출하여 save_case 호출
- KB에 축적되어 향후 유사 문제 시 참조됨

## 새 Agent 추가 방법
1. Agent Builder로 새 Agent 생성
2. 이 파일에 ask_xxx_agent 도구 추가
3. SYSTEM_PROMPT에 Agent 설명 추가

## 작업 위임 원칙
1. 단일 영역: 한 Agent로 해결 가능하면 해당 Agent에게 위임
2. 복합 영역: 여러 Agent 순차 호출 후 결과 종합
3. 불명확: 사용자에게 명확화 요청

## 응답 원칙
- 한국어로 응답
- 어떤 Agent에게 위임했는지 명시
- 결과를 종합하여 명확한 인사이트 제공
"""


def create_supervisor() -> Agent:
    """Supervisor Agent 인스턴스를 생성합니다."""
    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=REGION_NAME,
    )
    
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            ask_guide_agent,
            ask_news_agent,
            ask_news_analysis_agent,
            save_case,
            # 새 Agent 도구 추가 위치
        ],
    )


if __name__ == "__main__":
    supervisor = create_supervisor()
    print("🎯 Supervisor Agent 시작. 무엇이든 물어보세요!")
    print("   (종료: quit)\n")
    
    while True:
        user_input = input("사용자: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        if user_input:
            print(f"\nSupervisor: {supervisor(user_input)}\n")
