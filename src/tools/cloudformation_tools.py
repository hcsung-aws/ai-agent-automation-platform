"""CloudFormation stack events tool for DevOps Agent."""
import boto3
from strands import tool

cfn = boto3.client("cloudformation", region_name="us-east-1")


@tool
def get_stack_events(
    stack_name: str,
    limit: int = 10,
) -> str:
    """
    CloudFormation 스택 이벤트를 조회합니다 (배포 이력).
    
    Args:
        stack_name: CloudFormation 스택 이름
        limit: 최근 N개 이벤트
    
    Returns:
        스택 이벤트 목록
    """
    try:
        response = cfn.describe_stack_events(StackName=stack_name)
    except cfn.exceptions.ClientError as e:
        if "does not exist" in str(e):
            return f"스택 '{stack_name}'이 존재하지 않습니다."
        raise
    
    events = response.get("StackEvents", [])[:limit]
    
    if not events:
        return f"스택 '{stack_name}'에 이벤트가 없습니다."
    
    results = []
    for event in events:
        timestamp = event["Timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        resource_type = event.get("ResourceType", "N/A")
        logical_id = event.get("LogicalResourceId", "N/A")
        status = event.get("ResourceStatus", "N/A")
        reason = event.get("ResourceStatusReason", "")
        
        result = f"- [{timestamp}] {logical_id} ({resource_type}): {status}"
        if reason:
            result += f"\n  사유: {reason}"
        results.append(result)
    
    return f"스택 '{stack_name}' 최근 {len(events)}개 이벤트:\n" + "\n".join(results)


@tool
def list_stacks(
    status_filter: str = "active",
) -> str:
    """
    CloudFormation 스택 목록을 조회합니다.
    
    Args:
        status_filter: 상태 필터 (active, deleted, all)
    
    Returns:
        스택 목록
    """
    status_map = {
        "active": [
            "CREATE_COMPLETE",
            "UPDATE_COMPLETE",
            "UPDATE_ROLLBACK_COMPLETE",
        ],
        "deleted": ["DELETE_COMPLETE"],
        "all": None,
    }
    
    filters = status_map.get(status_filter, status_map["active"])
    
    if filters:
        response = cfn.list_stacks(StackStatusFilter=filters)
    else:
        response = cfn.list_stacks()
    
    stacks = response.get("StackSummaries", [])
    
    if not stacks:
        return f"'{status_filter}' 상태의 스택이 없습니다."
    
    results = []
    for stack in stacks[:20]:  # Limit to 20
        name = stack["StackName"]
        status = stack["StackStatus"]
        created = stack.get("CreationTime", "N/A")
        if hasattr(created, "strftime"):
            created = created.strftime("%Y-%m-%d %H:%M")
        
        results.append(f"- {name}: {status} (생성: {created})")
    
    return f"CloudFormation 스택 목록 ({status_filter}):\n" + "\n".join(results)
