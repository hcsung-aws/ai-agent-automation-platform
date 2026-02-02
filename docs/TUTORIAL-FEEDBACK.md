# 튜토리얼: 피드백 루프 설정

Agent가 동작하면 **피드백을 수집하여 지속적으로 개선**해야 합니다.

예상 소요 시간: 20분

---

## 왜 피드백이 필요한가?

```
Agent 배포 → 사용자 사용 → 문제 발생 → ???
```

피드백 없이는 어떤 문제가 있는지 알 수 없습니다.

```
Agent 배포 → 사용자 사용 → 👎 피드백 → 패턴 분석 → 개선
```

---

## Step 1: 피드백 테이블 생성 (5분)

### DynamoDB 테이블 생성

```bash
aws dynamodb create-table \
    --table-name agent-feedback \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
        AttributeName=message_id,AttributeType=S \
    --key-schema \
        AttributeName=session_id,KeyType=HASH \
        AttributeName=message_id,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

### 테이블 구조

| 필드 | 설명 |
|------|------|
| session_id | 세션 식별자 |
| message_id | 메시지 식별자 |
| timestamp | 피드백 시간 |
| rating | positive / negative |
| user_input | 사용자 질문 |
| agent_response | Agent 응답 |
| comment | 사용자 코멘트 (선택) |

---

## Step 2: 피드백 UI 확인 (5분)

이 프로젝트의 `app.py`에는 이미 피드백 버튼이 구현되어 있습니다.

### 피드백 버튼

각 Agent 응답 아래에 👍/👎 버튼이 표시됩니다:

```
Agent: 홍길동님의 휴가 잔여일은 12일입니다.

[👍 도움됨] [👎 개선필요]
```

### 피드백 저장

버튼 클릭 시 `agent-feedback` 테이블에 저장됩니다.

---

## Step 3: 피드백 조회 (5분)

### API 서버 실행

```bash
uvicorn logs_api:app --port 8001
```

### 대시보드 접속

브라우저에서 `http://localhost:8001/feedback` 접속

### API로 조회

```bash
# 전체 피드백
curl http://localhost:8001/api/feedback

# 부정 피드백만
curl http://localhost:8001/api/feedback?rating=negative
```

---

## Step 4: 피드백 분석 및 개선 (5분)

### 자동 분석 도구 사용

Supervisor에게 피드백 분석을 요청합니다:

```
"피드백 분석해서 개선점 알려줘"
```

Supervisor가 `analyze_negative_feedback` 도구를 호출하여:
1. 부정 피드백 조회
2. 공통 패턴 분석
3. 개선 방안 제안

### 분석 결과 예시

```
## 부정 피드백 분석 (5건)

### 공통 실패 패턴
1. 직원 ID 형식 오류 (3건)
   - 사용자가 "E001" 대신 "1번" 등으로 입력

### KB 문서 제안
- "직원 ID 형식 안내" 문서 추가 권장

### System Prompt 개선
- "직원 ID는 E001 형식입니다" 안내 추가 권장
```

### Agent Builder로 개선 적용

```
"HR Agent가 직원 ID 형식을 안내하도록 시스템 프롬프트 개선해줘"
```

---

## 피드백 루프 사이클

```
┌─────────────────────────────────────────┐
│                                         │
│   1. Agent 사용                         │
│          ↓                              │
│   2. 👍/👎 피드백 수집                  │
│          ↓                              │
│   3. 주간 피드백 분석                   │
│          ↓                              │
│   4. 개선점 파악                        │
│          ↓                              │
│   5. Agent Builder로 개선               │
│          ↓                              │
│   (1번으로 반복)                        │
│                                         │
└─────────────────────────────────────────┘
```

---

## 권장 운영 방식

### 주간 리뷰

매주 1회 피드백을 검토합니다:

```bash
# 지난 7일 부정 피드백 확인
curl "http://localhost:8001/api/feedback?rating=negative&limit=50"
```

### 개선 우선순위

| 우선순위 | 기준 |
|----------|------|
| 높음 | 같은 패턴 3회 이상 반복 |
| 중간 | 사용자 코멘트에 구체적 불만 |
| 낮음 | 단발성 오류 |

### 개선 적용

1. 패턴 파악 → Agent Builder에게 개선 요청
2. 테스트 → 동일 질문으로 확인
3. 배포 → 다음 주 피드백 모니터링

---

## 다음 단계

단일 Agent가 안정화되면 **Multi-Agent 구성**으로 확장합니다.

→ [TUTORIAL-MULTI-AGENT.md](TUTORIAL-MULTI-AGENT.md)
