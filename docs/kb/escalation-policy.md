# 에스컬레이션 정책

## 개요
문제 발생 시 에스컬레이션 절차와 담당자 정보입니다.

## 에스컬레이션 레벨

### Level 1: 운영팀
- 담당: 게임 운영팀
- 대응: 일반 문의, 경미한 이슈
- 연락: ops-team@example.com

### Level 2: 개발팀
- 담당: 백엔드 개발팀
- 대응: 기술적 문제, 버그 수정
- 연락: dev-team@example.com

### Level 3: 인프라팀
- 담당: DevOps/SRE팀
- 대응: 인프라 장애, 성능 이슈
- 연락: infra-team@example.com

### Level 4: 경영진
- 담당: CTO/PM
- 대응: 서비스 중단, 보안 사고
- 연락: emergency@example.com

## 에스컬레이션 기준

| 상황 | 레벨 | 대응 시간 |
|------|------|----------|
| 서비스 완전 중단 | L4 | 즉시 |
| 주요 기능 장애 | L3 | 15분 |
| 성능 저하 | L2 | 1시간 |
| 일반 버그 | L1 | 4시간 |

## 에스컬레이션 절차

1. 문제 발생 인지
2. 심각도 판단
3. 해당 레벨 담당자 연락
4. 30분 내 미해결 시 상위 레벨로 에스컬레이션
5. 해결 후 사후 분석 (RCA) 작성

## 연락처 요약

| 팀 | 이메일 | Slack |
|----|--------|-------|
| 운영팀 | ops-team@example.com | #ops-support |
| 개발팀 | dev-team@example.com | #dev-support |
| 인프라팀 | infra-team@example.com | #infra-oncall |
| 긴급 | emergency@example.com | #incident |
