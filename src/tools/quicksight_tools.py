"""QuickSight tools for Data Analytics Agent."""
import boto3
from strands import tool
from src.config import REGION_NAME

ACCOUNT_ID = "965037532757"


@tool
def list_quicksight_dashboards() -> str:
    """QuickSight 대시보드 목록을 조회합니다.
    
    Returns:
        대시보드 목록 (이름, ID, 상태)
    """
    client = boto3.client("quicksight", region_name=REGION_NAME)
    
    try:
        response = client.list_dashboards(AwsAccountId=ACCOUNT_ID)
        dashboards = response.get("DashboardSummaryList", [])
        
        if not dashboards:
            return "등록된 대시보드가 없습니다."
        
        result = ["QuickSight 대시보드 목록", "=" * 50]
        for d in dashboards:
            name = d.get("Name", "N/A")
            dash_id = d.get("DashboardId", "N/A")
            published = d.get("PublishedVersionNumber", 0)
            result.append(f"- {name}")
            result.append(f"  ID: {dash_id}")
            result.append(f"  버전: {published}")
        
        return "\n".join(result)
    except Exception as e:
        return f"대시보드 조회 실패: {str(e)}"


@tool
def list_quicksight_datasets() -> str:
    """QuickSight 데이터셋 목록을 조회합니다.
    
    Returns:
        데이터셋 목록 (이름, ID, 타입)
    """
    client = boto3.client("quicksight", region_name=REGION_NAME)
    
    try:
        response = client.list_data_sets(AwsAccountId=ACCOUNT_ID)
        datasets = response.get("DataSetSummaries", [])
        
        if not datasets:
            return "등록된 데이터셋이 없습니다."
        
        result = ["QuickSight 데이터셋 목록", "=" * 50]
        for ds in datasets:
            name = ds.get("Name", "N/A")
            ds_id = ds.get("DataSetId", "N/A")
            import_mode = ds.get("ImportMode", "N/A")
            result.append(f"- {name}")
            result.append(f"  ID: {ds_id}")
            result.append(f"  모드: {import_mode}")
        
        return "\n".join(result)
    except Exception as e:
        return f"데이터셋 조회 실패: {str(e)}"


@tool
def get_dataset_refresh_status(dataset_id: str) -> str:
    """데이터셋의 SPICE 새로고침 상태를 확인합니다.
    
    Args:
        dataset_id: 데이터셋 ID
    
    Returns:
        최근 새로고침 상태
    """
    client = boto3.client("quicksight", region_name=REGION_NAME)
    
    try:
        response = client.list_ingestions(
            AwsAccountId=ACCOUNT_ID,
            DataSetId=dataset_id,
            MaxResults=5
        )
        ingestions = response.get("Ingestions", [])
        
        if not ingestions:
            return "새로고침 기록이 없습니다."
        
        result = [f"데이터셋 {dataset_id} 새로고침 기록", "=" * 50]
        for ing in ingestions:
            status = ing.get("IngestionStatus", "N/A")
            created = ing.get("CreatedTime", "N/A")
            rows = ing.get("RowInfo", {}).get("RowsIngested", 0)
            result.append(f"- 상태: {status}")
            result.append(f"  시간: {created}")
            result.append(f"  행 수: {rows:,}")
            result.append("")
        
        return "\n".join(result)
    except Exception as e:
        return f"새로고침 상태 조회 실패: {str(e)}"
