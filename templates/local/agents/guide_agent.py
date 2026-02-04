"""Project Guide Agent - AIOps 스타터 킷 사용 가이드 챗봇.

이 Agent는 프로젝트 문서를 참조하여 사용자가 AIOps를 도입하는 과정에서
막히는 부분을 해결할 수 있도록 도와줍니다.

역할:
- 프로젝트 구조 및 사용법 안내
- Agent Builder 활용 방법 설명
- 로컬/AWS 배포 단계별 가이드
- 트러블슈팅 지원
"""
from strands import Agent, tool
from strands.models import BedrockModel


# 프로젝트 문서 검색 도구 (KB 연동 시 교체)
@tool
def search_project_docs(query: str) -> str:
    """프로젝트 문서에서 관련 내용을 검색합니다.
    
    Args:
        query: 검색할 내용 (예: "Agent Builder 사용법", "AWS 배포 방법")
    
    Returns:
        관련 문서 내용
    """
    # TODO: Bedrock KB 연동 시 실제 검색으로 교체
    # 연동 방법: docs/QUICKSTART-AWS.md "7단계: Knowledge Base 생성" 참고
    #
    # KB 연동 코드 예시:
    # import boto3
    # client = boto3.client('bedrock-agent-runtime')
    # response = client.retrieve(
    #     knowledgeBaseId='YOUR_KB_ID',
    #     retrievalQuery={'text': query}
    # )
    # return response['retrievalResults'][0]['content']['text']
    docs = {
        "시작": """
## 빠른 시작
1. 저장소 클론: git clone [repo-url]
2. 설치: ./templates/local/setup.sh
3. 실행: chainlit run app.py --port 8000
4. 브라우저에서 http://localhost:8000 접속
""",
        "agent builder": """
## Agent Builder 사용법
1. Kiro CLI 실행: kiro chat --agent agent-builder
2. 자연어로 요청: "CloudWatch 알람을 조회하는 Monitoring Agent 만들어줘"
3. Agent Builder가 코드 생성 및 등록
4. 테스트 후 피드백으로 개선
""",
        "로컬 배포": """
## 로컬 배포 가이드
1. Python 3.10+ 필요
2. ./templates/local/setup.sh 실행
3. .env 파일에 AWS 자격증명 설정
4. chainlit run app.py 실행
""",
        "aws 배포": """
## AWS 배포 가이드 (AgentCore)
1. AWS CLI 설정 확인
2. cd templates/aws && ./deploy.sh
3. AgentCore Runtime에 Agent 배포됨
4. Gateway로 도구 연결
5. Memory로 대화 컨텍스트 유지
""",
        "agent 만들기": """
## 새 Agent 만들기
1. Agent Builder 사용 (권장):
   kiro chat --agent agent-builder
   "HR Agent 만들어줘. 휴가 조회 기능으로"

2. 직접 작성:
   - templates/local/agents/example_agent.py 참고
   - @tool 데코레이터로 도구 정의
   - SYSTEM_PROMPT에 역할 명시
   - create_xxx_agent() 함수 작성
""",
        "supervisor": """
## Supervisor 구조
Supervisor는 여러 전문 Agent를 조율합니다:
- 사용자 요청 분석
- 적절한 Agent에게 위임
- 결과 종합하여 응답

예: "서버 장애가 매출에 영향을 줬는지 분석해줘"
→ DevOps Agent (장애 확인) + Analytics Agent (매출 분석)
""",
    }
    
    query_lower = query.lower()
    for key, content in docs.items():
        if key in query_lower:
            return content
    
    return """관련 문서를 찾지 못했습니다. 다음 주제로 질문해보세요:
- 시작 / 빠른 시작
- Agent Builder 사용법
- 로컬 배포 / AWS 배포
- Agent 만들기
- Supervisor 구조"""


