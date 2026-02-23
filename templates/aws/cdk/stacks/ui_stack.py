"""UI Stack - Fargate + Internal ALB で Chainlit UI をホスティング.

AgentCore Runtime の API を呼び出す Chainlit UI コンテナを
ECS Fargate + Internal ALB で配置します。
"""
from pathlib import Path
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
    aws_s3 as s3,
)
from constructs import Construct


class UIStack(Stack):
    """Chainlit UI 배포 스택 (Fargate + Internal ALB)."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        agent_runtime_arn: str,
        kb_bucket: s3.IBucket,
        agent_names: str = "Guide",
        stack_prefix: str = "AIOps",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # UI 코드 경로
        ui_path = self.node.try_get_context("agent_path") or str(
            Path(__file__).parent.parent.parent.parent / "local"
        )

        # VPC
        vpc = ec2.Vpc(
            self, "Vpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24,
                ),
            ],
        )

        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        # Fargate Service + Internal ALB
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "Service",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=1,
            assign_public_ip=False,
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(
                    directory=ui_path,
                    file="Dockerfile.ui",
                ),
                container_port=8000,
                environment={
                    "AGENT_RUNTIME_ARN": agent_runtime_arn,
                    "FEEDBACK_STORAGE": "s3",
                    "FEEDBACK_BUCKET": kb_bucket.bucket_name,
                    "BEDROCK_REGION": self.region,
                    "AGENT_NAMES": agent_names,
                },
                log_driver=ecs.LogDrivers.aws_logs(
                    stream_prefix="chainlit-ui",
                    log_retention=logs.RetentionDays.THREE_DAYS,
                ),
            ),
            public_load_balancer=False,
        )

        # ECS Exec 활성화 (SSM 포트포워딩용)
        service.service.enable_execute_command = True
        service.task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ssmmessages:CreateControlChannel",
                    "ssmmessages:CreateDataChannel",
                    "ssmmessages:OpenControlChannel",
                    "ssmmessages:OpenDataChannel",
                ],
                resources=["*"],
            )
        )

        # AgentCore 호출 권한
        service.task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock-agentcore:InvokeAgentRuntime"],
                resources=[agent_runtime_arn],
            )
        )

        # S3 피드백 버킷 읽기/쓰기
        kb_bucket.grant_read_write(service.task_definition.task_role)

        # 헬스체크
        service.target_group.configure_health_check(
            path="/",
            healthy_http_codes="200",
            interval=Duration.seconds(60),
            timeout=Duration.seconds(30),
            healthy_threshold_count=2,
            unhealthy_threshold_count=5,
        )

        CfnOutput(self, "InternalURL",
            value=f"http://{service.load_balancer.load_balancer_dns_name}",
            description="Internal ALB URL (SSM 포트포워딩으로 접속)",
        )
        CfnOutput(self, "VpcId", value=vpc.vpc_id)
        CfnOutput(self, "ClusterArn", value=cluster.cluster_arn)
