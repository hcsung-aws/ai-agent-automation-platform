"""피드백 저장소 — 환경변수로 로컬 JSON / DynamoDB 자동 전환.

FEEDBACK_STORAGE 환경변수:
- "local" (기본): JSON 파일 저장
- "dynamodb": DynamoDB 테이블 저장 (FEEDBACK_TABLE 필수)
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

_STORAGE = os.environ.get("FEEDBACK_STORAGE", "local")
_TABLE_NAME = os.environ.get("FEEDBACK_TABLE", "")

# --- DynamoDB ---
_table = None


def _get_table():
    global _table
    if _table is None:
        import boto3
        region = os.environ.get("BEDROCK_REGION", "us-east-1")
        _table = boto3.resource("dynamodb", region_name=region).Table(_TABLE_NAME)
    return _table


# --- Local JSON ---
FEEDBACK_FILE = Path(__file__).parent / "feedback.json"


def _load_json():
    if FEEDBACK_FILE.exists():
        return json.loads(FEEDBACK_FILE.read_text())
    return []


# --- Public API ---

def save_feedback(*, message_id, rating, user_input, agent_response, comment=None):
    """피드백 저장. rating: 'positive' | 'negative'."""
    entry = {
        "message_id": message_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rating": rating,
        "user_input": user_input[:1000],
        "agent_response": agent_response[:2000],
    }
    if comment:
        entry["comment"] = comment[:500]

    if _STORAGE == "dynamodb":
        _get_table().put_item(Item=entry)
    else:
        data = _load_json()
        data.append(entry)
        FEEDBACK_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return entry


def get_feedback(limit=50, rating_filter=None):
    """피드백 조회. rating_filter: 'positive' | 'negative' | None."""
    if _STORAGE == "dynamodb":
        kwargs = {}
        if rating_filter:
            from boto3.dynamodb.conditions import Attr
            kwargs["FilterExpression"] = Attr("rating").eq(rating_filter)
        resp = _get_table().scan(**kwargs)
        data = resp.get("Items", [])
    else:
        data = _load_json()
        if rating_filter:
            data = [d for d in data if d.get("rating") == rating_filter]

    return sorted(data, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
