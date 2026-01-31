# 게임 로그 분석 파이프라인 장애 대응 가이드

## 1. 장애 등급 정의

| 등급 | 정의 | 대응 시간 | 예시 |
|-----|------|----------|-----|
| P1 (Critical) | 데이터 수집 완전 중단 | 15분 이내 | Kinesis 스트림 다운, Log API 장애 |
| P2 (High) | 데이터 지연 또는 일부 손실 | 1시간 이내 | Firehose 전송 지연, 샤드 제한 초과 |
| P3 (Medium) | 분석 기능 장애 | 4시간 이내 | Athena 쿼리 실패, QuickSight 오류 |
| P4 (Low) | 성능 저하 | 24시간 이내 | 쿼리 속도 저하, 대시보드 로딩 지연 |

## 2. 장애 유형별 대응

### 2.1 Kinesis Data Streams 장애

#### 증상: WriteProvisionedThroughputExceeded 알람
**원인**: 샤드 용량 초과

**즉시 조치**:
```bash
# 현재 샤드 수 확인
aws kinesis describe-stream-summary --stream-name game-log-stream

# 샤드 수 증가 (예: 4 → 8)
aws kinesis update-shard-count \
    --stream-name game-log-stream \
    --target-shard-count 8 \
    --scaling-type UNIFORM_SCALING
```

**확인**:
```bash
# 스트림 상태 확인 (ACTIVE가 될 때까지 대기)
aws kinesis describe-stream-summary --stream-name game-log-stream
```

#### 증상: GetRecords.IteratorAgeMilliseconds 증가
**원인**: 컨슈머 처리 지연

**조치**:
1. Firehose 상태 확인
2. Lambda 컨슈머가 있다면 동시성 확인
3. 필요시 Enhanced Fan-Out 활성화

---

### 2.2 Data Firehose 장애

#### 증상: DeliveryToS3.DataFreshness > 900초
**원인**: S3 전송 지연

**확인**:
```bash
# Firehose 상태 확인
aws firehose describe-delivery-stream --delivery-stream-name game-log-firehose

# 최근 에러 확인
aws logs filter-log-events \
    --log-group-name /aws/kinesisfirehose/game-log-firehose \
    --start-time $(date -d '1 hour ago' +%s000) \
    --filter-pattern "ERROR"
```

**조치**:
1. S3 버킷 권한 확인
2. S3 Tables 상태 확인
3. 버퍼 설정 조정 (필요시)

#### 증상: DeliveryToS3.Success < 1
**원인**: S3 전송 실패

**확인**:
```bash
# 에러 로그 확인
aws logs filter-log-events \
    --log-group-name /aws/kinesisfirehose/game-log-firehose \
    --filter-pattern "?AccessDenied ?ServiceUnavailable ?InternalError"
```

**조치**:
1. IAM 역할 권한 확인
2. S3 버킷 정책 확인
3. S3 Tables 테이블 상태 확인

---

### 2.3 S3 Tables (Iceberg) 장애

#### 증상: Athena 쿼리 시 "Table not found" 또는 메타데이터 오류
**원인**: 테이블 메타데이터 손상

**확인**:
```bash
# 테이블 상태 확인
aws s3tables get-table \
    --table-bucket-arn arn:aws:s3tables:us-east-1:ACCOUNT:bucket/game-logs \
    --namespace game_logs \
    --name player_events
```

**조치**:
```sql
-- Athena에서 테이블 복구 시도
MSCK REPAIR TABLE game_logs.player_events;
```

#### 증상: 쿼리 성능 급격히 저하
**원인**: 스몰 파일 문제 또는 스냅샷 과다

**조치**:
```sql
-- 테이블 최적화 (Compaction)
ALTER TABLE game_logs.player_events
EXECUTE optimize WHERE event_time >= current_date - interval '1' day;

-- 오래된 스냅샷 정리
ALTER TABLE game_logs.player_events
EXECUTE expire_snapshots(retention_threshold => '3d');

-- 고아 파일 정리
ALTER TABLE game_logs.player_events
EXECUTE remove_orphan_files(retention_threshold => '3d');
```

---

### 2.4 Athena 장애

#### 증상: 쿼리 실행 실패 - "HIVE_METASTORE_ERROR"
**원인**: Glue Data Catalog 연결 문제

**확인**:
```bash
# Glue 테이블 확인
aws glue get-table --database-name game_logs --name player_events
```

**조치**:
1. Glue Data Catalog 서비스 상태 확인
2. IAM 권한 확인 (glue:GetTable, glue:GetPartitions)
3. 테이블 재생성 (최후 수단)

#### 증상: 쿼리 타임아웃
**원인**: 대용량 스캔 또는 비효율적 쿼리

