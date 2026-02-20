#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.devops_agent_stack import DevOpsAgentStack

app = cdk.App()

DevOpsAgentStack(
    app,
    "DevOpsAgentStack",
    env=cdk.Environment(region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")),
)

app.synth()
