"""EC2 status tool for DevOps Agent."""
import boto3
from strands import tool

ec2 = boto3.client("ec2", region_name="us-east-1")


@tool
def get_ec2_status(
    game_name: str = None,
    instance_ids: list = None,
) -> str:
    """
    EC2 인스턴스 상태를 조회합니다.
    
    Args:
        game_name: 게임 이름으로 필터링 (선택)
        instance_ids: 특정 인스턴스 ID 목록 (선택)
    
    Returns:
        EC2 인스턴스 상태 정보
    """
    filters = []
    
    if game_name:
        filters.append({"Name": "tag:Game", "Values": [game_name]})
    
    if instance_ids:
        response = ec2.describe_instances(InstanceIds=instance_ids)
    elif filters:
        response = ec2.describe_instances(Filters=filters)
    else:
        # Default: get all running instances
        filters.append({"Name": "instance-state-name", "Values": ["running", "stopped", "pending"]})
        response = ec2.describe_instances(Filters=filters)
    
    results = []
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            instance_id = instance["InstanceId"]
            state = instance["State"]["Name"]
            instance_type = instance["InstanceType"]
            
            # Get Name tag
            name = "N/A"
            game = "N/A"
            for tag in instance.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]
                if tag["Key"] == "Game":
                    game = tag["Value"]
            
            # Get public/private IP
            public_ip = instance.get("PublicIpAddress", "N/A")
            private_ip = instance.get("PrivateIpAddress", "N/A")
            
            results.append(
                f"- {instance_id} ({name})\n"
                f"  상태: {state}, 타입: {instance_type}\n"
                f"  게임: {game}\n"
                f"  Public IP: {public_ip}, Private IP: {private_ip}"
            )
    
    if not results:
        filter_desc = f"게임 '{game_name}'" if game_name else "조건"
        return f"{filter_desc}에 해당하는 EC2 인스턴스가 없습니다."
    
    header = f"EC2 인스턴스 상태"
    if game_name:
        header += f" (게임: {game_name})"
    header += f" - 총 {len(results)}개:\n"
    
    return header + "\n".join(results)
