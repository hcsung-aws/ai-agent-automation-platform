"""스타터 킷 공통 설정."""
import os

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
REGION_NAME = os.environ.get("BEDROCK_REGION", "us-east-1")
