#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stack import NewsAgentStack

app = cdk.App()
NewsAgentStack(
    app, "NewsAgentStack",
    env=cdk.Environment(region=os.environ.get("CDK_DEPLOY_REGION", "us-west-2")),
)
app.synth()
