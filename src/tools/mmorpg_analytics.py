"""MMORPG-specific analytics tools for Data Analytics Agent."""
import boto3
import time
from strands import tool

ATHENA_DATABASE = "game_logs"
ATHENA_OUTPUT = "s3://devops-agent-kb-965037532757/athena-results/"


def _run_query(query: str) -> str:
    """Execute Athena query and return results."""
    client = boto3.client("athena", region_name="us-east-1")
    
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": ATHENA_DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT}
    )
    query_id = response["QueryExecutionId"]
    
    for _ in range(30):
        status = client.get_query_execution(QueryExecutionId=query_id)
        state = status["QueryExecution"]["Status"]["State"]
        if state == "SUCCEEDED":
            break
        elif state in ["FAILED", "CANCELLED"]:
            return f"쿼리 실패: {status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')}"
        time.sleep(2)
    else:
        return "쿼리 타임아웃"
    
    results = client.get_query_results(QueryExecutionId=query_id, MaxResults=100)
    rows = results["ResultSet"]["Rows"]
    if not rows:
        return "결과 없음"
    
    headers = [col.get("VarCharValue", "") for col in rows[0]["Data"]]
    output = [" | ".join(headers), "-" * 60]
    for row in rows[1:]:
        values = [col.get("VarCharValue", "") for col in row["Data"]]
        output.append(" | ".join(values))
    return "\n".join(output)


@tool
def analyze_gacha_rates(date: str = None) -> str:
    """가챠(뽑기) 등급별 확률과 통계를 분석합니다.
    
    Args:
        date: 분석할 날짜 (YYYY-MM-DD, 기본: 전체)
    
    Returns:
        등급별 뽑기 횟수, 확률, 평균 비용
    """
    where = f"WHERE dt = '{date}'" if date else ""
    query = f"""
    SELECT 
        grade,
        COUNT(*) as pull_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as rate_pct,
        ROUND(AVG(cost_amount), 0) as avg_cost
    FROM hero_gacha
    {where}
    GROUP BY grade
    ORDER BY grade
    """
    return _run_query(query)


@tool
def analyze_currency_flow(currency_tid: int = None, date: str = None) -> str:
    """재화 획득/소비 흐름을 분석합니다.
    
    Args:
        currency_tid: 재화 종류 (1=골드, 2=다이아, 3=스태미나, 4=기타)
        date: 분석할 날짜 (YYYY-MM-DD)
    
    Returns:
        재화별 획득/소비량, 주요 사유
    """
    conditions = []
    if currency_tid:
        conditions.append(f"currency_tid = {currency_tid}")
    if date:
        conditions.append(f"dt = '{date}'")
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    query = f"""
    SELECT 
        currency_tid,
        change_type,
        change_reason,
        COUNT(*) as tx_count,
        SUM(ABS(delta_value)) as total_amount
    FROM currency_logs
    {where}
    GROUP BY currency_tid, change_type, change_reason
    ORDER BY currency_tid, change_type, total_amount DESC
    """
    return _run_query(query)


@tool
def analyze_user_retention(date: str) -> str:
    """일별 유저 리텐션(DAU, 신규, 복귀)을 분석합니다.
    
    Args:
        date: 분석할 날짜 (YYYY-MM-DD, 필수)
    
    Returns:
        DAU, 신규 유저, 복귀 유저 수
    """
    query = f"""
    SELECT 
        '{date}' as date,
        COUNT(DISTINCT char_uid) as dau,
        COUNT(DISTINCT CASE WHEN DATE(create_date) = DATE('{date}') THEN account_uid END) as new_users,
        AVG(level) as avg_level
    FROM characters
    WHERE dt = '{date}'
    """
    return _run_query(query)


@tool
def analyze_quest_completion(category1: int = None, date: str = None) -> str:
    """퀘스트 완료율을 분석합니다.
    
    Args:
        category1: 퀘스트 카테고리 (선택)
        date: 분석할 날짜 (YYYY-MM-DD)
    
    Returns:
        퀘스트별 시작/진행/완료 수
    """
    conditions = []
    if category1:
        conditions.append(f"category1 = {category1}")
    if date:
        conditions.append(f"dt = '{date}'")
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    query = f"""
    SELECT 
        category1,
        action,
        COUNT(*) as count,
        COUNT(DISTINCT char_uid) as unique_users
    FROM quest_logs
    {where}
    GROUP BY category1, action
    ORDER BY category1, action
    """
    return _run_query(query)


@tool
def analyze_level_distribution(date: str = None) -> str:
    """캐릭터 레벨 분포를 분석합니다.
    
    Args:
        date: 분석할 날짜 (YYYY-MM-DD)
    
    Returns:
        레벨 구간별 유저 수
    """
    where = f"WHERE dt = '{date}'" if date else ""
    query = f"""
    SELECT 
        CASE 
            WHEN level BETWEEN 1 AND 10 THEN '1-10'
            WHEN level BETWEEN 11 AND 30 THEN '11-30'
            WHEN level BETWEEN 31 AND 50 THEN '31-50'
            WHEN level BETWEEN 51 AND 70 THEN '51-70'
            WHEN level BETWEEN 71 AND 90 THEN '71-90'
            ELSE '91-100'
        END as level_range,
        COUNT(*) as user_count,
        ROUND(AVG(gold), 0) as avg_gold
    FROM characters
    {where}
    GROUP BY 1
    ORDER BY 1
    """
    return _run_query(query)


@tool
def analyze_attendance(date: str = None) -> str:
    """출석 현황을 분석합니다.
    
    Args:
        date: 분석할 날짜 (YYYY-MM-DD)
    
    Returns:
        출석 유저 수, 연속 출석 분포
    """
    where = f"WHERE dt = '{date}'" if date else ""
    query = f"""
    SELECT 
        COUNT(*) as total_attendance,
        SUM(reward_gold) as total_reward,
        ROUND(AVG(consecutive_days), 1) as avg_consecutive,
        MAX(consecutive_days) as max_consecutive
    FROM attendance_logs
    {where}
    """
    return _run_query(query)
