from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_glue as glue,
)
from constructs import Construct


class DevOpsAgentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # IAM Role for Agent execution
        self.agent_role = iam.Role(
            self,
            "AgentExecutionRole",
            role_name="GameOpsAgentRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("bedrock.amazonaws.com"),
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("glue.amazonaws.com"),
            ),
            description="IAM Role for Game Ops Multi-Agent System",
        )

        # CloudWatch permissions
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchAccess",
                actions=[
                    "cloudwatch:GetMetricStatistics",
                    "cloudwatch:ListMetrics",
                    "cloudwatch:GetMetricData",
                ],
                resources=["*"],
            )
        )

        # EC2 permissions
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="EC2ReadAccess",
                actions=[
                    "ec2:DescribeInstances",
                    "ec2:DescribeInstanceStatus",
                    "ec2:DescribeTags",
                ],
                resources=["*"],
            )
        )

        # CloudFormation permissions
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudFormationAccess",
                actions=[
                    "cloudformation:DescribeStacks",
                    "cloudformation:DescribeStackEvents",
                    "cloudformation:ListStacks",
                ],
                resources=["*"],
            )
        )

        # Bedrock permissions
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockAccess",
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:Retrieve",
                    "bedrock:RetrieveAndGenerate",
                ],
                resources=["*"],
            )
        )

        # Athena permissions
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="AthenaAccess",
                actions=[
                    "athena:StartQueryExecution",
                    "athena:GetQueryExecution",
                    "athena:GetQueryResults",
                    "athena:StopQueryExecution",
                ],
                resources=["*"],
            )
        )

        # Glue permissions
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="GlueAccess",
                actions=[
                    "glue:GetDatabase",
                    "glue:GetDatabases",
                    "glue:GetTable",
                    "glue:GetTables",
                    "glue:GetPartitions",
                    "glue:CreateTable",
                    "glue:CreatePartition",
                    "glue:DeleteTable",
                ],
                resources=["*"],
            )
        )

        # S3 Bucket for data and results
        self.data_bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=f"game-ops-agent-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        self.data_bucket.grant_read_write(self.agent_role)

        # DynamoDB - Incident Tickets Table
        self.incident_table = dynamodb.Table(
            self,
            "IncidentTicketsTable",
            table_name="incident-tickets",
            partition_key=dynamodb.Attribute(
                name="ticket_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.incident_table.add_global_secondary_index(
            index_name="game-index",
            partition_key=dynamodb.Attribute(
                name="game_name", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at", type=dynamodb.AttributeType.STRING
            ),
        )
        self.incident_table.grant_read_write_data(self.agent_role)

        # DynamoDB - Execution Logs Table
        self.execution_logs_table = dynamodb.Table(
            self,
            "ExecutionLogsTable",
            table_name="execution-logs",
            partition_key=dynamodb.Attribute(
                name="session_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.execution_logs_table.grant_read_write_data(self.agent_role)

        # Glue Database for analytics
        self.glue_database = glue.CfnDatabase(
            self,
            "GameLogsDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="game_logs",
                description="MMORPG game analytics database",
            ),
        )

        # Outputs
        CfnOutput(self, "AgentRoleArn", value=self.agent_role.role_arn)
        CfnOutput(self, "DataBucketName", value=self.data_bucket.bucket_name)
        CfnOutput(self, "IncidentTableName", value=self.incident_table.table_name)
        CfnOutput(self, "ExecutionLogsTableName", value=self.execution_logs_table.table_name)
