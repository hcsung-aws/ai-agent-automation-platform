"""AIOps 스타터 킷 - Chainlit UI.

이 파일은 Supervisor Agent와 대화하는 웹 UI를 제공합니다.
"""
import inspect
import json
import chainlit as cl
from strands.hooks import HookProvider, BeforeToolCallEvent, AfterToolCallEvent
from agents import supervisor as sup_module
from agents.supervisor import create_supervisor
from feedback_store import save_feedback


class ToolCallTracker(HookProvider):
    """Supervisor의 도구 호출을 추적하여 추론 과정을 기록."""

    def __init__(self):
        self.calls = []

    def register_hooks(self, registry):
        registry.add_callback(BeforeToolCallEvent, self._on_before)
        registry.add_callback(AfterToolCallEvent, self._on_after)

    def _on_before(self, event):
        self.calls.append({"name": event.tool_use["name"], "input": event.tool_use.get("input", {})})

    def _on_after(self, event):
        if not self.calls:
            return
        self.calls[-1]["status"] = event.result["status"]
        parts = [c["text"] for c in event.result.get("content", []) if isinstance(c, dict) and "text" in c]
        self.calls[-1]["output"] = "\n".join(parts)

    def reset(self):
        self.calls = []


# Supervisor 인스턴스
supervisor = None
_tracker = ToolCallTracker()


def _format_reasoning(calls):
    """도구 호출 기록을 처리 과정 요약 + 상세 내용 마크다운으로 변환."""
    if not calls:
        return ""

    lines = ["\n\n---\n🔍 **처리 과정**"]
    for i, call in enumerate(calls, 1):
        name = call["name"]
        icon = "✅" if call.get("status") == "success" else "❌"
        if name.startswith("ask_") and name.endswith("_agent"):
            display = name.replace("ask_", "").replace("_agent", "").replace("_", " ").title()
            lines.append(f"{i}. {icon} {display} Agent에게 질문")
        else:
            lines.append(f"{i}. {icon} `{name}` 실행")

    lines.append("\n📋 **상세 보기**\n")
    for call in calls:
        inp = json.dumps(call.get("input", {}), ensure_ascii=False)[:200]
        lines.append(f"**{call['name']}**")
        lines.append(f"- 입력: `{inp}`")
        out = call.get("output", "")
        if out:
            lines.append(f"- 결과:\n\n{out[:2000]}")
        lines.append("")

    return "\n".join(lines)


def _init_supervisor():
    """Supervisor를 생성하고 ToolCallTracker를 연결."""
    global supervisor
    supervisor = create_supervisor()
    supervisor.hooks.add_hook(_tracker)


@cl.on_chat_start
async def start():
    """채팅 시작 시 Supervisor 초기화."""
    _init_supervisor()
    cl.user_session.set("messages", {})
    cl.user_session.set("awaiting_feedback_comment", False)

    await cl.Message(content=_build_welcome()).send()


def _build_welcome() -> str:
    """supervisor.py의 ask_*_agent 도구를 감지하여 환영 메시지를 동적 생성."""
    lines = ["🚀 **AIOps 스타터 킷에 오신 것을 환영합니다!**\n\n현재 등록된 Agent:"]
    for name, obj in inspect.getmembers(sup_module, predicate=inspect.isfunction):
        if name.startswith("ask_") and name.endswith("_agent"):
            doc = (obj.__doc__ or "").strip().split("\n")[0]
            display = name.replace("ask_", "").replace("_agent", "").replace("_", " ").title()
            lines.append(f"- **{display} Agent**: {doc}")
    lines.append("\nSupervisor가 적절한 Agent에게 질문을 전달합니다.")
    return "\n".join(lines)


@cl.on_message
async def main(message: cl.Message):
    """사용자 메시지 처리."""
    global supervisor

    # 부정 피드백 코멘트 대기 중이면 처리
    if cl.user_session.get("awaiting_feedback_comment"):
        await _handle_feedback_comment(message)
        return

    if supervisor is None:
        _init_supervisor()

    _tracker.reset()
    response = supervisor(message.content)

    content = str(response) + _format_reasoning(_tracker.calls)
    msg_id = cl.user_session.get("_msg_counter", 0)
    cl.user_session.set("_msg_counter", msg_id + 1)
    mid = f"msg-{msg_id}"

    actions = [
        cl.Action(name="feedback_positive", payload={"mid": mid}, label="👍 좋아요"),
        cl.Action(name="feedback_negative", payload={"mid": mid}, label="👎 아쉬워요"),
    ]
    msg = cl.Message(content=content, actions=actions)
    await msg.send()

    # 피드백용 대화 쌍 저장
    messages = cl.user_session.get("messages", {})
    messages[mid] = {
        "user_input": message.content,
        "agent_response": str(response),
    }
    cl.user_session.set("messages", messages)


@cl.action_callback("feedback_positive")
async def on_positive(action: cl.Action):
    """긍정 피드백 저장."""
    pair = cl.user_session.get("messages", {}).get(action.payload["mid"])
    if not pair:
        return
    save_feedback(
        message_id=action.payload["mid"],
        rating="positive",
        user_input=pair["user_input"],
        agent_response=pair["agent_response"],
    )
    await cl.Message(content="✅ 피드백 감사합니다! 👍").send()


@cl.action_callback("feedback_negative")
async def on_negative(action: cl.Action):
    """부정 피드백 — 코멘트 요청."""
    cl.user_session.set("pending_feedback_mid", action.payload["mid"])
    cl.user_session.set("awaiting_feedback_comment", True)
    await cl.Message(content="어떤 점이 아쉬웠나요? (건너뛰려면 '건너뛰기' 입력)").send()


async def _handle_feedback_comment(message: cl.Message):
    """부정 피드백 코멘트 처리."""
    cl.user_session.set("awaiting_feedback_comment", False)
    mid = cl.user_session.get("pending_feedback_mid")
    pair = cl.user_session.get("messages", {}).get(mid)
    if not pair:
        return
    comment = None if message.content.strip() == "건너뛰기" else message.content
    save_feedback(
        message_id=mid,
        rating="negative",
        user_input=pair["user_input"],
        agent_response=pair["agent_response"],
        comment=comment,
    )
    await cl.Message(content="✅ 피드백 감사합니다! 개선에 반영하겠습니다. 👎").send()


@cl.on_chat_end
async def end():
    """채팅 종료 시 정리."""
    global supervisor
    supervisor = None
