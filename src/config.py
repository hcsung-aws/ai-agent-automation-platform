"""PoC 공통 설정."""
import os

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")
REGION_NAME = os.environ.get("BEDROCK_REGION", "us-east-1")
