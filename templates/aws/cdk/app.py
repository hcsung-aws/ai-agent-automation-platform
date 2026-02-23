#!/usr/bin/env python3
"""AIOps 스타터 킷 - AWS CDK 앱.

Hybrid Architecture: Infrastructure + AgentCore + UI (Fargate)
"""
import os
import aws_cdk as cdk
from stacks.infrastructure_stack import InfrastructureStack
from stacks.agentcore_stack import AgentCoreStack
from stacks.ui_stack import UIStack


app = cdk.App()

# 환경 설정
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

# 스택 접두사
stack_prefix = os.environ.get("STACK_PREFIX", "AIOps")

# 1. 기반 인프라 스택
infra_stack = InfrastructureStack(
    app, f"{stack_prefix}Infrastructure",
    env=env,
    stack_prefix=stack_prefix,
    description=f"{stack_prefix} - Infrastructure (ECR, IAM, KMS, KB, S3 Vectors, DynamoDB)",
)

# 2. AgentCore 스택
agentcore_stack = AgentCoreStack(
    app, f"{stack_prefix}AgentCore",
    env=env,
    ecr_repo_uri=infra_stack.ecr_repo.repository_uri,
    agent_role_arn=infra_stack.agent_role.role_arn,
    kms_key_arn=infra_stack.kms_key.key_arn,
    kb_bucket=infra_stack.kb_bucket,
    feedback_table=infra_stack.feedback_table,
    kb_id=infra_stack.kb_id,
    stack_prefix=stack_prefix,
    description=f"{stack_prefix} - AgentCore (Runtime, Memory)",
)
agentcore_stack.add_dependency(infra_stack)

# 3. UI 스택 (Fargate + Chainlit)
ui_stack = UIStack(
    app, f"{stack_prefix}UI",
    env=env,
    agent_runtime_arn=agentcore_stack.runtime.agent_runtime_arn,
    kb_bucket=infra_stack.kb_bucket,
    stack_prefix=stack_prefix,
    description=f"{stack_prefix} - UI (Fargate + Chainlit)",
)
ui_stack.add_dependency(agentcore_stack)

app.synth()
