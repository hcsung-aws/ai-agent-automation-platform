"""Project Guide Agent - AIOps 스타터 킷 사용 가이드 챗봇.

이 Agent는 프로젝트 문서를 참조하여 사용자가 AIOps를 도입하는 과정에서
막히는 부분을 해결할 수 있도록 도와줍니다.

역할:
- 프로젝트 구조 및 사용법 안내
- Agent Builder 활용 방법 설명
- 로컬/AWS 배포 단계별 가이드
- 트러블슈팅 지원
"""
import os
import logging
from pathlib import Path
from strands import Agent, tool
from strands.models import BedrockModel
from config import MODEL_ID, REGION_NAME

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# KB 설정 (환경변수)
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")
KB_S3_BUCKET = os.environ.get("KB_S3_BUCKET", "")
KB_S3_PREFIX = os.environ.get("KB_S3_PREFIX", "knowledge-base")
LOCAL_KB_PATH = Path(os.environ.get("LOCAL_KB_PATH", "knowledge-base"))

_bedrock_client = None
_s3_client = None


def _get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        import boto3
        _bedrock_client = boto3.client("bedrock-agent-runtime", region_name=REGION_NAME)
    return _bedrock_client


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client("s3", region_name=REGION_NAME)
    return _s3_client


def _search_s3_kb(query: str) -> str:
    """S3 버킷에서 .md 파일 검색 (Bedrock KB 없이 영속적 저장소)."""
    if not KB_S3_BUCKET:
        return ""
    
    try:
        s3 = _get_s3_client()
        results = []
        # 단어 단위 매칭 (2자 이상 단어만)
        keywords = [w for w in query.lower().split() if len(w) >= 2]
        
        response = s3.list_objects_v2(Bucket=KB_S3_BUCKET, Prefix=KB_S3_PREFIX)
        for obj in response.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".md"):
                continue
            
            file_obj = s3.get_object(Bucket=KB_S3_BUCKET, Key=key)
            content = file_obj["Body"].read().decode("utf-8")
            content_lower = content.lower()
            
            # 키워드 중 하나라도 매칭되면 포함
            matched = sum(1 for kw in keywords if kw in content_lower)
            if matched > 0:
                snippet = content[:2000] + "..." if len(content) > 2000 else content
                filename = key.replace(KB_S3_PREFIX + "/", "")
                results.append((matched, f"[{filename}]\n{snippet}"))
        
        # 매칭 수 기준 정렬 (많이 매칭된 것 우선)
        results.sort(key=lambda x: x[0], reverse=True)
        return "\n\n---\n\n".join(r[1] for r in results) if results else ""
    except Exception as e:
        print(f"⚠️ S3 검색 실패: {e}")
        return ""


def _search_local_kb(query: str) -> str:
    """로컬 KB에서 키워드 검색."""
    if not LOCAL_KB_PATH.exists():
        return ""
    
    results = []
    keywords = [w for w in query.lower().split() if len(w) >= 2]
    
    for md_file in LOCAL_KB_PATH.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        content_lower = content.lower()
        matched = sum(1 for kw in keywords if kw in content_lower)
        if matched > 0:
            snippet = content[:2000] + "..." if len(content) > 2000 else content
            results.append((matched, f"[{md_file.relative_to(LOCAL_KB_PATH)}]\n{snippet}"))
    
    results.sort(key=lambda x: x[0], reverse=True)
    return "\n\n---\n\n".join(r[1] for r in results) if results else ""


@tool
def search_project_docs(query: str) -> str:
    """프로젝트 문서에서 관련 내용을 검색합니다.
    
    Args:
        query: 검색할 내용 (예: "Agent Builder 사용법", "AWS 배포 방법")
    
    Returns:
        관련 문서 내용
    
    검색 우선순위: Bedrock KB → S3 → 로컬
    """
    print(f"[KB] search_project_docs called: query='{query}'")
    print(f"[KB] KNOWLEDGE_BASE_ID='{KNOWLEDGE_BASE_ID}', KB_S3_BUCKET='{KB_S3_BUCKET}', LOCAL_KB_PATH='{LOCAL_KB_PATH}'")
    
    # 1. Bedrock KB (설정된 경우)
    if KNOWLEDGE_BASE_ID:
        try:
            client = _get_bedrock_client()
            response = client.retrieve(
                knowledgeBaseId=KNOWLEDGE_BASE_ID,
                retrievalQuery={"text": query},
                retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}}
            )
            results = []
            for r in response.get("retrievalResults", []):
                if r.get("score", 0) > 0.3:
                    results.append(r.get("content", {}).get("text", ""))
            if results:
                return "\n\n---\n\n".join(results)
        except Exception as e:
            print(f"⚠️ Bedrock KB 접근 실패: {e}")
    
    # 2. S3 폴백 (AWS 환경에서 영속적 저장소)
    s3_result = _search_s3_kb(query)
    if s3_result:
        print(f"[KB] S3 hit: {len(s3_result)} chars")
        return s3_result
    else:
        print("[KB] S3 miss")
    
    # 3. 로컬 KB 폴백
    local_result = _search_local_kb(query)
    if local_result:
        print(f"[KB] Local hit: {len(local_result)} chars")
        return local_result
    else:
        print("[KB] Local miss")
    
    print("[KB] No results found")
    return "관련 문서를 찾지 못했습니다. knowledge-base/ 폴더에 .md 파일을 추가하세요."


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
│
├── knowledge-base/            # 로컬 KB (문서 추가 가능)
│   ├── common/
│   ├── devops/
│   ├── analytics/
│   └── monitoring/
│
├── docs/                      # 문서
│   ├── QUICKSTART-LOCAL.md
│   └── QUICKSTART-AWS.md
│
└── context_rule/              # Agent Builder 가이드
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
        model_id=MODEL_ID,
        region_name=REGION_NAME,
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
