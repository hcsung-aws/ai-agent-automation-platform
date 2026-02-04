"""Data Analytics Agent - Strands Agent for game analytics."""
from strands import Agent
from strands.models import BedrockModel

from src.tools.athena_tools import run_athena_query, list_athena_tables, get_table_schema
from src.tools.quicksight_tools import list_quicksight_dashboards, list_quicksight_datasets, get_dataset_refresh_status
from src.tools.kb_tools import search_analytics_knowledge
from src.tools.mmorpg_analytics import (
    analyze_gacha_rates,
    analyze_currency_flow,
    analyze_user_retention,
    analyze_quest_completion,
    analyze_level_distribution,
    analyze_attendance,
)

SYSTEM_PROMPT = """당신은 MMORPG 게임 데이터 분석 전문가 AI 에이전트입니다.

## Athena 테이블 (game_logs 데이터베이스)

### 분석용 테이블
1. **accounts** - 계정 스냅샷 (dt 파티션)
   - account_uid, channel_type, channel_id, create_date, login_date, logout_date

2. **characters** - 캐릭터 스냅샷 (dt 파티션)
   - char_uid, account_uid, char_name, char_type, level, exp, gold, login_date

3. **hero_gacha** - 영웅 뽑기 로그 (dt 파티션)
   - gacha_id, char_uid, hero_tid, grade, gacha_type, cost_currency, cost_amount, gacha_time

4. **currency_logs** - 재화 변동 로그 (dt 파티션)
   - log_id, char_uid, currency_tid, change_type, change_reason, before_value, delta_value, after_value

5. **quest_logs** - 퀘스트 활동 로그 (dt 파티션)
   - log_id, char_uid, quest_tid, category1, category2, action (start/progress/complete)

6. **attendance_logs** - 출석 로그 (dt 파티션)
   - char_uid, attend_date, reward_gold, consecutive_days

## 전용 분석 도구

### 가챠 분석
- `analyze_gacha_rates(date)`: 등급별 확률, 뽑기 횟수, 평균 비용

### 재화 분석
- `analyze_currency_flow(currency_tid, date)`: 획득/소비 흐름, 주요 사유
  - currency_tid: 1=골드, 2=다이아, 3=스태미나, 4=기타

### 유저 분석
- `analyze_user_retention(date)`: DAU, 신규 유저, 평균 레벨
- `analyze_level_distribution(date)`: 레벨 구간별 분포

### 콘텐츠 분석
- `analyze_quest_completion(category1, date)`: 퀘스트 완료율
- `analyze_attendance(date)`: 출석 현황, 연속 출석 분포

## Knowledge Base 활용
- 분석 방법, 절차, 가이드, 정책 관련 질문 시 먼저 search_analytics_knowledge() 호출
- KB 검색 결과를 참고하여 답변 구성

## 응답 원칙
- 한국어로 응답
- 방법/절차 질문 → KB 검색 우선
- 데이터 분석 요청 → 전용 도구 사용, 복잡한 분석은 run_athena_query 사용
- 결과에 대한 해석과 인사이트 제공
- 이상 징후 발견 시 알림
"""


def create_analytics_agent() -> Agent:
    """Create and return Data Analytics Agent instance."""
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
    )
    
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            # Athena 기본 도구
            run_athena_query,
            list_athena_tables,
            get_table_schema,
            # MMORPG 분석 도구
            analyze_gacha_rates,
            analyze_currency_flow,
            analyze_user_retention,
            analyze_quest_completion,
            analyze_level_distribution,
            analyze_attendance,
            # QuickSight 도구
            list_quicksight_dashboards,
            list_quicksight_datasets,
            get_dataset_refresh_status,
            # KB 도구
            search_analytics_knowledge,
        ],
    )
    
    return agent


if __name__ == "__main__":
    agent = create_analytics_agent()
    
    print("Data Analytics Agent 시작. 'quit'으로 종료.")
    print("-" * 50)
    
    while True:
        user_input = input("\n사용자: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        if not user_input:
            continue
        
        response = agent(user_input)
        print(f"\nAgent: {response}")
