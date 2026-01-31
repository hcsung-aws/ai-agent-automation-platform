"""CloudWatch metrics tool for DevOps Agent."""
import boto3
from datetime import datetime, timedelta
from strands import tool

cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")
ec2 = boto3.client("ec2", region_name="us-east-1")


@tool
def get_cloudwatch_metrics(
    game_name: str = "ToadstoneGame",
    metric_name: str = "CPUUtilization",
    period_minutes: int = 60,
) -> str:
    """
    게임 인프라의 CloudWatch 메트릭을 조회합니다.
    
    Args:
        game_name: 게임 이름 (태그 기반 필터링)
        metric_name: 메트릭 이름 (CPUUtilization, NetworkIn, NetworkOut, DiskReadOps 등)
        period_minutes: 조회 기간 (분)
    
    Returns:
        메트릭 통계 정보
    """
    # Get EC2 instances with game tag
    instances = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Game", "Values": [game_name]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )
    
    instance_ids = []
    for reservation in instances.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            instance_ids.append(instance["InstanceId"])
    
    if not instance_ids:
        return f"게임 '{game_name}'에 해당하는 실행 중인 EC2 인스턴스가 없습니다."
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=period_minutes)
    
    results = []
    for instance_id in instance_ids:
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName=metric_name,
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5분 간격
            Statistics=["Average", "Maximum", "Minimum"],
        )
        
        datapoints = response.get("Datapoints", [])
        if datapoints:
            # Sort by timestamp
            datapoints.sort(key=lambda x: x["Timestamp"])
            latest = datapoints[-1]
            results.append(
                f"- {instance_id}: 평균={latest.get('Average', 0):.2f}, "
                f"최대={latest.get('Maximum', 0):.2f}, 최소={latest.get('Minimum', 0):.2f}"
            )
        else:
            results.append(f"- {instance_id}: 데이터 없음")
    
    return f"게임 '{game_name}' {metric_name} 메트릭 (최근 {period_minutes}분):\n" + "\n".join(results)
