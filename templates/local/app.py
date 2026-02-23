"""AIOps 스타터 킷 - Chainlit UI.

이 파일은 Supervisor Agent와 대화하는 웹 UI를 제공합니다.

동작 모드 (환경변수로 자동 전환):
- 로컬 모드: AGENT_RUNTIME_ARN 미설정 → Agent 직접 호출
- API 모드:  AGENT_RUNTIME_ARN 설정 → AgentCore API 호출
"""
import asyncio
import inspect
import json
import os
import uuid

import chainlit as cl
from feedback_store import save_feedback

# --- 모드 판별 ---
AGENT_RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN", "")
_IS_API_MODE = bool(AGENT_RUNTIME_ARN)

# --- 로컬 모드 전용 import ---
if not _IS_API_MODE:
    from strands.hooks import HookProvider, BeforeToolCallEvent, AfterToolCallEvent
    from agents import supervisor as sup_module
    from agents.supervisor import create_supervisor


# === 로컬 모드: ToolCallTracker ===

class ToolCallTracker:
    """Supervisor의 도구 호출을 추적하여 추론 과정을 기록 (로컬 모드 전용)."""

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


# --- 인스턴스 ---
supervisor = None
_tracker = ToolCallTracker() if not _IS_API_MODE else None


# === API 모드: AgentCore 호출 ===

_agentcore_client = None


def _get_agentcore_client():
    global _agentcore_client
    if _agentcore_client is None:
        import boto3
        _agentcore_client = boto3.client(
            "bedrock-agentcore",
            region_name=os.environ.get("BEDROCK_REGION", "us-east-1"),
        )
    return _agentcore_client


def _invoke_agentcore(prompt: str, session_id: str) -> str:
    """AgentCore Runtime API 호출."""
    client = _get_agentcore_client()
    response = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        runtimeSessionId=session_id,
        payload=json.dumps({"prompt": prompt}).encode(),
    )

    content_type = response.get("contentType", "")

    if "text/event-stream" in content_type:
        # Streaming 응답
        parts = []
        for line in response["response"].iter_lines(chunk_size=10):
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    parts.append(decoded[6:])
        return "\n".join(parts)
    elif content_type == "application/json":
        # JSON 응답
        chunks = []
        for chunk in response.get("response", []):
            chunks.append(chunk.decode("utf-8"))
        return json.loads("".join(chunks)).get("response", "".join(chunks))
    else:
        # 기타
        return str(response.get("response", ""))


# === 공통 함수 ===

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
    """Supervisor를 생성하고 ToolCallTracker를 연결 (로컬 모드 전용)."""
    global supervisor
    if _IS_API_MODE:
        return
    supervisor = create_supervisor()
    supervisor.hooks.add_hook(_tracker)


async def _call_agent(prompt: str, session_id: str) -> tuple[str, str]:
    """Agent 호출. 반환: (응답 텍스트, 추론 과정 마크다운)."""
    if _IS_API_MODE:
        response = await asyncio.to_thread(_invoke_agentcore, prompt, session_id)
        return response, ""
    else:
        _tracker.reset()
        response = await asyncio.to_thread(supervisor, prompt)
        return str(response), _format_reasoning(_tracker.calls)


def _build_welcome() -> str:
    """환영 메시지 생성."""
    if _IS_API_MODE:
        # API 모드: 환경변수에서 Agent 목록 읽기
        agent_names = os.environ.get("AGENT_NAMES", "Guide")
        lines = ["🚀 **AIOps 스타터 킷에 오신 것을 환영합니다!** (AWS 모드)\n\n등록된 Agent:"]
        for name in agent_names.split(","):
            lines.append(f"- **{name.strip()} Agent**")
        lines.append("\nSupervisor가 적절한 Agent에게 질문을 전달합니다.")
        return "\n".join(lines)
    else:
        # 로컬 모드: supervisor.py에서 동적 감지
        lines = ["🚀 **AIOps 스타터 킷에 오신 것을 환영합니다!**\n\n현재 등록된 Agent:"]
        for name, obj in inspect.getmembers(sup_module, predicate=inspect.isfunction):
            if name.startswith("ask_") and name.endswith("_agent"):
                doc = (obj.__doc__ or "").strip().split("\n")[0]
                display = name.replace("ask_", "").replace("_agent", "").replace("_", " ").title()
                lines.append(f"- **{display} Agent**: {doc}")
        lines.append("\nSupervisor가 적절한 Agent에게 질문을 전달합니다.")
        return "\n".join(lines)


# === Chainlit 이벤트 핸들러 ===

@cl.on_chat_start
async def start():
    """채팅 시작 시 초기화."""
    _init_supervisor()
    cl.user_session.set("session_id", str(uuid.uuid4()))
    cl.user_session.set("messages", {})
    cl.user_session.set("awaiting_feedback_comment", False)
    await cl.Message(content=_build_welcome()).send()


@cl.on_message
async def main(message: cl.Message):
    """사용자 메시지 처리."""
    global supervisor

    # 부정 피드백 코멘트 대기 중이면 처리
    if cl.user_session.get("awaiting_feedback_comment"):
        await _handle_feedback_comment(message)
        return

    if not _IS_API_MODE and supervisor is None:
        _init_supervisor()

    session_id = cl.user_session.get("session_id", str(uuid.uuid4()))
    response_text, reasoning = await _call_agent(message.content, session_id)

    content = response_text + reasoning
    msg_id = cl.user_session.get("_msg_counter", 0)
    cl.user_session.set("_msg_counter", msg_id + 1)
    mid = f"msg-{msg_id}"

    actions = [
        cl.Action(name="feedback_positive", payload={"mid": mid}, label="👍 좋아요"),
        cl.Action(name="feedback_negative", payload={"mid": mid}, label="👎 아쉬워요"),
    ]
    msg = cl.Message(content=content, actions=actions)
    await msg.send()

    messages = cl.user_session.get("messages", {})
    messages[mid] = {
        "user_input": message.content,
        "agent_response": response_text,
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
