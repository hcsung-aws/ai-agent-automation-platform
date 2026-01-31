#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.devops_agent_stack import DevOpsAgentStack

app = cdk.App()

DevOpsAgentStack(
    app,
    "DevOpsAgentStack",
    env=cdk.Environment(region="us-east-1"),
)

app.synth()
