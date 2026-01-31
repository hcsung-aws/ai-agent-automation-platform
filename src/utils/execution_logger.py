"""Execution logging for agent interactions."""
import boto3
import uuid
from datetime import datetime
from typing import Optional

REGION = "us-east-1"
TABLE_NAME = "execution-logs"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)


def generate_session_id() -> str:
    """Generate unique session ID."""
    return str(uuid.uuid4())[:8]


def log_execution(
    session_id: str,
    agent_type: str,
    user_input: str,
    agent_response: str,
    tools_used: list[str] = None,
    sub_agents: list[str] = None,
    execution_time_ms: int = 0,
    status: str = "success",
    error: Optional[str] = None,
) -> dict:
    """Log agent execution to DynamoDB.
    
    Args:
        session_id: Session identifier
        agent_type: Type of agent (supervisor, devops, analytics)
        user_input: User's input message
        agent_response: Agent's response
        tools_used: List of tools invoked
        sub_agents: List of sub-agents called (for supervisor)
        execution_time_ms: Execution time in milliseconds
        status: Execution status (success, error)
        error: Error message if failed
    
    Returns:
        Logged item
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    item = {
        "session_id": session_id,
        "timestamp": timestamp,
        "agent_type": agent_type,
        "user_input": user_input,
        "agent_response": agent_response[:5000],  # Truncate long responses
        "tools_used": tools_used or [],
        "sub_agents": sub_agents or [],
        "execution_time_ms": execution_time_ms,
        "status": status,
    }
    
    if error:
        item["error"] = error
    
    table.put_item(Item=item)
    return item


def get_session_logs(session_id: str, limit: int = 50) -> list[dict]:
    """Get execution logs for a session.
    
    Args:
        session_id: Session identifier
        limit: Maximum number of logs to return
    
    Returns:
        List of execution logs
    """
    response = table.query(
        KeyConditionExpression="session_id = :sid",
        ExpressionAttributeValues={":sid": session_id},
        Limit=limit,
        ScanIndexForward=False,  # Most recent first
    )
    return response.get("Items", [])


def get_recent_logs(limit: int = 20) -> list[dict]:
    """Get recent execution logs across all sessions.
    
    Args:
        limit: Maximum number of logs to return
    
    Returns:
        List of recent execution logs
    """
    response = table.scan(Limit=limit)
    items = response.get("Items", [])
    return sorted(items, key=lambda x: x.get("timestamp", ""), reverse=True)
