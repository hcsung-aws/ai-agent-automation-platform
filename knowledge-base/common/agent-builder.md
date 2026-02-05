# Agent Builder 사용법

## 실행 방법

```bash
kiro chat --agent agent-builder
```

## 자연어로 요청

예시:
- "CloudWatch 알람을 조회하는 Monitoring Agent 만들어줘"
- "HR Agent 만들어줘. 휴가 조회 기능으로"
- "서버 상태 체크하는 Agent 생성해줘"

## 동작 과정

1. Agent Builder가 요청 분석
2. 코드 자동 생성 (`agents/` 디렉토리)
3. Supervisor에 자동 연결
4. 테스트 방법 안내

## 개선 요청

생성된 Agent에 피드백:
- "이 기능 추가해줘"
- "응답 형식 바꿔줘"
- "에러 처리 추가해줘"
