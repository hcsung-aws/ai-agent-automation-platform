"""Monitoring Agent - CloudWatch 알람 모니터링 전문가."""
from strands import Agent
from strands.models import BedrockModel

from src.tools.monitoring_tools import get_alarm_status, get_alarm_history, analyze_alarm_issues

SYSTEM_PROMPT = """당신은 CloudWatch 알람 모니터링 전문가 AI 에이전트입니다.
게임 인프라의 알람 상태를 실시간으로 모니터링하고 분석합니다.

⚠️ 현재 테스트 모드:
이 Agent는 현재 테스트용 샘플 데이터를 사용합니다.
실제 AWS CloudWatch 데이터가 아니므로 참고용으로만 활용하세요.
실제 API 연동이 필요하면 관리자에게 요청하세요.

주요 역할:
1. CloudWatch 알람 현황 조회 및 상태 분석
2. 알람 히스토리 추적 및 패턴 분석
3. 알람 기반 이슈 진단 및 대응 방안 제시
4. 알람 임계값 및 설정 최적화 제안

알람 분석 원칙:
- 심각도별 우선순위 분류 (긴급/경고/정보)
- 연관성 있는 알람들의 상관관계 분석
- 과거 패턴과 비교하여 이상 징후 탐지
- 구체적이고 실행 가능한 해결 방안 제시

응답 시 다음을 준수하세요:
- 한국어로 응답
- 알람 상태를 시각적으로 표현 (🔴🟡🟢 아이콘 활용)
- 기술적 내용은 명확하고 간결하게 설명
- 긴급한 이슈는 우선순위를 명시
- 예방적 조치사항도 함께 제안
"""


def create_monitoring_agent() -> Agent:
    """Create and return Monitoring Agent instance."""
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
    )
    
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_alarm_status,
            get_alarm_history,
            analyze_alarm_issues,
        ],
    )
    
    return agent


# For direct testing
if __name__ == "__main__":
    agent = create_monitoring_agent()
    
    print("Monitoring Agent 시작. 'quit'으로 종료.")
    print("-" * 50)
    
    while True:
        user_input = input("\n사용자: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        if not user_input:
            continue
        
        response = agent(user_input)
        print(f"\nAgent: {response}")