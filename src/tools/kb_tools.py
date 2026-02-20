"""Knowledge Base tools with metadata filtering and local fallback."""
import json
import os
from pathlib import Path
import boto3
from strands import tool
from src.config import REGION_NAME

# 환경변수에서 설정 로드
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")
DATA_SOURCE_ID = os.environ.get("KB_DATA_SOURCE_ID", "")
S3_BUCKET = os.environ.get("KB_S3_BUCKET", "")
S3_PREFIX = os.environ.get("KB_S3_PREFIX", "knowledge-base")
LOCAL_KB_PATH = Path(os.environ.get("LOCAL_KB_PATH", "knowledge-base"))

_client = None
_s3_client = None
_agent_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-agent-runtime", region_name=REGION_NAME)
    return _client


def _search_local(query: str, category: str = None) -> str:
    """로컬 파일 시스템에서 검색 (Bedrock KB 폴백용)."""
    if not LOCAL_KB_PATH.exists():
        return "로컬 KB 디렉토리가 없습니다."
    
    # 검색 대상 카테고리 결정
    categories = [category] if category and category != "common" else []
    categories.append("common")  # 공통은 항상 포함
    
    results = []
    keywords = [w for w in query.lower().split() if len(w) >= 2]
    
    for cat in categories:
        cat_path = LOCAL_KB_PATH / cat
        if not cat_path.exists():
            continue
        for md_file in cat_path.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            content_lower = content.lower()
            matched = sum(1 for kw in keywords if kw in content_lower)
            if matched > 0:
                snippet = content[:2000] + "..." if len(content) > 2000 else content
                results.append((matched, f"[{cat}/{md_file.name}]\n{snippet}"))
    
    results.sort(key=lambda x: x[0], reverse=True)
    return "\n\n---\n\n".join(r[1] for r in results) if results else "관련 문서를 찾지 못했습니다."


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3", region_name=REGION_NAME)
    return _s3_client


def _search_s3(query: str, category: str = None) -> str:
    """S3 버킷에서 .md 파일을 검색 (Bedrock KB 없이 S3 직접 검색)."""
    if not S3_BUCKET:
        return ""
    
    try:
        s3 = _get_s3_client()
        
        # 검색 대상 카테고리 결정
        categories = [category] if category and category != "common" else []
        categories.append("common")
        
        results = []
        keywords = [w for w in query.lower().split() if len(w) >= 2]
        
        for cat in categories:
            prefix = f"{S3_PREFIX}/{cat}/"
            response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
            
            for obj in response.get("Contents", []):
                key = obj["Key"]
                if not key.endswith(".md"):
                    continue
                
                file_obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
                content = file_obj["Body"].read().decode("utf-8")
                content_lower = content.lower()
                
                matched = sum(1 for kw in keywords if kw in content_lower)
                if matched > 0:
                    snippet = content[:2000] + "..." if len(content) > 2000 else content
                    filename = key.split("/")[-1]
                    results.append((matched, f"[{cat}/{filename}]\n{snippet}"))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return "\n\n---\n\n".join(r[1] for r in results) if results else ""
    except Exception as e:
        print(f"⚠️ S3 검색 실패: {e}")
        return ""


def _get_agent_client():
    global _agent_client
    if _agent_client is None:
        _agent_client = boto3.client("bedrock-agent", region_name=REGION_NAME)
    return _agent_client


def _search_kb(query: str, category: str = None) -> str:
    """내부 검색 함수 - Bedrock KB → S3 → 로컬 순서로 폴백."""
    # 1. Bedrock KB (설정된 경우)
    if KNOWLEDGE_BASE_ID:
        try:
            client = _get_client()
            
            retrieval_config = {
                "vectorSearchConfiguration": {
                    "numberOfResults": 5
                }
            }
            
            # 카테고리 필터 적용
            if category:
                if category == "common":
                    retrieval_config["vectorSearchConfiguration"]["filter"] = {
                        "equals": {"key": "category", "value": "common"}
                    }
                else:
                    retrieval_config["vectorSearchConfiguration"]["filter"] = {
                        "orAll": [
                            {"equals": {"key": "category", "value": "common"}},
                            {"equals": {"key": "category", "value": category}}
                        ]
                    }
            
            response = client.retrieve(
                knowledgeBaseId=KNOWLEDGE_BASE_ID,
                retrievalQuery={"text": query},
                retrievalConfiguration=retrieval_config
            )
            
            results = []
            for i, result in enumerate(response.get("retrievalResults", []), 1):
                content = result.get("content", {}).get("text", "")
                score = result.get("score", 0)
                metadata = result.get("metadata", {})
                cat = metadata.get("category", "unknown")
                
                if score > 0.3:
                    if len(content) > 2000:
                        content = content[:2000] + "..."
                    results.append(f"[결과 {i}] (관련도: {score:.2f}, 카테고리: {cat})\n{content}")
            
            if results:
                return "\n\n---\n\n".join(results)
        except Exception as e:
            print(f"⚠️ Bedrock KB 접근 실패: {e}")
    
    # 2. S3 직접 검색 (Bedrock KB 없이)
    if S3_BUCKET:
        s3_result = _search_s3(query, category)
        if s3_result:
            return s3_result
    
    # 3. 로컬 파일 검색
    return _search_local(query, category)


