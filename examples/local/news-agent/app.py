"""AIOps 스타터 킷 - Chainlit UI.

이 파일은 Supervisor Agent와 대화하는 웹 UI를 제공합니다.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "agents"))
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
import json
import chainlit as cl
from strands.hooks import HookProvider, BeforeToolCallEvent, AfterToolCallEvent
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

    await cl.Message(
        content="""🚀 **AIOps 스타터 킷에 오신 것을 환영합니다!**

현재 등록된 Agent:
- 📰 **뉴스 크롤링** — 최신 뉴스 수집, 키워드 검색, 날짜별 저장/조회
- 📊 **뉴스 분석** — 트렌드 분석, 키워드 빈도, 소스별 비교
- 📖 **프로젝트 가이드** — 사용법, 배포 방법, 트러블슈팅

이렇게 물어보세요:
- "오늘 뉴스 가져와"
- "AI 관련 뉴스 검색해줘"
- "저장된 뉴스 트렌드 분석해줘"
- "어떻게 시작해요?"

Supervisor가 적절한 Agent에게 질문을 전달합니다."""
    ).send()


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
    response = await asyncio.to_thread(supervisor, message.content)

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

    # 피드백용 대화 쌍 + 메시지 객체 저장
    messages = cl.user_session.get("messages", {})
    messages[mid] = {
        "user_input": message.content,
        "agent_response": str(response),
        "msg": msg,
    }
    cl.user_session.set("messages", messages)


async def _mark_feedback(action: cl.Action, label: str):
    """피드백 버튼을 제거하고 선택 결과를 메시지에 표시."""
    pair = cl.user_session.get("messages", {}).get(action.payload["mid"])
    if not pair:
        return None
    msg = pair.get("msg")
    if msg:
        await msg.remove_actions()
        msg.actions = []
        msg.content += f"\n\n> {label}"
        await msg.update()
    return pair


@cl.action_callback("feedback_positive")
async def on_positive(action: cl.Action):
    """긍정 피드백 저장."""
    pair = await _mark_feedback(action, "✅ 👍 좋아요")
    if not pair:
        return
    save_feedback(
        message_id=action.payload["mid"],
        rating="positive",
        user_input=pair["user_input"],
        agent_response=pair["agent_response"],
    )


@cl.action_callback("feedback_negative")
async def on_negative(action: cl.Action):
    """부정 피드백 — 코멘트 요청."""
    pair = await _mark_feedback(action, "👎 아쉬워요")
    if not pair:
        return
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
