"""News Agent - RSS 기반 뉴스 크롤링, 날짜별 저장 및 조회."""
import json
from datetime import date
from pathlib import Path

import feedparser
from strands import Agent, tool
from strands.models import BedrockModel
from config import MODEL_ID, REGION_NAME

RSS_FEEDS = {
    "연합뉴스": "https://www.yonhapnewstv.co.kr/browse/feed/",
    "Google News": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
    "TechCrunch": "https://techcrunch.com/feed/",
    "AWS News": "https://aws.amazon.com/blogs/aws/feed/",
}

NEWS_DIR = Path("news-data")


def _save_news(date_str: str, articles: list[dict]) -> None:
    """뉴스 데이터를 JSON 파일로 저장합니다."""
    NEWS_DIR.mkdir(exist_ok=True)
    path = NEWS_DIR / f"{date_str}.json"
    # 기존 파일이 있으면 병합
    existing = json.loads(path.read_text("utf-8")) if path.exists() else []
    existing_links = {a["link"] for a in existing}
    merged = existing + [a for a in articles if a["link"] not in existing_links]
    path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), "utf-8")


def _load_news(date_str: str) -> list[dict] | None:
    """저장된 뉴스 데이터를 로드합니다. 없으면 None."""
    path = NEWS_DIR / f"{date_str}.json"
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return None


def _format_articles(articles: list[dict]) -> str:
    """기사 목록을 문자열로 포맷합니다."""
    return "\n\n".join(
        f"[{a['source']}] {a['title']}\n  링크: {a['link']}\n  요약: {a['summary']}"
        for a in articles
    ) if articles else "뉴스가 없습니다."


@tool
def fetch_news(source: str = "", max_items: int = 5) -> str:
    """RSS 피드에서 최신 뉴스를 가져와 오늘 날짜로 저장합니다.

    이미 오늘 저장된 뉴스가 있으면 크롤링하지 않고 저장된 결과를 반환합니다.

    Args:
        source: 뉴스 소스 이름 (비어있으면 전체). 가능한 값: 연합뉴스, Google News, TechCrunch, AWS News
        max_items: 가져올 뉴스 수 (기본 5)

    Returns:
        뉴스 목록 (제목, 링크, 요약)
    """
    today = date.today().isoformat()

    # 캐시 확인
    cached = _load_news(today)
    if cached:
        if source:
            cached = [a for a in cached if a["source"] == source]
        return f"[저장된 뉴스 - {today}]\n\n" + _format_articles(cached)

    # RSS 크롤링
    feeds = {source: RSS_FEEDS[source]} if source in RSS_FEEDS else RSS_FEEDS
    articles = []
    for name, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_items]:
                articles.append({
                    "source": name,
                    "title": entry.get("title", "N/A"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:200],
                    "published": entry.get("published", ""),
                })
        except Exception as e:
            articles.append({"source": name, "title": f"피드 로드 실패: {e}", "link": "", "summary": "", "published": ""})

    _save_news(today, articles)
    return f"[크롤링 완료 - {today}에 저장됨]\n\n" + _format_articles(articles)


@tool
def search_news(keyword: str, max_items: int = 5) -> str:
    """키워드로 Google News를 검색합니다.

    Args:
        keyword: 검색할 키워드
        max_items: 가져올 뉴스 수 (기본 5)

    Returns:
        검색된 뉴스 목록
    """
    import urllib.parse

    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:max_items]:
        articles.append({
            "source": "Google News",
            "title": entry.get("title", "N/A"),
            "link": entry.get("link", ""),
            "summary": "",
            "published": entry.get("published", ""),
        })

    # 검색 결과도 오늘 날짜로 저장
    if articles:
        _save_news(date.today().isoformat(), articles)

    return _format_articles(articles) if articles else f"'{keyword}' 관련 뉴스를 찾지 못했습니다."


@tool
def list_saved_news() -> str:
    """저장된 뉴스 파일 목록을 조회합니다.

    Returns:
        날짜별 저장된 뉴스 파일 목록과 기사 수
    """
    if not NEWS_DIR.exists():
        return "저장된 뉴스가 없습니다. fetch_news로 먼저 뉴스를 수집하세요."

    files = sorted(NEWS_DIR.glob("*.json"), reverse=True)
    if not files:
        return "저장된 뉴스가 없습니다."

    lines = []
    for f in files:
        articles = json.loads(f.read_text("utf-8"))
        lines.append(f"• {f.stem} — {len(articles)}건")
    return "📁 저장된 뉴스 목록:\n" + "\n".join(lines)


@tool
def load_news_by_date(date_str: str) -> str:
    """특정 날짜에 저장된 뉴스를 조회합니다.

    Args:
        date_str: 조회할 날짜 (YYYY-MM-DD 형식)

    Returns:
        해당 날짜의 뉴스 목록
    """
    articles = _load_news(date_str)
    if articles is None:
        return f"{date_str}에 저장된 뉴스가 없습니다."
    return f"📰 {date_str} 뉴스 ({len(articles)}건):\n\n" + _format_articles(articles)


SYSTEM_PROMPT = """당신은 뉴스 크롤링 전문 Agent입니다.

## 역할
RSS 피드를 통해 최신 뉴스를 수집하고, 날짜별로 저장/조회합니다.

## 도구 사용 지침
- 최신 뉴스 요청 시 → fetch_news 호출 (오늘 이미 저장된 뉴스가 있으면 캐시 반환)
- 특정 주제/키워드 뉴스 요청 시 → search_news 호출
- 저장된 뉴스 목록 확인 시 → list_saved_news 호출
- 특정 날짜 뉴스 조회 시 → load_news_by_date 호출 (YYYY-MM-DD 형식)

## 사용 가능한 뉴스 소스
- 연합뉴스, Google News, TechCrunch, AWS News

## 응답 원칙
- 한국어로 응답
- 뉴스 제목, 핵심 내용, 출처 링크를 포함
- 여러 뉴스를 가져온 경우 주요 트렌드를 요약
- 도구가 반환하는 URL/링크를 마크다운 [제목](URL) 형식으로 응답에 반드시 포함 (생략 금지)
"""


def create_news_agent() -> Agent:
    """News Agent 인스턴스를 생성합니다."""
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION_NAME)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[fetch_news, search_news, list_saved_news, load_news_by_date],
    )
