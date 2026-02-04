# 장애 대응 가이드

## 에스컬레이션 절차

1. L1: 담당자 확인 (5분 이내)
2. L2: 팀 리더 보고 (15분 이내)
3. L3: 부서장 보고 (30분 이내)

## 주요 장애 유형

### Kinesis 샤드 용량 초과
- 증상: WriteProvisionedThroughputExceeded 에러
- 조치: 샤드 수 증가 또는 배치 크기 조정

### EC2 인스턴스 장애
- 증상: StatusCheckFailed 알람
- 조치: 인스턴스 재시작 또는 교체