**조치**:
1. 파티션 필터 추가
   ```sql
   -- Bad
   SELECT * FROM game_logs.player_events WHERE player_id = 'xxx';
   
   -- Good (파티션 필터 추가)
   SELECT * FROM game_logs.player_events 
   WHERE event_time >= current_date - interval '1' day
     AND player_id = 'xxx';
   ```

2. 워크그룹 설정 확인
   ```bash
   aws athena get-work-group --work-group primary
   ```

---

### 2.5 QuickSight 장애

#### 증상: 대시보드 로딩 실패
**원인**: SPICE 데이터셋 새로고침 실패

**확인**:
```bash
# 데이터셋 새로고침 상태 확인
aws quicksight list-ingestions \
    --aws-account-id ACCOUNT_ID \
    --data-set-id DATASET_ID
```

**조치**:
1. SPICE 용량 확인
2. 데이터 소스 연결 확인
3. 수동 새로고침 실행

#### 증상: "Access Denied" 오류
**원인**: 권한 문제

**조치**:
1. QuickSight 사용자 권한 확인
2. 데이터 소스 권한 확인
3. Row-Level Security 설정 확인

---

## 3. 데이터 복구 절차

### 3.1 데이터 손실 시 복구

**1단계: 손실 범위 파악**
```sql
-- 시간대별 레코드 수 확인
SELECT DATE_TRUNC('hour', event_time) as hour, COUNT(*) as records
FROM game_logs.player_events
WHERE event_time >= timestamp '2024-01-01 00:00:00'
  AND event_time < timestamp '2024-01-02 00:00:00'
GROUP BY DATE_TRUNC('hour', event_time)
ORDER BY hour;
```

**2단계: Kinesis 데이터 보존 확인**
```bash
# 스트림 보존 기간 확인 (기본 24시간)
aws kinesis describe-stream-summary --stream-name game-log-stream
```

**3단계: 백업에서 복구**
- S3 버전 관리가 활성화된 경우 이전 버전 복구
- Iceberg 타임 트래블 사용:
  ```sql
  -- 특정 시점 데이터 조회
  SELECT * FROM game_logs.player_events
  FOR TIMESTAMP AS OF timestamp '2024-01-01 12:00:00';
  ```

### 3.2 테이블 복구

**Iceberg 스냅샷에서 복구**:
```sql
-- 스냅샷 목록 확인
SELECT * FROM game_logs."player_events$snapshots";

-- 특정 스냅샷으로 롤백
ALTER TABLE game_logs.player_events
EXECUTE rollback_to_snapshot(snapshot_id => 1234567890);
```

---

## 4. 에스컬레이션 절차

### 4.1 에스컬레이션 경로

```
L1 (운영팀) → L2 (인프라팀) → L3 (AWS Support)
   15분          30분           1시간
```

### 4.2 AWS Support 케이스 생성 시 포함 정보

1. **장애 시간**: 시작/종료 시간 (UTC)
2. **영향 범위**: 영향받는 서비스, 사용자 수
3. **에러 메시지**: 전체 에러 로그
4. **시도한 조치**: 이미 수행한 트러블슈팅
5. **리소스 ARN**: 관련 AWS 리소스 ARN

---

## 5. 장애 후 조치

### 5.1 RCA (Root Cause Analysis) 작성

모든 P1, P2 장애 후 24시간 내 RCA 작성:

```markdown
## 장애 보고서

### 개요
- 장애 시간: YYYY-MM-DD HH:MM ~ HH:MM (KST)
- 영향: [영향 범위]
- 등급: P1/P2

### 타임라인
- HH:MM - [이벤트]
- HH:MM - [이벤트]

### 근본 원인
[원인 분석]

### 조치 사항
[수행한 조치]

### 재발 방지
- [ ] [액션 아이템 1]
- [ ] [액션 아이템 2]
```

### 5.2 모니터링 개선

장애 후 필요시 알람 추가/조정:
```bash
# CloudWatch 알람 생성 예시
aws cloudwatch put-metric-alarm \
    --alarm-name "Kinesis-HighIteratorAge" \
    --metric-name GetRecords.IteratorAgeMilliseconds \
    --namespace AWS/Kinesis \
    --statistic Maximum \
    --period 300 \
    --threshold 60000 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:alerts
```

---

## 6. 연락처

| 상황 | 담당 | 연락처 |
|-----|------|-------|
| P1/P2 장애 | 인프라팀 온콜 | oncall@example.com, 010-XXXX-XXXX |
| P3/P4 장애 | 인프라팀 | infra@example.com |
| AWS 기술 지원 | AWS Support | AWS Console > Support |
| 비즈니스 영향 보고 | 게임운영팀 | gameops@example.com |
