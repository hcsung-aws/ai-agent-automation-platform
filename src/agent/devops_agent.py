"""DevOps Agent - Strands Agent with tools integration."""
from strands import Agent
from strands.models import BedrockModel

from src.tools.cloudwatch_tools import get_cloudwatch_metrics
from src.tools.ec2_tools import get_ec2_status
from src.tools.cloudformation_tools import get_stack_events, list_stacks
from src.tools.ticket_tools import create_incident_ticket, get_incident_tickets
from src.tools.kb_tools import search_devops_knowledge

SYSTEM_PROMPT = """당신은 DevOps 전문가 AI 에이전트입니다.
온라인 게임 인프라를 모니터링하고 운영을 지원합니다.

주요 역할:
1. CloudWatch 메트릭 조회 및 분석
2. EC2 인스턴스 상태 확인
3. CloudFormation 배포 이력 확인
4. 장애 티켓 생성 및 관리
5. 운영 매뉴얼 및 장애 대응 가이드 검색

기본 게임 태그는 'ToadstoneGame'입니다.
사용자가 다른 게임을 지정하면 해당 게임으로 조회합니다.

장애 대응 시:
- 먼저 search_devops_knowledge로 관련 가이드를 검색하세요
- 가이드에 따라 단계별 대응 방법을 안내하세요

응답 시 다음을 준수하세요:
- 한국어로 응답
- 기술적 내용은 명확하게 설명
- 문제 발견 시 원인과 해결 방안 제시
- 필요시 장애 티켓 생성 제안
"""


def create_devops_agent() -> Agent:
    """Create and return DevOps Agent instance."""
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
    )
    
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_cloudwatch_metrics,
            get_ec2_status,
            get_stack_events,
            list_stacks,
            create_incident_ticket,
            get_incident_tickets,
            search_devops_knowledge,
        ],
    )
    
    return agent


# For direct testing
if __name__ == "__main__":
    agent = create_devops_agent()
    
    print("DevOps Agent 시작. 'quit'으로 종료.")
    print("-" * 50)
    
    while True:
        user_input = input("\n사용자: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        if not user_input:
            continue
        
        response = agent(user_input)
        print(f"\nAgent: {response}")
