"""뉴스 데이터 저장소 — 환경변수로 S3/로컬 자동 전환.

NEWS_S3_BUCKET 설정 시 → S3 (prefix: news-data/)
미설정 시 → 로컬 파일시스템 (news-data/)
"""
import json
import os
from pathlib import Path

_S3_BUCKET = os.environ.get("NEWS_S3_BUCKET", "")
_S3_PREFIX = "news-data/"
_LOCAL_DIR = Path("news-data")

_s3 = None


def _get_s3():
    global _s3
    if _s3 is None:
        import boto3
        _s3 = boto3.client("s3", region_name=os.environ.get("BEDROCK_REGION", "us-east-1"))
    return _s3


def save_news(date_str: str, articles: list[dict]) -> None:
    """뉴스 데이터를 저장합니다. 기존 데이터가 있으면 병합."""
    existing = load_news(date_str) or []
    existing_links = {a["link"] for a in existing}
    merged = existing + [a for a in articles if a["link"] not in existing_links]
    body = json.dumps(merged, ensure_ascii=False, indent=2)

    if _S3_BUCKET:
        _get_s3().put_object(
            Bucket=_S3_BUCKET, Key=f"{_S3_PREFIX}{date_str}.json",
            Body=body, ContentType="application/json",
        )
    else:
        _LOCAL_DIR.mkdir(exist_ok=True)
        (_LOCAL_DIR / f"{date_str}.json").write_text(body, "utf-8")


def load_news(date_str: str) -> list[dict] | None:
    """특정 날짜의 뉴스 데이터를 로드합니다. 없으면 None."""
    if _S3_BUCKET:
        try:
            resp = _get_s3().get_object(Bucket=_S3_BUCKET, Key=f"{_S3_PREFIX}{date_str}.json")
            return json.loads(resp["Body"].read())
        except _get_s3().exceptions.NoSuchKey:
            return None
    else:
        path = _LOCAL_DIR / f"{date_str}.json"
        return json.loads(path.read_text("utf-8")) if path.exists() else None


def list_dates() -> list[dict]:
    """저장된 날짜 목록을 반환합니다. [{date_str, count}, ...]"""
    if _S3_BUCKET:
        resp = _get_s3().list_objects_v2(Bucket=_S3_BUCKET, Prefix=_S3_PREFIX)
        results = []
        for obj in resp.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".json"):
                date_str = key[len(_S3_PREFIX):-5]  # "news-data/2026-02-24.json" → "2026-02-24"
                data = load_news(date_str)
                results.append({"date": date_str, "count": len(data) if data else 0})
        return sorted(results, key=lambda x: x["date"], reverse=True)
    else:
        if not _LOCAL_DIR.exists():
            return []
        results = []
        for f in sorted(_LOCAL_DIR.glob("*.json"), reverse=True):
            articles = json.loads(f.read_text("utf-8"))
            results.append({"date": f.stem, "count": len(articles)})
        return results
