# 튜토리얼: MCP 연동 Agent 만들기

MCP(Model Context Protocol)를 사용하여 외부 도구 서버를 Agent에 연결하는 방법을 배웁니다.

예상 소요 시간: 30분

---

## 사전 준비

```bash
cd templates/local
source .venv/bin/activate
pip install "mcp>=1.0.0"
```

MCP 서버 실행에 `uvx`가 필요합니다:
```bash
pip install uv  # uvx 포함
```

→ 로컬 환경이 아직 없다면 [QUICKSTART-LOCAL.md](QUICKSTART-LOCAL.md) 먼저 진행

---

## MCP란?

MCP(Model Context Protocol)는 AI Agent가 외부 도구 서버와 통신하는 표준 프로토콜입니다.

```
┌──────────┐     MCP 프로토콜     ┌──────────────────┐
│  Agent   │ ◄──────────────────► │  MCP Server      │
│ (Strands)│                      │ (도구 제공)       │
└──────────┘                      └──────────────────┘
```

기존 `@tool` 데코레이터와의 차이:

| | @tool (커스텀) | MCP |
|---|---|---|
| 도구 위치 | Agent 코드 내부 | 외부 서버 |
| 재사용 | 프로젝트 내 | 프로젝트 간 공유 |
| 언어 | Python만 | 언어 무관 |
| 적합한 경우 | 프로젝트 고유 로직 | 범용 도구 (DB, API, 문서 검색) |

두 방식을 **혼합 사용**하는 것이 권장됩니다.

---

## Step 1: 예시 Agent 실행

프로젝트에 포함된 MCP 연동 예시를 실행합니다:

```bash
cd templates/local/agents
python mcp_agent.py
```

```
🔌 MCP Agent 시작 (AWS Documentation 검색)

질문: Lambda 콜드 스타트 줄이는 방법은?
→ MCP 서버가 AWS 문서를 검색하여 응답
```

이 Agent는 두 종류의 도구를 사용합니다:
- **MCP 도구**: AWS Documentation MCP Server의 `search_documentation`, `read_documentation`
- **커스텀 도구**: `save_summary` (검색 결과를 로컬 KB에 저장)

---

## Step 2: MCP 연동 코드 이해

### 핵심 패턴 (Managed Integration)

```python
from mcp import stdio_client, StdioServerParameters
from strands import Agent, tool
from strands.tools.mcp import MCPClient

# 1. MCP 클라이언트 생성
mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )
))

# 2. 커스텀 도구 정의
@tool
def save_summary(title: str, content: str) -> str:
    """검색 결과를 저장합니다."""
    ...

# 3. Agent에 MCP + 커스텀 도구 혼합 전달
agent = Agent(
    tools=[mcp_client, save_summary],  # 혼합 사용
)
```

`MCPClient`를 `tools`에 직접 전달하면 Agent가 연결 lifecycle을 자동 관리합니다.

---

## Step 3: Transport 옵션

MCP는 3가지 전송 방식을 지원합니다.

### stdio (로컬 프로세스)

로컬에서 MCP 서버를 프로세스로 실행합니다. 가장 간단한 방식입니다.

```python
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient

mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="uvx", args=["mcp-server-package@latest"])
))
```

### Streamable HTTP (원격 서버)

HTTP 기반 원격 MCP 서버에 연결합니다.

```python
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

mcp_client = MCPClient(
    lambda: streamablehttp_client("http://localhost:8000/mcp")
)
```

인증이 필요한 경우:
```python
mcp_client = MCPClient(
    lambda: streamablehttp_client(
        url="https://api.example.com/mcp/",
        headers={"Authorization": f"Bearer {os.getenv('MCP_TOKEN')}"}
    )
)
```

### AgentCore Gateway (AWS IAM 인증)

AWS에서 관리형 MCP 서버를 사용할 때 IAM 인증을 적용합니다.

```bash
pip install mcp-proxy-for-aws
```

```python
from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client
from strands.tools.mcp import MCPClient

mcp_client = MCPClient(lambda: aws_iam_streamablehttp_client(
    endpoint="https://your-service.us-east-1.amazonaws.com/mcp",
    aws_region="us-east-1",
    aws_service="bedrock-agentcore"
))
```

---

## Step 4: 여러 MCP 서버 연결

여러 MCP 서버의 도구를 하나의 Agent에서 사용할 수 있습니다:

```python
aws_docs = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"])
), prefix="aws")  # 도구 이름 충돌 방지

db_server = MCPClient(
    lambda: streamablehttp_client("http://localhost:9000/mcp"),
    prefix="db"
)

agent = Agent(tools=[aws_docs, db_server, my_custom_tool])
```

`prefix`를 사용하면 도구 이름이 `aws_search_documentation`, `db_query` 등으로 구분됩니다.

---

## Step 5: Supervisor에 연결

MCP Agent를 기존 Multi-Agent 구조에 연결합니다.

`supervisor.py`에 추가:

```python
_mcp_agent = None

def _get_mcp_agent():
    global _mcp_agent
    if _mcp_agent is None:
        from mcp_agent import create_mcp_agent
        _mcp_agent = create_mcp_agent()
    return _mcp_agent

@tool
def ask_mcp_agent(query: str) -> str:
    """AWS 문서 검색 Agent에게 질문합니다.

    AWS 서비스 사용법, 설정 방법, 모범 사례 등을 검색합니다.

    Args:
        query: AWS 관련 질문

    Returns:
        검색 결과 기반 응답
    """
    agent = _get_mcp_agent()
    return str(agent(query))
```

---

## 다음 단계

- **Agent Builder로 MCP Agent 생성**: `kiro chat --agent agent-builder`에서 "MCP 연동 Agent 만들어줘"
- **커스텀 MCP 서버 만들기**: [Strands MCP 문서](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/mcp-tools/)
- **AWS 배포**: [deployment-guide.md](deployment-guide.md)

---

## 트러블슈팅

### uvx 명령어를 찾을 수 없음
```bash
pip install uv
```

### MCP 서버 연결 실패
- MCP 서버 패키지가 설치 가능한지 확인: `uvx awslabs.aws-documentation-mcp-server@latest --help`
- 네트워크 연결 확인

### 도구가 발견되지 않음
- MCP 서버가 `list_tools`를 올바르게 구현하는지 확인
- `MCPClient`를 `with` 문 밖에서 사용하면 Manual 방식에서는 실패 (Managed 방식 권장)
