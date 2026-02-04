"""AIOps 스타터 킷 - Chainlit UI.

이 파일은 Supervisor Agent와 대화하는 웹 UI를 제공합니다.
"""
import chainlit as cl
from agents.supervisor import create_supervisor

# Supervisor 인스턴스
supervisor = None


@cl.on_chat_start
async def start():
    """채팅 시작 시 Supervisor 초기화."""
    global supervisor
    supervisor = create_supervisor()
    
    await cl.Message(
        content="""🚀 **AIOps 스타터 킷에 오신 것을 환영합니다!**

무엇이든 물어보세요:
- "어떻게 시작해요?"
- "Agent 어떻게 만들어요?"
- "AWS에 배포하려면?"

Supervisor가 적절한 Agent에게 질문을 전달합니다."""
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """사용자 메시지 처리."""
    global supervisor
    
    if supervisor is None:
        supervisor = create_supervisor()
    
    # 처리 중 표시
    msg = cl.Message(content="")
    await msg.send()
    
    # Supervisor에게 질문
    response = supervisor(message.content)
    
    # 응답 전송
    msg.content = str(response)
    await msg.update()


@cl.on_chat_end
async def end():
    """채팅 종료 시 정리."""
    global supervisor
    supervisor = None
