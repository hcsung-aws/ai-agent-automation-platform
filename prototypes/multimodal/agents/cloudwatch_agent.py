"""CloudWatch Monitoring Agent - AWS 리소스 모니터링 및 알람 관리.

기능:
1. CloudWatch 알람 목록 조회
2. 메트릭 시각화 이미지 생성 (GetMetricWidgetImage API)
3. 알람 상태 요약
"""
import json
from strands import Agent, tool
from strands.models import BedrockModel
from config import MODEL_ID, REGION_NAME
from media_utils import add_image

_cloudwatch_client = None


def _get_cloudwatch_client():
    """CloudWatch 클라이언트 싱글톤."""
    global _cloudwatch_client
    if _cloudwatch_client is None:
        import boto3
        _cloudwatch_client = boto3.client("cloudwatch", region_name=REGION_NAME)
    return _cloudwatch_client


@tool
def list_alarms(state_value: str = None, max_records: int = 50) -> str:
    """CloudWatch 알람 목록을 조회합니다.
    
    Args:
        state_value: 필터링할 상태 (OK, ALARM, INSUFFICIENT_DATA). None이면 전체 조회
        max_records: 최대 조회 개수 (기본 50)
    
    Returns:
        알람 목록 (이름, 상태, 설명)
    """
    try:
        client = _get_cloudwatch_client()
        params = {"MaxRecords": max_records}
        if state_value:
            params["StateValue"] = state_value
        
        response = client.describe_alarms(**params)
        alarms = response.get("MetricAlarms", [])
        
        if not alarms:
            return f"조회된 알람이 없습니다. (필터: {state_value or '전체'})"
        
        lines = [f"총 {len(alarms)}개 알람 조회됨:\n"]
        for alarm in alarms:
            name = alarm.get("AlarmName", "N/A")
            state = alarm.get("StateValue", "N/A")
            desc = alarm.get("AlarmDescription", "설명 없음")
            lines.append(f"- **{name}** [{state}]: {desc}")
        
        return "\n".join(lines)
    except Exception as e:
        return f"알람 조회 실패: {str(e)}"


@tool
def get_metric_widget(metric_name: str, namespace: str, period: int = 300, stat: str = "Average") -> str:
    """CloudWatch 메트릭을 시각화 이미지로 생성합니다.
    
    Args:
        metric_name: 메트릭 이름 (예: CPUUtilization)
        namespace: 네임스페이스 (예: AWS/EC2)
        period: 집계 주기(초, 기본 300)
        stat: 통계 유형 (Average, Sum, Maximum 등)
    
    Returns:
        이미지 생성 결과 메시지
    """
    try:
        client = _get_cloudwatch_client()
        widget = {
            "metrics": [[namespace, metric_name]],
            "period": period,
            "stat": stat,
            "view": "timeSeries",
            "width": 800,
            "height": 400,
            "title": f"{namespace}/{metric_name}"
        }
        
        response = client.get_metric_widget_image(MetricWidget=json.dumps(widget))
        image_data = response["MetricWidgetImage"]
        
        add_image(data=image_data, caption=f"{namespace}/{metric_name} ({stat})")
        
        return f"✅ {namespace}/{metric_name} 메트릭 이미지를 생성했습니다."
    except Exception as e:
        return f"메트릭 이미지 생성 실패: {str(e)}"


@tool
def summarize_alarm_states() -> str:
    """전체 알람의 상태를 요약합니다.
    
    Returns:
        상태별 알람 개수 및 ALARM 상태 알람 목록
    """
    try:
        client = _get_cloudwatch_client()
        response = client.describe_alarms()
        alarms = response.get("MetricAlarms", [])
        
        if not alarms:
            return "등록된 알람이 없습니다."
        
        states = {"OK": 0, "ALARM": 0, "INSUFFICIENT_DATA": 0}
        alarm_list = []
        
        for alarm in alarms:
            state = alarm.get("StateValue", "UNKNOWN")
            if state in states:
                states[state] += 1
            if state == "ALARM":
                alarm_list.append(alarm.get("AlarmName", "N/A"))
        
        lines = [
            f"📊 알람 상태 요약 (총 {len(alarms)}개):",
            f"- ✅ OK: {states['OK']}개",
            f"- 🚨 ALARM: {states['ALARM']}개",
            f"- ⚠️ INSUFFICIENT_DATA: {states['INSUFFICIENT_DATA']}개"
        ]
        
        if alarm_list:
            lines.append("\n🚨 ALARM 상태 알람:")
            for name in alarm_list:
                lines.append(f"  - {name}")
        
        return "\n".join(lines)
    except Exception as e:
        return f"알람 상태 요약 실패: {str(e)}"


SYSTEM_PROMPT = """당신은 AWS CloudWatch 모니터링 전문 Agent입니다.

## 역할
CloudWatch 알람 조회, 메트릭 시각화, 알람 상태 분석을 담당합니다.

## 도구 사용 지침
- "알람 목록 보여줘", "알람 조회" → list_alarms() 호출
- "ALARM 상태만", "문제 있는 알람" → list_alarms(state_value="ALARM")
- "메트릭 차트", "그래프", "시각화" → get_metric_widget() 호출
  예: "EC2 CPU 사용률" → get_metric_widget("CPUUtilization", "AWS/EC2")
- "전체 상태", "요약", "현황" → summarize_alarm_states() 호출

## 멀티모달 출력 원칙
- 메트릭 시각화는 반드시 이미지로 제공 (get_metric_widget 사용)
- 이미지는 자동으로 사이드채널에 등록되어 UI에 표시됨
- 텍스트 설명과 이미지를 함께 제공

## 응답 원칙
- 한국어로 명확하게 응답
- 알람 상태는 이모지로 시각화 (✅ OK, 🚨 ALARM, ⚠️ INSUFFICIENT_DATA)
- 메트릭 이미지 생성 시 어떤 메트릭인지 설명
"""


def create_cloudwatch_agent() -> Agent:
    """CloudWatch Agent 인스턴스를 생성합니다."""
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION_NAME)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[list_alarms, get_metric_widget, summarize_alarm_states]
    )


if __name__ == "__main__":
    agent = create_cloudwatch_agent()
    print("📊 CloudWatch Monitoring Agent 시작!")
    print("   (종료: quit)\n")
    
    while True:
        user_input = input("질문: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        if user_input:
            print(f"\n{agent(user_input)}\n")
