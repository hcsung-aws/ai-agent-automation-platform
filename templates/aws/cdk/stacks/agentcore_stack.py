"""AgentCore Stack - Runtime, Gateway, Memory 구성.

Amazon Bedrock AgentCore L2 Construct를 활용한 Agent 배포 스택입니다.
Strands Agent를 컨테이너로 패키징하여 AgentCore Runtime에 배포합니다.
"""
from pathlib import Path
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_s3 as s3,
)
from constructs import Construct
import aws_cdk.aws_bedrock_agentcore_alpha as agentcore


class AgentCoreStack(Stack):
    """AgentCore 배포 스택 (L2 Construct 사용).
    
    구성 요소:
    - AgentCore Runtime: Strands Agent 컨테이너 호스팅
    - AgentCore Memory: 대화 컨텍스트 유지
    """
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        ecr_repo_uri: str,
        agent_role_arn: str,
        kms_key_arn: str,
        kb_bucket: s3.IBucket,
        feedback_table: dynamodb.ITable,
        kb_id: str = "",
        stack_prefix: str = "AIOps",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # 리소스명 접두사 (소문자)
        prefix = stack_prefix.lower()
        
        # Agent 코드 경로 (CDK context 또는 기본값)
        agent_path = self.node.try_get_context("agent_path") or str(
            Path(__file__).parent.parent.parent.parent / "local"
        )
        
        # === AgentCore Runtime ===
        # 로컬 Dockerfile에서 자동 빌드/푸시
        self.runtime = agentcore.Runtime(
            self, "SupervisorRuntime",
            runtime_name=f"{prefix}_supervisor",
            agent_runtime_artifact=agentcore.AgentRuntimeArtifact.from_asset(
                agent_path,
                file="agents/Dockerfile",
            ),
            description="AIOps Supervisor Agent - Multi-Agent 협업 조율",
            environment_variables={
                "KNOWLEDGE_BASE_ID": kb_id,
                "KB_S3_BUCKET": kb_bucket.bucket_name,  # S3 폴백용
                "KB_S3_PREFIX": "knowledge-base",
                "LOCAL_KB_PATH": "/app/knowledge-base",
                "FEEDBACK_STORAGE": "dynamodb",
                "FEEDBACK_TABLE": feedback_table.table_name,
                "NEWS_S3_BUCKET": kb_bucket.bucket_name,  # KB 버킷 재사용
            },
        )
        
        # Bedrock 모델 호출 권한
        self.runtime.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
            ],
            resources=[
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
                "arn:aws:bedrock:*:*:inference-profile/*",
            ],
        ))
        
        # Bedrock KB 검색 권한
        self.runtime.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["bedrock:Retrieve"],
            resources=[f"arn:aws:bedrock:{self.region}:{self.account}:knowledge-base/*"],
        ))
        
        # S3 KB 버킷 읽기/쓰기 권한 (사례 저장 포함)
        kb_bucket.grant_read_write(self.runtime.role)
        
        # DynamoDB 피드백 테이블 읽기/쓰기 권한
        feedback_table.grant_read_write_data(self.runtime.role)
        
        # === AgentCore Memory ===
        self.memory = agentcore.Memory(
            self, "AgentMemory",
            memory_name=f"{prefix}_memory",
            description="Agent 대화 컨텍스트 저장",
        )
        
        # === Outputs ===
        CfnOutput(self, "RuntimeId",
            value=self.runtime.agent_runtime_id,
            description="AgentCore Runtime ID",
        )
        
        CfnOutput(self, "MemoryId",
            value=self.memory.memory_id,
            description="AgentCore Memory ID",
        )
        
        CfnOutput(self, "KBBucketForAgent",
            value=kb_bucket.bucket_name,
            description="Agent가 사용하는 KB S3 버킷",
        )
