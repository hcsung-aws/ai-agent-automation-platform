"""AgentCore Runtime Lambda 핸들러.

AgentCore Runtime은 Lambda 스타일 핸들러를 기대합니다.
"""
import json
from supervisor import create_supervisor

# Supervisor Agent 인스턴스 (콜드 스타트 최적화)
_supervisor = None


def get_supervisor():
    global _supervisor
    if _supervisor is None:
        _supervisor = create_supervisor()
    return _supervisor


def handler(event, context):
    """Lambda 핸들러 - AgentCore Runtime 엔트리포인트."""
    # 입력 파싱
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)
    
    # prompt 또는 query 필드 지원
    query = body.get("prompt") or body.get("query", "")
    
    # Agent 호출
    supervisor = get_supervisor()
    response = supervisor(query)
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "response": str(response)
        }, ensure_ascii=False)
    }