@tool
def get_project_structure() -> str:
    """프로젝트 디렉토리 구조를 보여줍니다.
    
    Returns:
        프로젝트 구조 설명
    """
    return """
## 프로젝트 구조

```
aiops-starter-kit/
├── templates/
│   ├── local/                 # 로컬 배포용
│   │   ├── setup.sh          # 원클릭 설치
│   │   ├── app.py            # Chainlit UI
│   │   └── agents/           # Agent 템플릿
│   │       ├── supervisor.py
│   │       └── guide_agent.py (이 파일)
│   │
│   └── aws/                   # AWS 배포용
│       ├── deploy.sh         # 배포 스크립트
│       └── cdk/              # CDK 스택
│           └── stacks/
│               ├── infrastructure_stack.py
│               └── agentcore_stack.py
│
├── src/                       # PoC 구현 (참고용)
│   ├── agent/                # Agent 구현 예시
│   └── tools/                # 도구 구현 예시
│
├── docs/                      # 문서
│   ├── QUICKSTART-LOCAL.md
│   └── QUICKSTART-AWS.md
│
└── context_rule/              # Agent Builder 가이드
    └── agent-builder-guide.md
```
"""


@tool
def get_next_step(current_step: str) -> str:
    """현재 단계에서 다음에 해야 할 일을 안내합니다.
    
    Args:
        current_step: 현재 진행 중인 단계 (예: "설치 완료", "첫 Agent 생성")
    
    Returns:
        다음 단계 안내
    """
    steps = {
        "설치": "다음 단계: Agent Builder로 첫 번째 Agent를 만들어보세요.\n→ kiro chat --agent agent-builder",
        "첫 agent": "다음 단계: 피드백 루프를 설정하세요.\n→ 👍/👎 버튼으로 피드백 수집 → 분석 → 개선",
        "피드백": "다음 단계: 두 번째 Agent를 추가하고 Supervisor로 연결하세요.",
        "multi-agent": "다음 단계: AWS에 배포하여 프로덕션 환경을 구축하세요.\n→ cd templates/aws && ./deploy.sh",
        "aws 배포": "축하합니다! AIOps 기본 환경이 구축되었습니다.\n다음: 실제 업무에 맞는 Agent를 추가하고 지속적으로 개선하세요.",
    }
    
    for key, next_step in steps.items():
        if key in current_step.lower():
            return next_step
    
    return """현재 단계를 파악하지 못했습니다. 다음 중 어디에 해당하나요?
1. 설치 완료
2. 첫 Agent 생성 완료
3. 피드백 루프 설정 완료
4. Multi-Agent 구성 완료
5. AWS 배포 완료"""


SYSTEM_PROMPT = """당신은 AIOps 스타터 킷 사용을 도와주는 가이드 챗봇입니다.

## 역할
사용자가 이 프로젝트를 활용하여 AIOps를 도입하는 과정에서 막히는 부분을 해결합니다.

## 주요 안내 영역
1. **시작하기**: 설치, 초기 설정
2. **Agent Builder**: 자연어로 Agent 생성하는 방법
3. **로컬 배포**: 개발 환경 구축
4. **AWS 배포**: AgentCore 활용 프로덕션 배포
5. **Agent 개발**: 새 Agent 만들기, 도구 추가
6. **Multi-Agent**: Supervisor 구성, Agent 협업

## 응답 원칙
- 한국어로 친절하게 응답
- 단계별로 명확하게 안내
- 막힌 부분의 원인과 해결책 제시
- 다음 단계도 함께 안내
- 필요시 search_project_docs로 문서 검색

## 자주 묻는 질문
- "어떻게 시작해요?" → 빠른 시작 가이드
- "Agent 어떻게 만들어요?" → Agent Builder 사용법
- "AWS에 배포하려면?" → AWS 배포 가이드
- "에러가 나요" → 트러블슈팅 안내
"""


def create_guide_agent() -> Agent:
    """Project Guide Agent 인스턴스를 생성합니다."""
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
    )
    
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            search_project_docs,
            get_project_structure,
            get_next_step,
        ],
    )


if __name__ == "__main__":
    agent = create_guide_agent()
    print("🚀 AIOps 스타터 킷 가이드입니다. 무엇이든 물어보세요!")
    print("   (종료: quit)\n")
    
    while True:
        user_input = input("질문: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        if user_input:
            print(f"\n{agent(user_input)}\n")
