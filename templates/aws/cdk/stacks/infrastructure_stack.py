"""Infrastructure Stack - ECR, IAM, KMS, KB S3 등 기반 인프라.

AgentCore 배포를 위한 기반 인프라를 구성합니다.
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_kms as kms,
    aws_logs as logs,
    aws_s3 as s3,
    CfnOutput,
)
from constructs import Construct


class InfrastructureStack(Stack):
    """AgentCore 기반 인프라 스택."""
    
    def __init__(self, scope: Construct, construct_id: str, stack_prefix: str = "AIOps", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # 리소스명 접두사 (소문자)
        prefix = stack_prefix.lower()
        
        # === KMS 키 (암호화) ===
        self.kms_key = kms.Key(
            self, "AgentCoreKey",
            description=f"{stack_prefix} Agent 암호화 키",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
        
        # === ECR 리포지토리 (Agent 컨테이너) ===
        self.ecr_repo = ecr.Repository(
            self, "AgentRepository",
            repository_name=f"{prefix}-agents",
            encryption=ecr.RepositoryEncryption.KMS,
            encryption_key=self.kms_key,
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True,
            image_scan_on_push=True,  # 보안 스캔
        )
        
        # === Knowledge Base S3 버킷 ===
        # Bedrock KB 없이도 S3에서 직접 검색 가능
        # 나중에 Bedrock KB 데이터 소스로 연결 가능
        self.kb_bucket = s3.Bucket(
            self, "KnowledgeBaseBucket",
            bucket_name=f"{prefix}-kb-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        
        # === CloudWatch 로그 그룹 ===
        self.log_group = logs.LogGroup(
            self, "AgentLogs",
            log_group_name=f"/{prefix}/agents",
            retention=logs.RetentionDays.ONE_MONTH,
            encryption_key=self.kms_key,
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        # === IAM 역할 (AgentCore Runtime) ===
        self.agent_role = iam.Role(
            self, "AgentCoreRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="AgentCore Runtime 실행 역할",
        )
        
        # Bedrock 모델 호출 권한
        self.agent_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
            ],
            resources=["arn:aws:bedrock:*::foundation-model/*"],
        ))
        
        # CloudWatch 로그 권한
        self.agent_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "logs:CreateLogStream",
                "logs:PutLogEvents",
            ],
            resources=[self.log_group.log_group_arn + ":*"],
        ))
        
        # KMS 복호화 권한
        self.kms_key.grant_decrypt(self.agent_role)
        
        # KB S3 버킷 읽기 권한
        self.kb_bucket.grant_read(self.agent_role)
        
        # === IAM 역할 (Agent Builder - Kiro CLI) ===
        self.builder_role = iam.Role(
            self, "AgentBuilderRole",
            assumed_by=iam.AccountPrincipal(self.account),
            description="Agent Builder (Kiro CLI) 역할",
        )
        
        # ECR 푸시 권한
        self.ecr_repo.grant_pull_push(self.builder_role)
        
        # KB S3 버킷 읽기/쓰기 권한
        self.kb_bucket.grant_read_write(self.builder_role)
        
        # AgentCore 관리 권한
        self.builder_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:CreateAgent",
                "bedrock:UpdateAgent",
                "bedrock:DeleteAgent",
                "bedrock:GetAgent",
                "bedrock:ListAgents",
            ],
            resources=["*"],
        ))
        
        # === Outputs ===
        CfnOutput(self, "ECRRepositoryUri",
            value=self.ecr_repo.repository_uri,
            description="ECR 리포지토리 URI",
        )
        
        CfnOutput(self, "AgentRoleArn",
            value=self.agent_role.role_arn,
            description="AgentCore Runtime 역할 ARN",
        )
        
        CfnOutput(self, "KMSKeyArn",
            value=self.kms_key.key_arn,
            description="암호화 키 ARN",
        )
        
        CfnOutput(self, "KBBucketName",
            value=self.kb_bucket.bucket_name,
            description="Knowledge Base S3 버킷 (Bedrock KB 없이 직접 검색 가능)",
        )