@tool
def search_common_knowledge(query: str) -> str:
    """공통 지식 베이스에서 검색합니다.
    
    조직 정보, 프로젝트 개요, 용어집, 에스컬레이션 정책 등
    모든 Agent가 알아야 할 공통 지식을 검색합니다.
    
    Args:
        query: 검색할 내용
    
    Returns:
        관련 공통 지식 내용
    """
    return _search_kb(query, category="common")


@tool
def search_devops_knowledge(query: str) -> str:
    """DevOps 지식 베이스에서 검색합니다.
    
    운영 매뉴얼, 장애 대응 가이드, 인프라 문서 등을 검색합니다.
    공통 지식도 함께 검색됩니다.
    
    Args:
        query: 검색할 내용 (예: "Kinesis 샤드 용량 초과", "장애 대응 절차")
    
    Returns:
        관련 DevOps 가이드 내용
    """
    return _search_kb(query, category="devops")


@tool
def search_analytics_knowledge(query: str) -> str:
    """Analytics 지식 베이스에서 검색합니다.
    
    데이터 분석 가이드, Athena 쿼리 패턴, 지표 정의 등을 검색합니다.
    공통 지식도 함께 검색됩니다.
    
    Args:
        query: 검색할 내용
    
    Returns:
        관련 Analytics 가이드 내용
    """
    return _search_kb(query, category="analytics")


@tool
def search_monitoring_knowledge(query: str) -> str:
    """Monitoring 지식 베이스에서 검색합니다.
    
    알람 설정 가이드, 모니터링 정책, 임계값 기준 등을 검색합니다.
    공통 지식도 함께 검색됩니다.
    
    Args:
        query: 검색할 내용
    
    Returns:
        관련 Monitoring 가이드 내용
    """
    return _search_kb(query, category="monitoring")


# 기존 호환성 유지
@tool
def search_operations_guide(query: str) -> str:
    """운영 매뉴얼 및 장애 대응 가이드에서 정보를 검색합니다.
    
    (기존 호환성 유지 - search_devops_knowledge와 동일)
    
    Args:
        query: 검색할 내용
    
    Returns:
        관련 운영 가이드 내용
    """
    return _search_kb(query, category="devops")


# ============================================
# KB 쓰기 도구 (v1.3 자동 개선용)
# ============================================

@tool
def add_kb_document(category: str, filename: str, content: str, doc_type: str = "guide") -> str:
    """Knowledge Base에 새 문서를 추가합니다.
    
    Args:
        category: 문서 카테고리 (common, devops, analytics, monitoring)
        filename: 파일명 (예: "new-guide.md")
        content: 문서 내용 (마크다운 형식)
        doc_type: 문서 유형 (guide, policy, faq 등)
    
    Returns:
        업로드 결과
    """
    if category not in ["common", "devops", "analytics", "monitoring"]:
        return f"오류: 유효하지 않은 카테고리입니다. (common, devops, analytics, monitoring 중 선택)"
    
    if not filename.endswith(".md"):
        filename = f"{filename}.md"
    
    results = []
    
    # 로컬 저장 (항상)
    local_dir = LOCAL_KB_PATH / category
    local_dir.mkdir(parents=True, exist_ok=True)
    local_file = local_dir / filename
    local_file.write_text(content, encoding="utf-8")
    results.append(f"✅ 로컬 저장: {local_file}")
    
    # S3 업로드 (설정된 경우만)
    if S3_BUCKET:
        try:
            s3 = _get_s3_client()
            doc_key = f"{S3_PREFIX}/{category}/{filename}"
            s3.put_object(Bucket=S3_BUCKET, Key=doc_key, Body=content.encode("utf-8"))
            
            metadata = {"metadataAttributes": {"category": category, "doc_type": doc_type}}
            meta_key = f"{doc_key}.metadata.json"
            s3.put_object(Bucket=S3_BUCKET, Key=meta_key, Body=json.dumps(metadata).encode("utf-8"))
            results.append(f"✅ S3 업로드: s3://{S3_BUCKET}/{doc_key}")
            results.append("\n💡 KB에 반영하려면 trigger_kb_sync()를 호출하세요.")
        except Exception as e:
            results.append(f"⚠️ S3 업로드 실패 (로컬만 저장됨): {e}")
    
    return "\n".join(results)


@tool
def trigger_kb_sync() -> str:
    """Knowledge Base 동기화를 실행합니다.
    
    S3에 업로드된 새 문서를 Bedrock KB에 인덱싱합니다.
    
    Returns:
        동기화 작업 상태
    """
    if not KNOWLEDGE_BASE_ID or not DATA_SOURCE_ID:
        return "⚠️ KB 동기화 불가: KNOWLEDGE_BASE_ID 또는 KB_DATA_SOURCE_ID가 설정되지 않았습니다."
    
    client = _get_agent_client()
    
    response = client.start_ingestion_job(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        dataSourceId=DATA_SOURCE_ID,
    )
    
    job = response.get("ingestionJob", {})
    job_id = job.get("ingestionJobId", "unknown")
    status = job.get("status", "unknown")
    
    return f"✅ KB Sync 시작됨\n- Job ID: {job_id}\n- 상태: {status}\n\n💡 인덱싱에 30초~1분 소요됩니다."
