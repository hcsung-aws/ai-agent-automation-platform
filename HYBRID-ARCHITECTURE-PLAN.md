# Hybrid Architecture 전환 계획

## 목표

현재 AgentCore 전용 또는 Fargate 독자 스택으로 분리된 배포 구조를 **Hybrid 아키텍처**로 통합한다.

```
User → Fargate (Chainlit UI, :8000)
         │ boto3.invoke_agent_runtime()
         ▼
       AgentCore Runtime (Supervisor + Agents, :8080)
         │
         ├── Bedrock LLM
         ├── Bedrock KB (S3 Vectors, 자동 생성)
         └── S3 (피드백 공통 저장 → 향후 KB 학습)
```

## 배경

- AgentCore는 API 전용 (:8080, POST /invocations) → Chainlit 웹 UI 서빙 불가
- agent-builder E2E 테스트 시 Fargate 독자 스택 생성 → template/aws의 KB 자동 생성 우회
- 해결: Fargate(UI) + AgentCore(Agents) 분리, template/aws에서 통합 관리

## 핵심 원칙

1. **Agent 코드 변경 없음**: supervisor.py, agents, tools, main.py는 로컬/AWS 동일
2. **app.py 최소 분기**: 환경변수 1개(AGENT_RUNTIME_ARN)로 transport만 전환
3. **KB 자동 생성**: template/aws의 InfrastructureStack이 KB를 자동 생성 (이미 구현됨)
4. **피드백 S3 공통 저장**: 향후 KB 학습에 활용 가능

## 개발 워크플로 (전환 후)

```
1. 로컬 개발: supervisor.py, agents, tools 작성
2. 로컬 테스트:
   a) chainlit run app.py (UI 테스트, 직접 Agent 호출)
   b) agentcore dev → agentcore invoke --dev (AgentCore 시뮬레이션)
3. AWS 배포: deploy.sh → Infrastructure + AgentCore + UI 자동 배포
```

---

## Phase 1: feedback_store.py S3 모드 추가

**파일**: `templates/local/feedback_store.py`

현재 local JSON / DynamoDB만 지원. S3 모드 추가.

```
FEEDBACK_STORAGE 환경변수:
- "local" (기본): JSON 파일 저장
- "dynamodb": DynamoDB 테이블 저장
- "s3": S3 버킷 저장 (FEEDBACK_BUCKET 필수) ← 추가
```

S3 저장 형식: `s3://{FEEDBACK_BUCKET}/feedback/{date}/{message_id}.json`

**참고**: news-agent의 feedback_store.py에 S3 구현이 이미 있음.

---

## Phase 2: app.py AgentCore API 클라이언트 모드

**파일**: `templates/local/app.py`

환경변수 `AGENT_RUNTIME_ARN`이 설정되면 API 클라이언트 모드로 동작.

### 변경 사항

1. `_call_agent(prompt)` 함수 추가:
   - AGENT_RUNTIME_ARN 있음 → boto3 `invoke_agent_runtime` 호출
   - AGENT_RUNTIME_ARN 없음 → 기존 직접 호출 (supervisor(prompt))

2. `on_message`에서 `_call_agent()` 사용

3. 환영 메시지:
   - 로컬 모드: 기존 동적 감지 (inspect.getmembers)
   - API 모드: 환경변수 `AGENT_NAMES`로 Agent 목록 전달 (예: "Guide,News,Analytics")

4. ToolCallTracker:
   - API 모드에서는 AgentCore 응답에 추론 과정이 포함되지 않으므로 비활성화
   - 로컬 모드에서만 동작

### 코드 구조

```python
import os

AGENT_RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN", "")
_IS_API_MODE = bool(AGENT_RUNTIME_ARN)

async def _call_agent(prompt: str, session_id: str) -> str:
    if _IS_API_MODE:
        return await asyncio.to_thread(_invoke_agentcore, prompt, session_id)
    else:
        _tracker.reset()
        response = await asyncio.to_thread(supervisor, prompt)
        return str(response)

def _invoke_agentcore(prompt: str, session_id: str) -> str:
    client = boto3.client('bedrock-agentcore')
    resp = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        runtimeSessionId=session_id,
        payload=json.dumps({"prompt": prompt}).encode()
    )
    # streaming 응답 처리
    ...
```

---

## Phase 3: UI Dockerfile 생성

**파일**: `templates/local/Dockerfile.ui`

