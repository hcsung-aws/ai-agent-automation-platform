"""Monitoring Tools - CloudWatch 알람 조회 및 분석."""
from datetime import datetime, timedelta
from strands import tool

# 테스트 데이터
TEST_ALARMS = [
    {
        "AlarmName": "ToadstoneGame-HighCPU-WebServer",
        "StateValue": "ALARM",
        "StateReason": "Threshold Crossed: 1 out of the last 1 datapoints [85.2] was greater than the threshold (80.0)",
        "MetricName": "CPUUtilization",
        "Threshold": 80.0,
        "ComparisonOperator": "GreaterThanThreshold",
        "StateUpdatedTimestamp": datetime.now() - timedelta(minutes=15)
    },
    {
        "AlarmName": "ToadstoneGame-DatabaseConnections",
        "StateValue": "OK",
        "StateReason": "Threshold Crossed: 1 out of the last 1 datapoints [45.0] was not greater than the threshold (100.0)",
        "MetricName": "DatabaseConnections",
        "Threshold": 100.0,
        "ComparisonOperator": "GreaterThanThreshold",
        "StateUpdatedTimestamp": datetime.now() - timedelta(hours=2)
    },
    {
        "AlarmName": "ToadstoneGame-DiskSpace-GameServer",
        "StateValue": "INSUFFICIENT_DATA",
        "StateReason": "Insufficient Data: 1 datapoint was unknown",
        "MetricName": "DiskSpaceUtilization",
        "Threshold": 90.0,
        "ComparisonOperator": "GreaterThanThreshold",
        "StateUpdatedTimestamp": datetime.now() - timedelta(minutes=5)
    },
    {
        "AlarmName": "ToadstoneGame-ResponseTime-API",
        "StateValue": "ALARM",
        "StateReason": "Threshold Crossed: 2 out of the last 2 datapoints [1250.0, 1180.0] was greater than the threshold (1000.0)",
        "MetricName": "ResponseTime",
        "Threshold": 1000.0,
        "ComparisonOperator": "GreaterThanThreshold",
        "StateUpdatedTimestamp": datetime.now() - timedelta(minutes=8)
    }
]

TEST_ALARM_HISTORY = [
    {
        "AlarmName": "ToadstoneGame-HighCPU-WebServer",
        "Timestamp": datetime.now() - timedelta(minutes=15),
        "HistoryItemType": "StateUpdate",
        "HistorySummary": "Alarm updated from OK to ALARM",
        "HistoryData": "CPU 사용률이 80% 임계값을 초과했습니다."
    },
    {
        "AlarmName": "ToadstoneGame-ResponseTime-API",
        "Timestamp": datetime.now() - timedelta(minutes=8),
        "HistoryItemType": "StateUpdate", 
        "HistorySummary": "Alarm updated from OK to ALARM",
        "HistoryData": "API 응답시간이 1초를 초과했습니다."
    },
    {
        "AlarmName": "ToadstoneGame-DatabaseConnections",
        "Timestamp": datetime.now() - timedelta(hours=2),
        "HistoryItemType": "StateUpdate",
        "HistorySummary": "Alarm updated from ALARM to OK",
        "HistoryData": "데이터베이스 연결 수가 정상 범위로 돌아왔습니다."
    }
]


TEST_DATA_NOTICE = "⚠️ [테스트 데이터] 실제 AWS CloudWatch API 연동 전 샘플입니다.\n\n"


@tool
def get_alarm_status(state_filter: str = "ALL") -> str:
    """CloudWatch 알람 목록을 상태별로 조회합니다.
    
    Args:
        state_filter: 조회할 알람 상태 (ALL, OK, ALARM, INSUFFICIENT_DATA)
    
    Returns:
        알람 목록 및 상태 정보
    """
    filtered_alarms = TEST_ALARMS
    if state_filter != "ALL":
        filtered_alarms = [alarm for alarm in TEST_ALARMS if alarm["StateValue"] == state_filter]
    
    if not filtered_alarms:
        return TEST_DATA_NOTICE + f"상태가 '{state_filter}'인 알람이 없습니다."
    
    result = f"=== CloudWatch 알람 현황 ({state_filter}) ===\n\n"
    
    # 상태별 카운트
    status_count = {"OK": 0, "ALARM": 0, "INSUFFICIENT_DATA": 0}
    for alarm in TEST_ALARMS:
        status_count[alarm["StateValue"]] += 1
    
    result += f"전체 알람: {len(TEST_ALARMS)}개\n"
    result += f"- 정상(OK): {status_count['OK']}개\n"
    result += f"- 알람(ALARM): {status_count['ALARM']}개\n"
    result += f"- 데이터부족(INSUFFICIENT_DATA): {status_count['INSUFFICIENT_DATA']}개\n\n"
    
    # 알람 상세 정보
    for alarm in filtered_alarms:
        status_icon = "🔴" if alarm["StateValue"] == "ALARM" else "🟡" if alarm["StateValue"] == "INSUFFICIENT_DATA" else "🟢"
        result += f"{status_icon} **{alarm['AlarmName']}**\n"
        result += f"   상태: {alarm['StateValue']}\n"
        result += f"   메트릭: {alarm['MetricName']}\n"
        result += f"   임계값: {alarm['Threshold']}\n"
        result += f"   사유: {alarm['StateReason']}\n"
        result += f"   업데이트: {alarm['StateUpdatedTimestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    return TEST_DATA_NOTICE + result


