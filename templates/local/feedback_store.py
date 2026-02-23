"""피드백 저장소 — 환경변수로 로컬 JSON / DynamoDB / S3 자동 전환.

FEEDBACK_STORAGE 환경변수:
- "local" (기본): JSON 파일 저장
- "dynamodb": DynamoDB 테이블 저장 (FEEDBACK_TABLE 필수)
- "s3": S3 버킷 저장 (FEEDBACK_BUCKET 필수)
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

_STORAGE = os.environ.get("FEEDBACK_STORAGE", "local")
_TABLE_NAME = os.environ.get("FEEDBACK_TABLE", "")
_BUCKET_NAME = os.environ.get("FEEDBACK_BUCKET", "")
_S3_PREFIX = "feedback/"

# --- DynamoDB ---
_table = None


def _get_table():
    global _table
    if _table is None:
        import boto3
        region = os.environ.get("BEDROCK_REGION", "us-east-1")
        _table = boto3.resource("dynamodb", region_name=region).Table(_TABLE_NAME)
    return _table


# --- S3 ---
_s3 = None


def _get_s3():
    global _s3
    if _s3 is None:
        import boto3
        _s3 = boto3.client("s3", region_name=os.environ.get("BEDROCK_REGION", "us-east-1"))
    return _s3


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
    elif _STORAGE == "s3":
        key = f"{_S3_PREFIX}{entry['timestamp']}_{message_id}.json"
        _get_s3().put_object(
            Bucket=_BUCKET_NAME,
            Key=key,
            Body=json.dumps(entry, ensure_ascii=False),
            ContentType="application/json",
        )
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
    elif _STORAGE == "s3":
        s3 = _get_s3()
        resp = s3.list_objects_v2(Bucket=_BUCKET_NAME, Prefix=_S3_PREFIX, MaxKeys=limit * 2)
        data = []
        for obj in resp.get("Contents", []):
            body = s3.get_object(Bucket=_BUCKET_NAME, Key=obj["Key"])["Body"].read()
            data.append(json.loads(body))
        if rating_filter:
            data = [d for d in data if d.get("rating") == rating_filter]
    else:
        data = _load_json()
        if rating_filter:
            data = [d for d in data if d.get("rating") == rating_filter]

    return sorted(data, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
