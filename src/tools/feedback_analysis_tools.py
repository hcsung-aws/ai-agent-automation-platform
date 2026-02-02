"""Feedback analysis tools for auto-improvement suggestions."""
from strands import tool
from src.utils.execution_logger import get_feedback


@tool
def analyze_negative_feedback(limit: int = 20) -> str:
    """부정 피드백(👎)을 조회하여 분석용 데이터를 반환합니다.
    
    수집된 부정 피드백에서 공통 패턴을 찾고 개선 방안을 제안하는 데 사용합니다.
    
    Args:
        limit: 조회할 피드백 수 (기본 20건)
    
    Returns:
        분석용 피드백 데이터 (user_input, agent_response, comment 포함)
    """
    feedback = get_feedback(limit=limit, rating_filter="negative")
    
    if not feedback:
        return "부정 피드백이 없습니다. 아직 개선이 필요한 패턴이 발견되지 않았습니다."
    
    result = f"## 부정 피드백 분석 ({len(feedback)}건)\n\n"
    
    for i, f in enumerate(feedback, 1):
        result += f"### 케이스 {i}\n"
        result += f"- **사용자 질문**: {f.get('user_input', 'N/A')}\n"
        result += f"- **Agent 응답**: {f.get('agent_response', 'N/A')[:500]}...\n"
        if f.get('comment'):
            result += f"- **사용자 코멘트**: {f.get('comment')}\n"
        result += f"- **시간**: {f.get('timestamp', '')[:19]}\n\n"
    
    result += """---
## 분석 요청
위 피드백을 분석하여 다음을 제안해주세요:
1. **공통 실패 패턴**: 어떤 유형의 질문에서 실패가 발생하는가?
2. **KB 문서 제안**: 어떤 가이드 문서를 추가하면 좋을까?
3. **System Prompt 개선**: 어떤 지침을 추가/수정하면 좋을까?
"""
    
    return result
