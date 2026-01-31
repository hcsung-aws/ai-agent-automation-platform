"""Knowledge Base tools for DevOps Agent."""
import boto3
from strands import tool

KNOWLEDGE_BASE_ID = "H50SNRJBFF"


@tool
def search_operations_guide(query: str) -> str:
    """운영 매뉴얼 및 장애 대응 가이드에서 정보를 검색합니다.
    
    Args:
        query: 검색할 내용 (예: "Kinesis 샤드 용량 초과", "Athena 쿼리 타임아웃")
    
    Returns:
        관련 운영 가이드 내용
    """
    client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
    
    response = client.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "vectorSearchConfiguration": {
                "numberOfResults": 3
            }
        }
    )
    
    results = []
    for i, result in enumerate(response.get("retrievalResults", []), 1):
        content = result.get("content", {}).get("text", "")
        score = result.get("score", 0)
        # 관련성 높은 결과만 포함
        if score > 0.3:
            # 내용이 너무 길면 앞부분만
            if len(content) > 2000:
                content = content[:2000] + "..."
            results.append(f"[결과 {i}] (관련도: {score:.2f})\n{content}")
    
    if not results:
        return "관련 운영 가이드를 찾지 못했습니다."
    
    return "\n\n---\n\n".join(results)
