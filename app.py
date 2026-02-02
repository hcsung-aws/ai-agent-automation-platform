"""Chainlit UI for Supervisor Agent (Multi-Agent) with process visualization and feedback."""
import asyncio
import time
from typing import Callable
import chainlit as cl
from strands import Agent, tool
from strands.models import BedrockModel

from src.agent.devops_agent import create_devops_agent
from src.agent.analytics_agent import create_analytics_agent
from src.agent.godot_review_agent import create_godot_review_agent
from src.utils.execution_logger import (
    log_execution, generate_session_id, 
    log_feedback, generate_message_id
)


def create_visualized_supervisor(on_step: Callable):
    """Create supervisor with step callbacks for visualization."""
    
    devops_agent = None
    analytics_agent = None
    godot_review_agent = None
    
    @tool
    def ask_devops_agent(query: str) -> str:
        """DevOps 전문가 에이전트에게 질문합니다."""
        nonlocal devops_agent
        on_step("devops", "start", query)
        if devops_agent is None:
            devops_agent = create_devops_agent()
        response = str(devops_agent(query))
        on_step("devops", "end", response)
        return response

    @tool
    def ask_analytics_agent(query: str) -> str:
        """데이터 분석 전문가 에이전트에게 질문합니다."""
        nonlocal analytics_agent
        on_step("analytics", "start", query)
        if analytics_agent is None:
            analytics_agent = create_analytics_agent()
        response = str(analytics_agent(query))
        on_step("analytics", "end", response)
        return response

    @tool
    def ask_godot_review_agent(query: str) -> str:
        """Godot/GDScript 코드 리뷰 전문가 에이전트에게 질문합니다."""
        nonlocal godot_review_agent
        on_step("godot_review", "start", query)
        if godot_review_agent is None:
            godot_review_agent = create_godot_review_agent()
        response = str(godot_review_agent(query))
        on_step("godot_review", "end", response)
        return response

    SYSTEM_PROMPT = """당신은 게임 운영 총괄 AI 에이전트(Supervisor)입니다.
사용자의 요청을 분석하여 **가장 적합한 하나의 전문가 에이전트**에게 작업을 위임합니다.

## 전문가 에이전트 및 담당 영역

### DevOps Agent (ask_devops_agent)
- 인프라 모니터링, CloudWatch 메트릭
- EC2 인스턴스 상태 확인
- 장애 티켓 생성/조회
- CloudFormation 배포 이력
- 키워드: 서버, 인프라, EC2, 장애, 배포, 모니터링

### Analytics Agent (ask_analytics_agent)
- DAU/MAU, 리텐션 분석
- 가챠/뽑기 확률 분석
- 재화 흐름 분석 (획득/소비)
- 퀘스트/업적 완료율
- 키워드: 분석, DAU, 가챠, 재화, 퀘스트, 통계

### Godot Review Agent (ask_godot_review_agent)
- GDScript 코드 리뷰
- Godot 베스트 프랙티스 검증
- 성능 이슈 분석
- 키워드: 코드, 리뷰, GDScript, Godot, 스크립트

## 위임 규칙

1. **단일 에이전트 원칙**: 요청당 하나의 에이전트만 호출
2. **맥락 유지**: 이전 대화가 특정 에이전트 영역이면 같은 에이전트에 위임
3. **명확한 영역**: 키워드로 영역 판단, 애매하면 사용자에게 확인
4. **복합 요청**: 여러 영역이 필요하면 순차적으로 호출 (동시 호출 금지)

## 예시

- "코드 리뷰해줘" → Godot Review Agent만 호출
- "구체적인 코드 제안해줘" (이전이 코드 리뷰) → Godot Review Agent만 호출
- "서버 상태 확인해줘" → DevOps Agent만 호출
- "DAU 분석해줘" → Analytics Agent만 호출

## 응답 원칙
- 한국어로 응답
- **에이전트 응답을 반드시 텍스트로 출력할 것**
- 에이전트가 반환한 전체 내용을 그대로 복사하여 응답에 포함
- 요약하거나 생략하지 말 것
- 도구 호출 후 반드시 결과를 사용자에게 보여줄 것
"""

    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
    )
    
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[ask_devops_agent, ask_analytics_agent, ask_godot_review_agent],
    )


