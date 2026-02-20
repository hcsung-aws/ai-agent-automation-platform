"""Athena tools for Data Analytics Agent."""
import boto3
import time
from strands import tool
from src.config import REGION_NAME

ATHENA_DATABASE = "game_logs"
ATHENA_OUTPUT = "s3://devops-agent-kb-965037532757/athena-results/"


@tool
def run_athena_query(query: str, database: str = ATHENA_DATABASE) -> str:
    """Athena SQL 쿼리를 실행하고 결과를 반환합니다.
    
    Args:
        query: 실행할 SQL 쿼리
        database: 데이터베이스 이름 (기본: game_logs)
    
    Returns:
        쿼리 결과 (최대 100행)
    """
    client = boto3.client("athena", region_name=REGION_NAME)
    
    # 쿼리 실행
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT}
    )
    query_id = response["QueryExecutionId"]
    
    # 완료 대기 (최대 60초)
    for _ in range(30):
        status = client.get_query_execution(QueryExecutionId=query_id)
        state = status["QueryExecution"]["Status"]["State"]
        
        if state == "SUCCEEDED":
            break
        elif state in ["FAILED", "CANCELLED"]:
            reason = status["QueryExecution"]["Status"].get("StateChangeReason", "Unknown")
            return f"쿼리 실패: {reason}"
        time.sleep(2)
    else:
        return "쿼리 타임아웃 (60초 초과)"
    
    # 결과 조회
    results = client.get_query_results(QueryExecutionId=query_id, MaxResults=100)
    
    rows = results["ResultSet"]["Rows"]
    if not rows:
        return "결과 없음"
    
    # 헤더
    headers = [col.get("VarCharValue", "") for col in rows[0]["Data"]]
    
    # 데이터
    output = [" | ".join(headers), "-" * 50]
    for row in rows[1:]:
        values = [col.get("VarCharValue", "") for col in row["Data"]]
        output.append(" | ".join(values))
    
    return "\n".join(output)


@tool
def list_athena_tables(database: str = ATHENA_DATABASE) -> str:
    """Athena 데이터베이스의 테이블 목록을 조회합니다.
    
    Args:
        database: 데이터베이스 이름 (기본: game_logs)
    
    Returns:
        테이블 목록
    """
    client = boto3.client("glue", region_name=REGION_NAME)
    
    try:
        response = client.get_tables(DatabaseName=database)
        tables = response.get("TableList", [])
        
        if not tables:
            return f"데이터베이스 '{database}'에 테이블이 없습니다."
        
        result = [f"데이터베이스: {database}", "=" * 40]
        for table in tables:
            name = table["Name"]
            cols = len(table.get("StorageDescriptor", {}).get("Columns", []))
            result.append(f"- {name} ({cols} columns)")
        
        return "\n".join(result)
    except client.exceptions.EntityNotFoundException:
        return f"데이터베이스 '{database}'를 찾을 수 없습니다."


@tool
def get_table_schema(table_name: str, database: str = ATHENA_DATABASE) -> str:
    """테이블의 스키마(컬럼 정보)를 조회합니다.
    
    Args:
        table_name: 테이블 이름
        database: 데이터베이스 이름 (기본: game_logs)
    
    Returns:
        테이블 스키마 정보
    """
    client = boto3.client("glue", region_name=REGION_NAME)
    
    try:
        response = client.get_table(DatabaseName=database, Name=table_name)
        table = response["Table"]
        
        columns = table.get("StorageDescriptor", {}).get("Columns", [])
        partitions = table.get("PartitionKeys", [])
        
        result = [f"테이블: {database}.{table_name}", "=" * 50, "", "컬럼:"]
        for col in columns:
            result.append(f"  - {col['Name']}: {col['Type']}")
        
        if partitions:
            result.append("\n파티션 키:")
            for p in partitions:
                result.append(f"  - {p['Name']}: {p['Type']}")
        
        return "\n".join(result)
    except client.exceptions.EntityNotFoundException:
        return f"테이블 '{database}.{table_name}'을 찾을 수 없습니다."
