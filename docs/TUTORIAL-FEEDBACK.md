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

## Step 1: Chainlit 피드백 버튼 활성화 (5분)

Chainlit은 `@cl.on_feedback` 콜백을 등록하면 메시지별 👍/👎 버튼을 자동으로 표시합니다.

별도의 config 설정은 필요 없습니다.

---

## Step 2: 피드백 저장 (5분)

Chainlit의 피드백 콜백을 활용하여 피드백을 파일에 저장합니다.

### `templates/local/app.py`에 콜백 추가

```python
import json
from datetime import datetime
from pathlib import Path
import chainlit as cl

FEEDBACK_FILE = Path("feedback.jsonl")

@cl.on_feedback
async def on_feedback(feedback: cl.types.Feedback):
    """피드백을 JSONL 파일에 저장합니다."""
    record = {
        "timestamp": datetime.now().isoformat(),
        "for_message_id": feedback.forId,
        "rating": "positive" if feedback.value == 1 else "negative",
        "comment": feedback.comment or "",
    }
    with open(FEEDBACK_FILE, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

### 저장 형식

`feedback.jsonl`에 한 줄씩 저장됩니다:

```json
{"timestamp": "2026-02-09T10:30:00", "for_message_id": "abc123", "rating": "negative", "comment": "직원 ID 형식을 몰랐어요"}
```

---

## Step 3: 피드백 분석 및 개선 (10분)

### 부정 피드백 확인

```bash
cd templates/local
# 부정 피드백만 필터
grep '"negative"' feedback.jsonl | python -m json.tool
```

### Agent Builder로 개선 적용

부정 피드백에서 패턴을 발견하면 Agent Builder에게 개선을 요청합니다:

```bash
kiro chat --agent agent-builder
```

```
"HR Agent가 직원 ID 형식을 안내하도록 시스템 프롬프트 개선해줘.
사용자들이 'E001' 형식을 모르고 '1번' 등으로 입력하는 경우가 많아."
```

Agent Builder가 `agents/hr_agent.py`의 SYSTEM_PROMPT를 수정합니다.

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
# 부정 피드백 수 확인
grep -c '"negative"' feedback.jsonl

# 최근 부정 피드백 확인
grep '"negative"' feedback.jsonl | tail -10
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

## 확장: DynamoDB로 피드백 저장 (선택)

팀 규모가 커지면 파일 대신 DynamoDB에 저장할 수 있습니다.

### 테이블 생성

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

### 피드백 콜백 수정

```python
import boto3

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("agent-feedback")

@cl.on_feedback
async def on_feedback(feedback: cl.types.Feedback):
    table.put_item(Item={
        "session_id": cl.user_session.get("id", "unknown"),
        "message_id": feedback.forId,
        "timestamp": datetime.now().isoformat(),
        "rating": "positive" if feedback.value == 1 else "negative",
        "comment": feedback.comment or "",
    })
```

---

## 다음 단계

단일 Agent가 안정화되면 **Multi-Agent 구성**으로 확장합니다.

→ [TUTORIAL-MULTI-AGENT.md](TUTORIAL-MULTI-AGENT.md)
