"""Chainlit UI for Supervisor Agent (Multi-Agent)."""
import chainlit as cl
from src.agent.supervisor_agent import LoggingSupervisorAgent

agent = None


@cl.on_chat_start
async def start():
    """Initialize agent on chat start."""
    global agent
    agent = LoggingSupervisorAgent()
    
    await cl.Message(
        content=f"안녕하세요! 게임 운영 AI 에이전트입니다.\n"
        f"(세션 ID: {agent.session_id})\n\n"
        "**DevOps 영역:**\n"
        "- 인프라 모니터링, EC2 상태, 배포 이력\n"
        "- 장애 티켓 관리, 운영 가이드 검색\n\n"
        "**데이터 분석 영역:**\n"
        "- DAU/MAU, 리텐션 분석\n"
        "- 가챠 확률, 재화 흐름, 퀘스트 완료율\n\n"
        "무엇을 도와드릴까요?"
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle user messages."""
    global agent
    
    if agent is None:
        agent = LoggingSupervisorAgent()
    
    msg = cl.Message(content="")
    await msg.send()
    
    response = agent(message.content)
    
    msg.content = response
    await msg.update()
