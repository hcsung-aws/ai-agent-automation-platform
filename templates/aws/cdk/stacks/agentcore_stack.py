"""AgentCore Stack - Runtime, Gateway, Memory 구성.

Amazon Bedrock AgentCore를 활용한 Agent 배포 스택입니다.
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_s3 as s3,
    CfnOutput,
    CustomResource,
    custom_resources as cr,
)
from constructs import Construct


class AgentCoreStack(Stack):
    """AgentCore 배포 스택.
    
    구성 요소:
    - AgentCore Runtime: Agent 컨테이너 호스팅
    - AgentCore Gateway: Lambda 도구를 MCP 호환으로 변환
    - AgentCore Memory: 대화 컨텍스트 유지
    """
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        ecr_repo_uri: str,
        agent_role_arn: str,
        kms_key_arn: str,
        stack_prefix: str = "AIOps",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # 리소스명 접두사 (소문자)
        prefix = stack_prefix.lower()
        
        # === AgentCore Memory (S3 기반) ===
        self.memory_bucket = s3.Bucket(
            self, "AgentMemory",
            bucket_name=f"{prefix}-agent-memory-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.KMS,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
        )
        
        # === AgentCore Gateway - 도구 Lambda ===
        # 예시: Echo 도구 (템플릿)
        self.tool_lambda = lambda_.Function(
            self, "ToolLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import json

def handler(event, context):
    \"\"\"MCP 호환 도구 핸들러 템플릿.
    
    AgentCore Gateway가 이 Lambda를 MCP 도구로 변환합니다.
    \"\"\"
    tool_name = event.get('tool_name', 'unknown')
    parameters = event.get('parameters', {})
    
    # 도구별 처리
    if tool_name == 'echo':
        message = parameters.get('message', '')
        return {
            'statusCode': 200,
            'body': json.dumps({'result': f'Echo: {message}'})
        }
    
    return {
        'statusCode': 400,
        'body': json.dumps({'error': f'Unknown tool: {tool_name}'})
    }
"""),
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        
        # === AgentCore Runtime 설정 ===
        # AgentCore Runtime은 AWS 콘솔 또는 CLI로 생성
        # 여기서는 필요한 IAM 정책만 설정
        
        agent_role = iam.Role.from_role_arn(
            self, "AgentRole", agent_role_arn
        )
        
        # Memory 버킷 접근 권한
        self.memory_bucket.grant_read_write(agent_role)
        
        # Tool Lambda 호출 권한
        self.tool_lambda.grant_invoke(agent_role)
        
        # === AgentCore 배포 가이드 출력 ===
        CfnOutput(self, "MemoryBucketName",
            value=self.memory_bucket.bucket_name,
            description="Agent Memory S3 버킷",
        )
        
        CfnOutput(self, "ToolLambdaArn",
            value=self.tool_lambda.function_arn,
            description="도구 Lambda ARN (Gateway 연결용)",
        )
        
        CfnOutput(self, "DeploymentGuide",
            value=f"""
AgentCore Runtime 배포 가이드:

1. Agent 컨테이너 빌드 및 푸시:
   docker build -t aiops-agent .
   docker tag aiops-agent:latest {ecr_repo_uri}:latest
   docker push {ecr_repo_uri}:latest

2. AgentCore Runtime 생성 (CLI):
   aws bedrock create-agent \\
     --agent-name aiops-supervisor \\
     --agent-resource-role-arn {agent_role_arn} \\
     --foundation-model anthropic.claude-3-5-sonnet-20241022-v2:0

3. Gateway에 도구 연결:
   aws bedrock create-agent-action-group \\
     --agent-id <agent-id> \\
     --action-group-name tools \\
     --action-group-executor lambdaArn={self.tool_lambda.function_arn}

4. Memory 활성화:
   aws bedrock update-agent \\
     --agent-id <agent-id> \\
     --memory-configuration enabled=true,storageDays=30
""",
            description="AgentCore 배포 가이드",
        )
