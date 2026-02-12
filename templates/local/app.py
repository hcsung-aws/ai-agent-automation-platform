"""AIOps 스타터 킷 - Chainlit UI.

이 파일은 Supervisor Agent와 대화하는 웹 UI를 제공합니다.
"""
import json
import chainlit as cl
import boto3
from agents.supervisor import create_supervisor
from agents.case_tools import save_case

# Supervisor 인스턴스
supervisor = None
_bedrock_runtime = None


def _get_bedrock_runtime():
    global _bedrock_runtime
    if _bedrock_runtime is None:
        _bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")
    return _bedrock_runtime


def _summarize_conversation(user_input: str, agent_response: str) -> dict:
    """대화를 사례 문서 형식으로 요약."""
    client = _get_bedrock_runtime()
    response = client.converse(
        modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        messages=[{
            "role": "user",
            "content": [{"text": f"""다음 대화를 사례 문서로 요약하세요. JSON만 응답하세요. 다른 텍스트 없이 JSON만 출력하세요.

{{"title": "한 줄 제목", "problem": "문제 상황 요약", "resolution": "해결 과정과 결과", "tags": "쉼표구분태그"}}

대화:
사용자: {user_input}
Agent: {agent_response[:3000]}"""}]
        }],
        system=[{"text": "사례 문서 요약기. JSON만 출력한다."}],
    )
    text = response["output"]["message"]["content"][0]["text"]
    if "```" in text:
        text = text.split("```")[1].removeprefix("json").strip()
    return json.loads(text)


@cl.on_chat_start
async def start():
    """채팅 시작 시 Supervisor 초기화."""
    global supervisor
    supervisor = create_supervisor()
    cl.user_session.set("messages", {})
    cl.user_session.set("pending_case", None)

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

    msg = cl.Message(content="")
    await msg.send()

    response = supervisor(message.content)

    msg.content = str(response)
    await msg.update()

    # 피드백용 대화 쌍 저장
    messages = cl.user_session.get("messages", {})
    messages[msg.id] = {
        "user_input": message.content,
        "agent_response": str(response),
    }
    cl.user_session.set("messages", messages)


@cl.on_feedback
async def on_feedback(feedback: cl.types.Feedback):
    """긍정 피드백 시 사례 저장 제안."""
    if feedback.value != 1:
        return

    messages = cl.user_session.get("messages", {})
    pair = messages.get(feedback.forId)
    if not pair:
        return

    try:
        case_data = _summarize_conversation(pair["user_input"], pair["agent_response"])
    except Exception as e:
        print(f"[Case] 요약 실패: {e}")
        return

    cl.user_session.set("pending_case", case_data)

    preview = (
        f"📝 **사례 저장 제안**\n\n"
        f"**제목**: {case_data['title']}\n\n"
        f"**문제**: {case_data['problem']}\n\n"
        f"**해결**: {case_data['resolution']}\n\n"
        f"**태그**: {case_data.get('tags', '')}"
    )

    actions = [
        cl.Action(name="confirm_case", label="✅ 저장", value="confirm"),
        cl.Action(name="reject_case", label="❌ 취소", value="reject"),
    ]

    await cl.Message(content=preview, actions=actions).send()


@cl.action_callback("confirm_case")
async def on_confirm(action: cl.Action):
    """사례 저장 확인."""
    case_data = cl.user_session.get("pending_case")
    if not case_data:
        return

    result = save_case(
        title=case_data["title"],
        problem=case_data["problem"],
        resolution=case_data["resolution"],
        tags=case_data.get("tags", ""),
    )
    cl.user_session.set("pending_case", None)
    await cl.Message(content=str(result)).send()


@cl.action_callback("reject_case")
async def on_reject(action: cl.Action):
    """사례 저장 취소."""
    cl.user_session.set("pending_case", None)
    await cl.Message(content="사례 저장을 취소했습니다.").send()


@cl.on_chat_end
async def end():
    """채팅 종료 시 정리."""
    global supervisor
    supervisor = None
