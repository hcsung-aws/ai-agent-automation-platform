"""Knowledge Base tools with metadata filtering."""
import boto3
from strands import tool

KNOWLEDGE_BASE_ID = "H50SNRJBFF"
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
    return _client


def _search_kb(query: str, category: str = None) -> str:
    """내부 검색 함수 - 메타데이터 필터 적용."""
    client = _get_client()
    
    retrieval_config = {
        "vectorSearchConfiguration": {
            "numberOfResults": 5
        }
    }
    
    # 카테고리 필터 적용
    if category:
        if category == "common":
            retrieval_config["vectorSearchConfiguration"]["filter"] = {
                "equals": {"key": "category", "value": "common"}
            }
        else:
            # 공통 + 도메인 문서 모두 검색
            retrieval_config["vectorSearchConfiguration"]["filter"] = {
                "orAll": [
                    {"equals": {"key": "category", "value": "common"}},
                    {"equals": {"key": "category", "value": category}}
                ]
            }
    
    response = client.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration=retrieval_config
    )
    
    results = []
    for i, result in enumerate(response.get("retrievalResults", []), 1):
        content = result.get("content", {}).get("text", "")
        score = result.get("score", 0)
        metadata = result.get("metadata", {})
        cat = metadata.get("category", "unknown")
        
        if score > 0.3:
            if len(content) > 2000:
                content = content[:2000] + "..."
            results.append(f"[결과 {i}] (관련도: {score:.2f}, 카테고리: {cat})\n{content}")
    
    if not results:
        return "관련 문서를 찾지 못했습니다."
    
    return "\n\n---\n\n".join(results)


@tool
def search_common_knowledge(query: str) -> str:
    """공통 지식 베이스에서 검색합니다.
    
    조직 정보, 프로젝트 개요, 용어집, 에스컬레이션 정책 등
    모든 Agent가 알아야 할 공통 지식을 검색합니다.
    
    Args:
        query: 검색할 내용
    
    Returns:
        관련 공통 지식 내용
    """
    return _search_kb(query, category="common")


@tool
def search_devops_knowledge(query: str) -> str:
    """DevOps 지식 베이스에서 검색합니다.
    
    운영 매뉴얼, 장애 대응 가이드, 인프라 문서 등을 검색합니다.
    공통 지식도 함께 검색됩니다.
    
    Args:
        query: 검색할 내용 (예: "Kinesis 샤드 용량 초과", "장애 대응 절차")
    
    Returns:
        관련 DevOps 가이드 내용
    """
    return _search_kb(query, category="devops")


@tool
def search_analytics_knowledge(query: str) -> str:
    """Analytics 지식 베이스에서 검색합니다.
    
    데이터 분석 가이드, Athena 쿼리 패턴, 지표 정의 등을 검색합니다.
    공통 지식도 함께 검색됩니다.
    
    Args:
        query: 검색할 내용
    
    Returns:
        관련 Analytics 가이드 내용
    """
    return _search_kb(query, category="analytics")


@tool
def search_monitoring_knowledge(query: str) -> str:
    """Monitoring 지식 베이스에서 검색합니다.
    
    알람 설정 가이드, 모니터링 정책, 임계값 기준 등을 검색합니다.
    공통 지식도 함께 검색됩니다.
    
    Args:
        query: 검색할 내용
    
    Returns:
        관련 Monitoring 가이드 내용
    """
    return _search_kb(query, category="monitoring")


# 기존 호환성 유지
@tool
def search_operations_guide(query: str) -> str:
    """운영 매뉴얼 및 장애 대응 가이드에서 정보를 검색합니다.
    
    (기존 호환성 유지 - search_devops_knowledge와 동일)
    
    Args:
        query: 검색할 내용
    
    Returns:
        관련 운영 가이드 내용
    """
    return _search_kb(query, category="devops")