@cl.on_chat_start
async def start():
    """Initialize session."""
    session_id = generate_session_id()
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("awaiting_feedback_comment", False)
    cl.user_session.set("feedback_given", {})  # Track which messages have feedback
    
    await cl.Message(
        content=f"안녕하세요! 게임 운영 AI 에이전트입니다.\n"
        f"(세션 ID: {session_id})\n\n"
        "**DevOps 영역:** 인프라 모니터링, 장애 티켓, 배포 이력\n"
        "**Analytics 영역:** DAU/MAU, 가챠 확률, 재화 흐름\n"
        "**Godot Review 영역:** GDScript 코드 리뷰, 성능 분석\n\n"
        "질문하시면 처리 과정을 단계별로 보여드립니다."
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle user messages with step visualization and feedback buttons."""
    if cl.user_session.get("awaiting_feedback_comment"):
        await handle_feedback_comment(message)
        return
    
    session_id = cl.user_session.get("session_id")
    message_id = generate_message_id()
    steps_log = []
    full_agent_responses = {}  # 에이전트별 전체 응답 저장
    
    def on_step(agent_name: str, phase: str, content: str):
        steps_log.append({
            "agent": agent_name,
            "phase": phase,
            "content": content[:200] + "..." if len(content) > 200 else content,
        })
        if phase == "end":
            full_agent_responses[agent_name] = content  # 전체 응답 저장
    
    status_msg = cl.Message(content="🔄 **Supervisor Agent** 분석 중...")
    await status_msg.send()
    
    loop = asyncio.get_event_loop()
    
    def run_agent():
        agent = create_visualized_supervisor(on_step)
        return str(agent(message.content))
    
    start_time = time.time()
    try:
        response = await loop.run_in_executor(None, run_agent)
        status = "success"
    except Exception as e:
        response = f"오류 발생: {e}"
        status = "error"
    
    elapsed = time.time() - start_time
    
    # Build process visualization
    process_lines = ["## 📋 처리 과정\n"]
    sub_agents = []
    
    for i, step in enumerate(steps_log):
        if step["agent"] == "devops":
            agent_emoji, agent_label = "🔧", "DevOps Agent"
        elif step["agent"] == "analytics":
            agent_emoji, agent_label = "📊", "Analytics Agent"
        else:
            agent_emoji, agent_label = "🎮", "Godot Review Agent"
        
        if step["phase"] == "start":
            process_lines.append(f"**{i+1}. {agent_emoji} {agent_label} 호출**")
            process_lines.append(f"   - 요청: {step['content']}\n")
        else:
            process_lines.append(f"   - 응답: {step['content']}\n")
            sub_agents.append(step["agent"])
    
    process_lines.append(f"⏱️ 총 소요시간: {elapsed:.1f}초")
    
    status_msg.content = "\n".join(process_lines)
    await status_msg.update()
    
    # Store context for feedback and detail view
    cl.user_session.set(f"feedback_{message_id}", {
        "user_input": message.content,
        "response": response,
    })
    cl.user_session.set(f"detail_{message_id}", full_agent_responses)
    
    # Build actions - feedback + detail view buttons
    actions = [
        cl.Action(name="feedback_positive", payload={"message_id": message_id}, label="👍 좋아요"),
        cl.Action(name="feedback_negative", payload={"message_id": message_id}, label="👎 아쉬워요"),
    ]
    
    # Add detail view button for each agent that responded
    for agent_name in full_agent_responses.keys():
        if agent_name == "devops":
            label = "🔧 DevOps 상세"
        elif agent_name == "analytics":
            label = "📊 Analytics 상세"
        else:
            label = "🎮 Godot Review 상세"
        actions.append(
            cl.Action(name="show_detail", payload={"message_id": message_id, "agent": agent_name}, label=label)
        )
    
    response_msg = cl.Message(content=f"## 💬 응답\n\n{response}", actions=actions)
    await response_msg.send()
    
    # Store message reference for later update
    cl.user_session.set(f"msg_{message_id}", response_msg)
    
    log_execution(
        session_id=session_id,
        agent_type="supervisor",
        user_input=message.content,
        agent_response=response,
        tools_used=[],
        sub_agents=list(set(sub_agents)),
        execution_time_ms=int(elapsed * 1000),
        status=status,
    )


async def update_feedback_display(message_id: str, rating: str, comment: str = None):
    """Update message to show feedback status with change option."""
    feedback_given = cl.user_session.get("feedback_given", {})
    feedback_given[message_id] = {"rating": rating, "comment": comment}
    cl.user_session.set("feedback_given", feedback_given)
    
    # Show feedback status with change button
    emoji = "👍" if rating == "positive" else "👎"
    status_text = f"✅ 피드백: {emoji}"
    if comment:
        status_text += f" (코멘트: {comment[:30]}...)" if len(comment) > 30 else f" (코멘트: {comment})"
    
    actions = [
        cl.Action(name="change_feedback", payload={"message_id": message_id}, label="🔄 피드백 변경"),
    ]
    
    await cl.Message(content=status_text, actions=actions).send()


@cl.action_callback("show_detail")
async def on_show_detail(action: cl.Action):
    """Show detailed agent response."""
    message_id = action.payload.get("message_id")
    agent_name = action.payload.get("agent")
    
    full_responses = cl.user_session.get(f"detail_{message_id}", {})
    detail_content = full_responses.get(agent_name, "상세 내용을 찾을 수 없습니다.")
    
    if agent_name == "devops":
        title = "🔧 DevOps Agent 상세 응답"
    elif agent_name == "analytics":
        title = "📊 Analytics Agent 상세 응답"
    else:
        title = "🎮 Godot Review Agent 상세 응답"
    
    await cl.Message(content=f"## {title}\n\n{detail_content}").send()


@cl.action_callback("feedback_positive")
async def on_positive_feedback(action: cl.Action):
    """Handle positive feedback."""
    message_id = action.payload.get("message_id")
    feedback_given = cl.user_session.get("feedback_given", {})
    
    # Check if already gave feedback
    if message_id in feedback_given:
        await cl.Message(content="⚠️ 이미 피드백을 제출하셨습니다. 변경하려면 '피드백 변경' 버튼을 눌러주세요.").send()
        return
    
    session_id = cl.user_session.get("session_id")
    context = cl.user_session.get(f"feedback_{message_id}", {})
    
    log_feedback(
        session_id=session_id,
        message_id=message_id,
        rating="positive",
        user_input=context.get("user_input", ""),
        agent_response=context.get("response", ""),
    )
    
    await update_feedback_display(message_id, "positive")


@cl.action_callback("feedback_negative")
async def on_negative_feedback(action: cl.Action):
    """Handle negative feedback - ask for comment."""
    message_id = action.payload.get("message_id")
    feedback_given = cl.user_session.get("feedback_given", {})
    
    # Check if already gave feedback
    if message_id in feedback_given:
        await cl.Message(content="⚠️ 이미 피드백을 제출하셨습니다. 변경하려면 '피드백 변경' 버튼을 눌러주세요.").send()
        return
    
    cl.user_session.set("pending_feedback_id", message_id)
    cl.user_session.set("awaiting_feedback_comment", True)
    cl.user_session.set("feedback_is_change", False)
    
    await cl.Message(
        content="😔 아쉬운 점이 있으셨군요. 어떤 부분이 개선되면 좋을까요?\n(입력하시거나 '건너뛰기'를 입력해주세요)"
    ).send()


@cl.action_callback("change_feedback")
async def on_change_feedback(action: cl.Action):
    """Allow user to change their feedback."""
    message_id = action.payload.get("message_id")
    
    # Remove from feedback_given to allow new feedback
    feedback_given = cl.user_session.get("feedback_given", {})
    if message_id in feedback_given:
        del feedback_given[message_id]
        cl.user_session.set("feedback_given", feedback_given)
    
    # Show new feedback options
    actions = [
        cl.Action(name="feedback_positive", payload={"message_id": message_id}, label="👍 좋아요"),
        cl.Action(name="feedback_negative", payload={"message_id": message_id}, label="👎 아쉬워요"),
    ]
    
    await cl.Message(content="피드백을 다시 선택해주세요:", actions=actions).send()


async def handle_feedback_comment(message: cl.Message):
    """Handle feedback comment."""
    cl.user_session.set("awaiting_feedback_comment", False)
    session_id = cl.user_session.get("session_id")
    message_id = cl.user_session.get("pending_feedback_id")
    context = cl.user_session.get(f"feedback_{message_id}", {})
    
    comment = None if message.content.strip() == "건너뛰기" else message.content
    
    log_feedback(
        session_id=session_id,
        message_id=message_id,
        rating="negative",
        user_input=context.get("user_input", ""),
        agent_response=context.get("response", ""),
        comment=comment,
    )
    
    await update_feedback_display(message_id, "negative", comment)
