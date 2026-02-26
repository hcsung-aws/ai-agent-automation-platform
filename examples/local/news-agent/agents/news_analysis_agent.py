"""News Analysis Agent - 저장된 뉴스 데이터 분석."""
import json

from strands import Agent, tool
from strands.models import BedrockModel
from config import MODEL_ID, REGION_NAME
from news_store import load_news, list_dates


@tool
def list_available_dates() -> str:
    """분석 가능한 날짜 목록을 조회합니다.

    Returns:
        날짜별 기사 수 목록
    """
    dates = list_dates()
    if not dates:
        return "저장된 뉴스가 없습니다. 먼저 뉴스 크롤링 Agent로 뉴스를 수집하세요."
    lines = [f"• {d['date']} — {d['count']}건" for d in dates]
    return "\n".join(lines)


@tool
def load_news_data(date_str: str) -> str:
    """특정 날짜의 뉴스 데이터를 분석용으로 로드합니다.

    Args:
        date_str: 날짜 (YYYY-MM-DD 형식)

    Returns:
        JSON 형태의 뉴스 데이터
    """
    articles = load_news(date_str)
    if articles is None:
        return f"{date_str}에 저장된 뉴스가 없습니다."
    return json.dumps(articles, ensure_ascii=False)


SYSTEM_PROMPT = """당신은 뉴스 분석 전문 Agent입니다.

## 역할
news-data/ 디렉토리에 저장된 뉴스 데이터를 분석하여 인사이트를 제공합니다.

## 도구 사용 지침
- 분석 가능한 날짜 확인 시 → list_available_dates 호출
- 특정 날짜 뉴스 분석 시 → load_news_data 호출 후 분석 수행
- 여러 날짜 비교 시 → load_news_data를 날짜별로 각각 호출

## 분석 역량
- 주요 트렌드 및 핫 토픽 도출
- 소스별 보도 비중 분석
- 키워드 빈도 분석
- 날짜 간 뉴스 흐름 비교

## 응답 원칙
- 한국어로 응답
- 데이터 기반의 구체적 분석 결과 제공
- 수치와 근거를 포함하여 설명
"""


def create_news_analysis_agent() -> Agent:
    """News Analysis Agent 인스턴스를 생성합니다."""
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION_NAME)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[list_available_dates, load_news_data],
    )