Chainlit UI 전용 컨테이너. Agent 코드 불포함.

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements-ui.txt .
RUN pip install --no-cache-dir -r requirements-ui.txt
COPY app.py config.py feedback_store.py ./
EXPOSE 8000
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
```

**파일**: `templates/local/requirements-ui.txt`

```
chainlit
boto3
```

---

## Phase 4: ui_stack.py 생성

**파일**: `templates/aws/cdk/stacks/ui_stack.py`

Fargate + Internal ALB. AgentCore Runtime ARN을 환경변수로 전달.

### 입력 파라미터
- `agent_runtime_arn`: AgentCoreStack에서 전달
- `kb_bucket`: InfrastructureStack에서 전달 (피드백 S3 저장용)
- `agent_names`: Agent 목록 문자열 (환영 메시지용)

### 리소스
- VPC (Public + Private, NAT 1개)
- ECS Cluster + Fargate Service
- Internal ALB
- ECS Exec 활성화 (SSM 접속용)

### 환경변수
```
AGENT_RUNTIME_ARN: AgentCore Runtime ARN
FEEDBACK_STORAGE: s3
FEEDBACK_BUCKET: KB S3 버킷명
BEDROCK_REGION: us-east-1
AGENT_NAMES: "Guide" (또는 동적)
```

### IAM 권한
- bedrock-agentcore:InvokeAgentRuntime
- s3:PutObject, s3:GetObject (피드백 버킷)

---

## Phase 5: CDK app.py 수정

**파일**: `templates/aws/cdk/app.py`

```python
# 3. UI 스택 (Fargate + Chainlit)
ui_stack = UIStack(
    app, f"{stack_prefix}UI",
    env=env,
    agent_runtime_arn=agentcore_stack.runtime.agent_runtime_arn,
    kb_bucket=infra_stack.kb_bucket,
    stack_prefix=stack_prefix,
)
ui_stack.add_dependency(agentcore_stack)
```

---

## Phase 6: deploy.sh 수정

**파일**: `templates/aws/deploy.sh`

배포 순서: Infrastructure → AgentCore → UI

출력에 UI 접속 정보 추가:
```
Internal ALB URL: http://internal-xxx.elb.amazonaws.com
SSM 포트포워딩: aws ssm start-session ...
```

---

## Phase 7: agent-builder 가이드 수정

**파일**: `context_rule/agent-builder-guide.md`, `templates/local/agent-builder.json`

### 변경 사항
1. "AWS 배포" 섹션: 독자 스택 생성 금지, 항상 template/aws/deploy.sh 사용
2. 배포 워크플로: agents/에 코드 추가 → deploy.sh → 3개 스택 자동 배포
3. KB는 InfrastructureStack에서 자동 생성됨을 명시

---

## Phase 8: 검증

1. `cd templates/aws/cdk && cdk synth --quiet` → 3개 스택 생성 확인
2. `pytest tests/ -v` → 기존 15개 테스트 통과
3. 로컬 테스트: `chainlit run app.py` (AGENT_RUNTIME_ARN 미설정 → 직접 모드)

---

## Phase 9: 정리

1. news-agent의 `deploy/` 독자 스택 → 제거 또는 deprecated 표시
2. README 아키텍처 다이어그램 업데이트
3. SESSION 로그 업데이트, git commit + push

---

## 파일 변경 요약

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| templates/local/feedback_store.py | 수정 | S3 모드 추가 |
| templates/local/app.py | 수정 | AgentCore API 클라이언트 모드 |
| templates/local/Dockerfile.ui | 신규 | UI 전용 컨테이너 |
| templates/local/requirements-ui.txt | 신규 | UI 의존성 |
| templates/aws/cdk/stacks/ui_stack.py | 신규 | Fargate + Chainlit |
| templates/aws/cdk/app.py | 수정 | UIStack 추가 |
| templates/aws/deploy.sh | 수정 | 3개 스택 배포 + UI 접속 정보 |
| context_rule/agent-builder-guide.md | 수정 | 배포 가이드 업데이트 |
| templates/local/agent-builder.json | 수정 | 리소스 참조 업데이트 |

---

## 진행 상태

- [x] Phase 1: feedback_store.py S3 모드 추가
- [x] Phase 2: app.py AgentCore API 클라이언트 모드
- [x] Phase 3: UI Dockerfile + requirements-ui.txt 생성
- [x] Phase 4: ui_stack.py 생성
- [x] Phase 5: CDK app.py 수정
- [x] Phase 6: deploy.sh 수정
- [x] Phase 7: agent-builder 가이드 수정
- [x] Phase 8: 검증 (CDK synth 3개 스택 ✅ + pytest 15/15 ✅)
- [ ] Phase 9: 정리 (README, git)

## Last Updated
2026-02-23 Mickey 25
