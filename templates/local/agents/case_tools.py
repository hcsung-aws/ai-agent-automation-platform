"""사례 기반 학습(Case-based Learning) 도구.

대화에서 해결한 문제를 사례 문서로 저장하여 KB에 축적합니다.
유사 문제 발생 시 search_project_docs가 과거 사례를 RAG로 참조합니다.

저장 우선순위: S3 (KB_S3_BUCKET 설정 시) → 로컬 파일시스템
"""
import os
import re
from datetime import datetime
from pathlib import Path
from strands import tool

KB_S3_BUCKET = os.environ.get("KB_S3_BUCKET", "")
KB_S3_PREFIX = os.environ.get("KB_S3_PREFIX", "knowledge-base")
LOCAL_KB_PATH = Path(os.environ.get("LOCAL_KB_PATH", "knowledge-base"))
CASES_PATH = LOCAL_KB_PATH / "cases"

_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client("s3", region_name="us-east-1")
    return _s3_client


def _slugify(text: str) -> str:
    """한글/영문 제목을 파일명으로 변환."""
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s]+', '-', text.strip())[:50]


def _build_case_content(title: str, problem: str, resolution: str, tags: str) -> str:
    """사례 문서 마크다운 생성."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    return f"""# {title}
- Date: {date_str}
- Tags: [{', '.join(tag_list)}]

## 문제
{problem}

## 해결
{resolution}
"""


def _make_filename(title: str) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"{date_str}-{_slugify(title)}.md"


def _save_to_s3(filename: str, content: str) -> str:
    """S3에 사례 저장."""
    s3 = _get_s3_client()
    key = f"{KB_S3_PREFIX}/cases/{filename}"
    s3.put_object(Bucket=KB_S3_BUCKET, Key=key, Body=content.encode("utf-8"))
    return f"s3://{KB_S3_BUCKET}/{key}"


def _save_to_local(filename: str, content: str) -> str:
    """로컬 파일시스템에 사례 저장."""
    CASES_PATH.mkdir(parents=True, exist_ok=True)
    filepath = CASES_PATH / filename
    counter = 1
    while filepath.exists():
        base = filename.rsplit(".", 1)[0]
        filepath = CASES_PATH / f"{base}-{counter}.md"
        counter += 1
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


@tool
def save_case(title: str, problem: str, resolution: str, tags: str = "") -> str:
    """대화에서 해결한 문제를 사례 문서로 저장합니다.

    사용자가 '사례로 저장해줘', '이 대화 기록해줘' 등 요청 시 호출합니다.
    현재 대화의 문제-해결 과정을 요약하여 KB에 축적합니다.

    Args:
        title: 사례 제목 (예: "EC2 CPU 알람 오탐 해결")
        problem: 문제 상황 설명 (사용자 질문, 증상, 원인 포함)
        resolution: 해결 과정과 결과 (분석 내용, 적용한 조치, 결과)
        tags: 쉼표로 구분된 태그 (예: "CloudWatch,알람,EC2")

    Returns:
        저장 결과 메시지
    """
    content = _build_case_content(title, problem, resolution, tags)
    filename = _make_filename(title)

    # S3 우선, 로컬 폴백
    if KB_S3_BUCKET:
        try:
            location = _save_to_s3(filename, content)
            return f"✅ 사례가 저장되었습니다: {location}"
        except Exception as e:
            print(f"⚠️ S3 저장 실패, 로컬 폴백: {e}")

    location = _save_to_local(filename, content)
    return f"✅ 사례가 저장되었습니다: {location}"
