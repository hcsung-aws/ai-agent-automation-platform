# Monitoring 도메인 가이드

## 개요
CloudWatch 알람 모니터링 및 이슈 리포팅 가이드입니다.

## 주요 모니터링 영역

### 1. CloudWatch 알람 현황
- ALARM 상태 알람 즉시 확인
- INSUFFICIENT_DATA 알람 원인 파악
- 알람 히스토리 추적

### 2. 알람 추이 분석
- 반복 발생 알람 패턴 식별
- 시간대별 알람 빈도 분석
- 근본 원인 추적

### 3. 이슈 리포팅
- 알람 분석 결과 문서화
- 권장 조치사항 제시
- 에스컬레이션 판단

## 모니터링 도구

| 도구 | 용도 |
|------|------|
| get_alarm_status | 알람 현황 조회 |
| analyze_alarm_trend | 알람 추이 분석 |
| create_issue_report | 이슈 리포트 생성 |

## 알람 심각도 분류

| 심각도 | 기준 | 대응 시간 |
|--------|------|----------|
| Critical | 서비스 중단 | 15분 이내 |
| High | 성능 저하 | 1시간 이내 |
| Medium | 잠재적 문제 | 4시간 이내 |
| Low | 정보성 | 다음 영업일 |

## 에스컬레이션 기준
- Critical 알람: 즉시 에스컬레이션
- 동일 알람 3회 반복: 근본 원인 분석 요청
- 30분 이상 미해결: 상위 레벨 에스컬레이션

## 관련 문서
- 에스컬레이션 정책: common/escalation-policy.md
- 트러블슈팅: devops/game-log-analytics-troubleshooting.md
