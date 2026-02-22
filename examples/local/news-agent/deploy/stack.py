"""News Agent 배포 스택 - ECS Fargate + ALB (완전 격리, cdk destroy로 제거)."""
import os
from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    Duration,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct

# 허용할 IP (ALLOWED_IP 환경변수로 변경 가능)
ALLOWED_IP = os.environ.get("ALLOWED_IP", "175.114.18.46/32")


class NewsAgentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC: Public + Private 서브넷, NAT Gateway 1개 (비용 절약)
        vpc = ec2.Vpc(
            self, "Vpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24
                ),
            ],
        )

        # VPC Flow Logs → CloudWatch Logs
        vpc.add_flow_log("FlowLog",
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(),
            traffic_type=ec2.FlowLogTrafficType.ALL,
        )

        # ECS Cluster
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        # Fargate Service + ALB
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "Service",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=1,
            assign_public_ip=False,  # Private subnet → Public IP 없음
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(
                    directory="..",
                    file="deploy/Dockerfile",
                    exclude=["cdk.out", "deploy/cdk.out", ".venv", "__pycache__", "*.pyc", "news-data"],
                ),
                container_port=8000,
                environment={
                    "BEDROCK_MODEL_ID": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                    "BEDROCK_REGION": "us-east-1",
                    "FEEDBACK_STORAGE": "local",
                },
                log_driver=ecs.LogDrivers.aws_logs(
                    stream_prefix="news-agent",
                    log_retention=logs.RetentionDays.THREE_DAYS,
                ),
            ),
            public_load_balancer=True,
            open_listener=False,
        )

        # ALB Security Group: 허용된 IP만 접근 가능
        service.load_balancer.connections.security_groups[0].add_ingress_rule(
            ec2.Peer.ipv4(ALLOWED_IP),
            ec2.Port.tcp(80),
            f"Allow only {ALLOWED_IP}",
        )

        # 헬스체크
        service.target_group.configure_health_check(
            path="/",
            healthy_http_codes="200",
            interval=Duration.seconds(60),
            timeout=Duration.seconds(30),
            healthy_threshold_count=2,
            unhealthy_threshold_count=5,
        )

        # Bedrock 호출 권한
        service.task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                resources=["*"],
            )
        )

        # 모든 리소스에 RemovalPolicy.DESTROY 적용
        for child in self.node.find_all():
            if hasattr(child, "apply_removal_policy"):
                try:
                    child.apply_removal_policy(RemovalPolicy.DESTROY)
                except Exception:
                    pass

        CfnOutput(self, "URL", value=f"http://{service.load_balancer.load_balancer_dns_name}")
