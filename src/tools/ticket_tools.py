"""Incident ticket tool for DevOps Agent."""
import boto3
import uuid
from datetime import datetime
from strands import tool
from src.config import REGION_NAME

dynamodb = boto3.resource("dynamodb", region_name=REGION_NAME)
table = dynamodb.Table("incident-tickets")


@tool
def create_incident_ticket(
    title: str,
    description: str,
    severity: str,
    game_name: str = "ToadstoneGame",
) -> str:
    """
    장애 티켓을 생성합니다.
    
    Args:
        title: 티켓 제목
        description: 상세 설명
        severity: 심각도 (low, medium, high, critical)
        game_name: 게임 이름
    
    Returns:
        생성된 티켓 정보
    """
    valid_severities = ["low", "medium", "high", "critical"]
    if severity.lower() not in valid_severities:
        return f"유효하지 않은 심각도입니다. 다음 중 선택: {', '.join(valid_severities)}"
    
    ticket_id = str(uuid.uuid4())[:8]
    created_at = datetime.utcnow().isoformat()
    
    item = {
        "ticket_id": ticket_id,
        "created_at": created_at,
        "title": title,
        "description": description,
        "severity": severity.lower(),
        "game_name": game_name,
        "status": "open",
    }
    
    table.put_item(Item=item)
    
    return (
        f"장애 티켓이 생성되었습니다:\n"
        f"- 티켓 ID: {ticket_id}\n"
        f"- 제목: {title}\n"
        f"- 심각도: {severity}\n"
        f"- 게임: {game_name}\n"
        f"- 상태: open\n"
        f"- 생성 시간: {created_at}"
    )


@tool
def get_incident_tickets(
    game_name: str = None,
    status: str = "open",
    limit: int = 10,
) -> str:
    """
    장애 티켓 목록을 조회합니다.
    
    Args:
        game_name: 게임 이름으로 필터링 (선택)
        status: 상태 필터 (open, closed, all)
        limit: 최대 조회 개수
    
    Returns:
        티켓 목록
    """
    if game_name:
        # Use GSI
        response = table.query(
            IndexName="game-index",
            KeyConditionExpression="game_name = :gn",
            ExpressionAttributeValues={":gn": game_name},
            ScanIndexForward=False,  # Descending order
            Limit=limit,
        )
    else:
        response = table.scan(Limit=limit)
    
    items = response.get("Items", [])
    
    # Filter by status if not 'all'
    if status != "all":
        items = [i for i in items if i.get("status") == status]
    
    if not items:
        filter_desc = f"게임 '{game_name}'" if game_name else "전체"
        return f"{filter_desc}에 해당하는 {status} 상태 티켓이 없습니다."
    
    results = []
    for item in items[:limit]:
        results.append(
            f"- [{item['ticket_id']}] {item['title']}\n"
            f"  심각도: {item['severity']}, 상태: {item['status']}\n"
            f"  게임: {item['game_name']}, 생성: {item['created_at']}"
        )
    
    header = f"장애 티켓 목록"
    if game_name:
        header += f" (게임: {game_name})"
    header += f" - {len(results)}개:\n"
    
    return header + "\n".join(results)