@tool
def get_alarm_history(hours: int = 24) -> str:
    """최근 알람 히스토리를 조회합니다.
    
    Args:
        hours: 조회할 시간 범위 (기본: 24시간)
    
    Returns:
        알람 히스토리 정보
    """
    cutoff_time = datetime.now() - timedelta(hours=hours)
    recent_history = [h for h in TEST_ALARM_HISTORY if h["Timestamp"] >= cutoff_time]
    
    if not recent_history:
        return TEST_DATA_NOTICE + f"최근 {hours}시간 동안 알람 히스토리가 없습니다."
    
    result = f"=== 최근 {hours}시간 알람 히스토리 ===\n\n"
    
    # 시간순 정렬 (최신순)
    recent_history.sort(key=lambda x: x["Timestamp"], reverse=True)
    
    for history in recent_history:
        result += f"⏰ **{history['AlarmName']}**\n"
        result += f"   시간: {history['Timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"   변경: {history['HistorySummary']}\n"
        result += f"   상세: {history['HistoryData']}\n\n"
    
    return TEST_DATA_NOTICE + result


@tool
def analyze_alarm_issues() -> str:
    """현재 알람 상태를 분석하여 이슈를 리포팅합니다.
    
    Returns:
        알람 분석 결과 및 권장 조치사항
    """
    alarm_issues = [alarm for alarm in TEST_ALARMS if alarm["StateValue"] == "ALARM"]
    insufficient_data = [alarm for alarm in TEST_ALARMS if alarm["StateValue"] == "INSUFFICIENT_DATA"]
    
    result = "=== 알람 이슈 분석 리포트 ===\n\n"
    
    if not alarm_issues and not insufficient_data:
        result += "🟢 **현재 모든 알람이 정상 상태입니다.**\n"
        return result
    
    # 심각도별 분류
    critical_issues = []
    warning_issues = []
    
    for alarm in alarm_issues:
        if "CPU" in alarm["AlarmName"] or "ResponseTime" in alarm["AlarmName"]:
            critical_issues.append(alarm)
        else:
            warning_issues.append(alarm)
    
    # 심각한 이슈
    if critical_issues:
        result += "🔴 **긴급 대응 필요**\n"
        for alarm in critical_issues:
            result += f"- {alarm['AlarmName']}: "
            if "CPU" in alarm["AlarmName"]:
                result += "서버 CPU 사용률 과부하 → 스케일링 또는 부하 분산 검토\n"
            elif "ResponseTime" in alarm["AlarmName"]:
                result += "API 응답시간 지연 → 데이터베이스 쿼리 최적화 또는 캐시 검토\n"
        result += "\n"
    
    # 경고 이슈
    if warning_issues:
        result += "🟡 **모니터링 필요**\n"
        for alarm in warning_issues:
            result += f"- {alarm['AlarmName']}: 지속 모니터링 필요\n"
        result += "\n"
    
    # 데이터 부족 이슈
    if insufficient_data:
        result += "⚠️ **데이터 수집 이슈**\n"
        for alarm in insufficient_data:
            result += f"- {alarm['AlarmName']}: 메트릭 수집 상태 확인 필요\n"
        result += "\n"
    
    # 권장 조치사항
    result += "## 권장 조치사항\n"
    if critical_issues:
        result += "1. 긴급 이슈 우선 대응\n"
        result += "2. 시스템 리소스 확장 검토\n"
    if insufficient_data:
        result += "3. CloudWatch Agent 상태 점검\n"
    result += "4. 알람 임계값 재검토\n"
    
    return TEST_DATA_NOTICE + result