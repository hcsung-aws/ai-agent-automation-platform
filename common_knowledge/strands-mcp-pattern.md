# Strands SDK MCP 연동 패턴

## Managed Integration (권장)

MCPClient를 Agent tools에 직접 전달하면 lifecycle 자동 관리:

```python
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="uvx", args=["mcp-server@latest"])
))

agent = Agent(tools=[mcp_client])
```

## MCP + @tool 혼합

```python
agent = Agent(tools=[mcp_client, my_custom_tool])
```

## Transport 옵션

| Transport | 용도 | import |
|-----------|------|--------|
| stdio | 로컬 프로세스 | `from mcp import stdio_client, StdioServerParameters` |
| Streamable HTTP | 원격 서버 | `from mcp.client.streamable_http import streamablehttp_client` |
| SSE | 레거시 HTTP | `from mcp.client.sse import sse_client` |
| AWS IAM | AgentCore Gateway | `from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client` |

## 다중 서버 + prefix

```python
aws_client = MCPClient(..., prefix="aws")
db_client = MCPClient(..., prefix="db")
agent = Agent(tools=[aws_client, db_client])
# 도구 이름: aws_search, db_query 등
```

## Manual Context Management

lifecycle을 직접 제어해야 할 때:

```python
with mcp_client:
    tools = mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
    agent("query")  # with 블록 안에서만 사용 가능
```

## 의존성

```
mcp>=1.0.0
```

AgentCore Gateway 사용 시:
```
mcp-proxy-for-aws
```

## Last Updated
Mickey 17 - 2026-02-19
