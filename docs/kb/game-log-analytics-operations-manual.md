# 게임 로그 분석 파이프라인 운영 매뉴얼

## 1. 시스템 개요

### 1.1 아키텍처
```
게임 클라이언트 → Log API → Kinesis Data Streams → Data Firehose → S3 Tables (Iceberg) → Athena → QuickSight
```

### 1.2 주요 컴포넌트

| 컴포넌트 | 역할 | AWS 서비스 |
|---------|------|-----------|
| Log API | 게임 로그 수집 엔드포인트 | API Gateway + Lambda |
| 실시간 수집 | 초당 수천~수백만 레코드 처리 | Kinesis Data Streams |
| 버퍼링 & 배치 | 자동 버퍼링, 배치 처리 | Data Firehose |
| 데이터 저장 | Apache Iceberg 테이블 | S3 Tables |
| SQL 쿼리 | 고성능 분석 쿼리 | Amazon Athena |
| 대시보드 | 시각화 및 BI | Amazon QuickSight |

## 2. 일상 운영

### 2.1 모니터링 대시보드

**CloudWatch 대시보드**: `GameLogAnalytics-Dashboard`

주요 메트릭:
- `Kinesis/IncomingRecords`: 초당 수집 레코드 수
- `Kinesis/WriteProvisionedThroughputExceeded`: 쓰기 제한 초과
- `Firehose/DeliveryToS3.Records`: S3 전송 레코드 수
- `Firehose/DeliveryToS3.DataFreshness`: 데이터 지연 시간
- `Athena/TotalExecutionTime`: 쿼리 실행 시간

### 2.2 일일 점검 항목

1. **데이터 수집 상태**
   ```sql
   -- Athena에서 최근 데이터 확인
   SELECT DATE(event_time) as date, COUNT(*) as records
   FROM game_logs.player_events
   WHERE event_time >= current_date - interval '1' day
   GROUP BY DATE(event_time)
   ORDER BY date DESC;
   ```

2. **Kinesis 샤드 사용률**
   - CloudWatch > Kinesis > 스트림 선택 > `IncomingBytes` / `WriteProvisionedThroughputExceeded`
   - 사용률 80% 초과 시 샤드 증설 검토

3. **S3 Tables 상태**
   ```bash
   aws s3tables get-table --table-bucket-arn <bucket-arn> --namespace game_logs --name player_events
   ```

### 2.3 주간 점검 항목

1. **Iceberg 테이블 최적화**
   ```sql
   -- 스냅샷 정리 (7일 이전)
   ALTER TABLE game_logs.player_events
   EXECUTE expire_snapshots(retention_threshold => '7d');
   
   -- 데이터 파일 압축
   ALTER TABLE game_logs.player_events
   EXECUTE optimize WHERE event_time >= current_date - interval '7' day;
   ```

2. **비용 검토**
   - Cost Explorer에서 Kinesis, S3, Athena 비용 확인
   - 이상 비용 발생 시 쿼리 패턴 분석

## 3. 데이터 스키마

### 3.1 player_events 테이블

```sql
CREATE TABLE game_logs.player_events (
    event_id STRING,
    event_time TIMESTAMP,
    event_type STRING,      -- login, logout, purchase, level_up, match_start, match_end
    player_id STRING,
    game_id STRING,
    server_id STRING,
    session_id STRING,
    event_data MAP<STRING, STRING>,
    client_ip STRING,
    client_version STRING,
    platform STRING         -- ios, android, pc, console
)
PARTITIONED BY (day(event_time), event_type)
LOCATION 's3://game-logs-bucket/player_events/'
TBLPROPERTIES ('table_type' = 'ICEBERG');
```

### 3.2 주요 이벤트 타입

| event_type | 설명 | event_data 필드 |
|------------|------|----------------|
| login | 로그인 | device_id, login_method |
| logout | 로그아웃 | session_duration |
| purchase | 인앱 구매 | item_id, price, currency |
| level_up | 레벨업 | old_level, new_level |
| match_start | 매치 시작 | match_id, game_mode |
| match_end | 매치 종료 | match_id, result, score |

## 4. 자주 사용하는 쿼리

### 4.1 DAU (일일 활성 사용자)
```sql
SELECT DATE(event_time) as date,
       COUNT(DISTINCT player_id) as dau
FROM game_logs.player_events
WHERE event_type = 'login'
  AND event_time >= current_date - interval '30' day
GROUP BY DATE(event_time)
ORDER BY date DESC;
```

### 4.2 매출 분석
```sql
SELECT DATE(event_time) as date,
       COUNT(*) as transactions,
       SUM(CAST(event_data['price'] AS DECIMAL(10,2))) as revenue
FROM game_logs.player_events
WHERE event_type = 'purchase'
  AND event_time >= current_date - interval '7' day
GROUP BY DATE(event_time)
ORDER BY date DESC;
```

### 4.3 리텐션 분석
```sql
WITH first_login AS (
    SELECT player_id, MIN(DATE(event_time)) as first_date
    FROM game_logs.player_events
    WHERE event_type = 'login'
    GROUP BY player_id
)
SELECT f.first_date,
       COUNT(DISTINCT f.player_id) as new_users,
       COUNT(DISTINCT CASE WHEN DATE(e.event_time) = f.first_date + interval '1' day THEN e.player_id END) as d1_retained,
       COUNT(DISTINCT CASE WHEN DATE(e.event_time) = f.first_date + interval '7' day THEN e.player_id END) as d7_retained
FROM first_login f
LEFT JOIN game_logs.player_events e ON f.player_id = e.player_id AND e.event_type = 'login'
WHERE f.first_date >= current_date - interval '30' day
GROUP BY f.first_date
ORDER BY f.first_date DESC;
```

## 5. 접근 권한

### 5.1 IAM 역할

| 역할 | 권한 | 대상 |
|-----|------|-----|
| GameLogAnalytics-Admin | 전체 관리 | 인프라 팀 |
| GameLogAnalytics-Analyst | Athena 쿼리, QuickSight 조회 | 데이터 분석팀 |
| GameLogAnalytics-Viewer | QuickSight 대시보드 조회 | 기획팀, 운영팀 |

### 5.2 QuickSight 대시보드

- **GameAnalytics-Overview**: DAU, MAU, 매출 요약
- **GameAnalytics-Retention**: 리텐션 분석
- **GameAnalytics-Revenue**: 매출 상세 분석
- **GameAnalytics-Realtime**: 실시간 접속자 현황

## 6. 연락처

| 담당 | 역할 | 연락처 |
|-----|------|-------|
| 인프라팀 | 파이프라인 운영 | infra@example.com |
| 데이터팀 | 분석 쿼리 지원 | data@example.com |
| 게임운영팀 | 비즈니스 문의 | gameops@example.com |
