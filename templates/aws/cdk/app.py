#!/usr/bin/env python3
"""AIOps 스타터 킷 - AWS CDK 앱."""
import os
import aws_cdk as cdk
from stacks.infrastructure_stack import InfrastructureStack
from stacks.agentcore_stack import AgentCoreStack


app = cdk.App()

# 환경 설정
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

# 1. 기반 인프라 스택
infra_stack = InfrastructureStack(
    app, "AIOpsInfrastructure",
    env=env,
    description="AIOps 스타터 킷 - 기반 인프라 (ECR, IAM, KMS)",
)

# 2. AgentCore 스택
agentcore_stack = AgentCoreStack(
    app, "AIOpsAgentCore",
    env=env,
    ecr_repo_uri=infra_stack.ecr_repo.repository_uri,
    agent_role_arn=infra_stack.agent_role.role_arn,
    kms_key_arn=infra_stack.kms_key.key_arn,
    description="AIOps 스타터 킷 - AgentCore (Runtime, Gateway, Memory)",
)

# 의존성 설정
agentcore_stack.add_dependency(infra_stack)

app.synth()
