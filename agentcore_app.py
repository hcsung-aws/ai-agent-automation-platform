"""AgentCore entry point for DevOps Agent."""
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from src.agent.devops_agent import create_devops_agent

app = BedrockAgentCoreApp()
agent = create_devops_agent()


@app.entrypoint
def invoke(payload):
    """Handler for agent invocation."""
    user_message = payload.get(
        "prompt", "안녕하세요, 무엇을 도와드릴까요?"
    )
    response = agent(user_message)
    
    # Extract text from response
    if hasattr(response, "message"):
        content = response.message.get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", str(response))
    return str(response)


if __name__ == "__main__":
    app.run()
