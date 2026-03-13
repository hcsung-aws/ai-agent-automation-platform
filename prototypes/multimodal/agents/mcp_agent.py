"""MCP 연동 Agent 예시 - AWS Documentation MCP Server + 커스텀 도구 혼합.

이 Agent는 MCP(Model Context Protocol)를 통해 외부 MCP 서버의 도구를 사용하면서,
기존 @tool 패턴의 커스텀 도구도 함께 사용하는 혼합 패턴을 보여줍니다.

사용 예시:
- "AWS Lambda 콜드 스타트 줄이는 방법은?"  → MCP 도구 (AWS Docs 검색)
- "검색 결과를 요약해줘"                    → 커스텀 도구 (요약 저장)
"""
import os
import logging
from datetime import datetime
from pathlib import Path

from mcp import stdio_client, StdioServerParameters
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

from config import MODEL_ID, REGION_NAME

logger = logging.getLogger(__name__)

# MCP 서버 설정 (환경변수로 오버라이드 가능)
MCP_SERVER_COMMAND = os.environ.get("MCP_SERVER_COMMAND", "uvx")
MCP_SERVER_ARGS = os.environ.get(
    "MCP_SERVER_ARGS", "awslabs.aws-documentation-mcp-server@latest"
).split(",")

# 요약 저장 경로
SUMMARY_DIR = Path(os.environ.get("MCP_SUMMARY_DIR", "knowledge-base/mcp-summaries"))


def _create_mcp_client() -> MCPClient:
    """AWS Documentation MCP 클라이언트를 생성합니다."""
    return MCPClient(lambda: stdio_client(
        StdioServerParameters(command=MCP_SERVER_COMMAND, args=MCP_SERVER_ARGS)
    ))


@tool
def save_summary(title: str, content: str) -> str:
    """검색 결과 요약을 로컬 KB에 저장합니다.

    Args:
        title: 요약 제목 (예: "Lambda 콜드 스타트 최적화")
        content: 요약 내용

    Returns:
        저장 결과 메시지
    """
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_title = title.replace(" ", "-").replace("/", "-")[:50]
    filepath = SUMMARY_DIR / f"{timestamp}-{safe_title}.md"
    filepath.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")
    return f"저장 완료: {filepath}"


SYSTEM_PROMPT = """당신은 AWS 기술 문서 검색 및 요약 전문 Agent입니다.

## 역할
MCP를 통해 AWS 공식 문서를 검색하고, 사용자 질문에 정확하게 답변합니다.

## 도구 사용 지침
- AWS 서비스/기능 질문 시 → MCP 도구(search_documentation, read_documentation 등)로 검색
- 검색 결과 요약 저장 요청 시 → save_summary 호출
- 여러 문서를 참조해야 하면 검색을 여러 번 수행

## 응답 원칙
- 한국어로 응답
- 검색 결과의 출처(URL) 명시
- 핵심 내용을 간결하게 요약
- 코드 예시가 있으면 포함
"""


def create_mcp_agent() -> Agent:
    """MCP 연동 Agent 인스턴스를 생성합니다.

    MCPClient를 tools에 직접 전달하면 Agent가 lifecycle을 자동 관리합니다.
    """
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION_NAME)
    mcp_client = _create_mcp_client()

    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[mcp_client, save_summary],  # MCP 도구 + 커스텀 도구 혼합
    )


if __name__ == "__main__":
    agent = create_mcp_agent()
    print("🔌 MCP Agent 시작 (AWS Documentation 검색)")
    print("   (종료: quit)\n")

    while True:
        user_input = input("질문: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        if user_input:
            print(f"\n{agent(user_input)}\n")
