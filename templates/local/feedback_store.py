"""피드백 저장소 — 로컬 JSON 파일 기반.

로컬 환경에서는 JSON 파일에 저장하고,
AWS 배포 시 DynamoDB로 교체합니다.

## DynamoDB 마이그레이션 가이드
1. boto3 DynamoDB Table 리소스 생성:
   ```python
   import boto3
   table = boto3.resource("dynamodb", region_name=REGION).Table("feedback")
   ```
2. save_feedback() 내부를 table.put_item(Item=entry)로 교체
3. get_feedback() 내부를 table.scan()으로 교체
4. _load() / FEEDBACK_FILE 관련 코드 제거
5. CDK 스택에 DynamoDB 테이블 추가:
   ```python
   dynamodb.Table(self, "FeedbackTable",
       partition_key=dynamodb.Attribute(name="message_id", type=dynamodb.AttributeType.STRING),
       sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
   )
   ```
"""
import json
from datetime import datetime, timezone
from pathlib import Path

FEEDBACK_FILE = Path(__file__).parent / "feedback.json"


def save_feedback(*, message_id, rating, user_input, agent_response, comment=None):
    """피드백 저장. rating: 'positive' | 'negative'."""
    data = _load()
    entry = {
        "message_id": message_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rating": rating,
        "user_input": user_input[:1000],
        "agent_response": agent_response[:2000],
    }
    if comment:
        entry["comment"] = comment[:500]
    data.append(entry)
    FEEDBACK_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return entry


def get_feedback(limit=50, rating_filter=None):
    """피드백 조회. rating_filter: 'positive' | 'negative' | None."""
    data = _load()
    if rating_filter:
        data = [d for d in data if d.get("rating") == rating_filter]
    return sorted(data, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]


def _load():
    if FEEDBACK_FILE.exists():
        return json.loads(FEEDBACK_FILE.read_text())
    return []
