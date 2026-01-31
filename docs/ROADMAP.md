# 로드맵 및 개선 계획

## 비전: Agent가 Agent를 만들고 개선하는 플랫폼

```
┌─────────────────────────────────────────────────────────────────┐
│                    궁극적 목표                                   │
│                                                                 │
│   사용자: "HR Agent 만들어줘. 휴가 신청이랑 직원 조회 기능으로"   │
│                          ↓                                      │
│   Agent Builder Agent가 자동으로:                               │
│   1. 도구 코드 생성 (src/tools/hr_tools.py)                     │
│   2. Agent 생성 (src/agent/hr_agent.py)                         │
│   3. Supervisor에 연결                                          │
│   4. 테스트 실행                                                │
│                          ↓                                      │
│   사용자: "HR Agent가 자꾸 틀려. 개선해줘"                       │
│                          ↓                                      │
│   Agent Builder Agent가 자동으로:                               │
│   1. 실행 로그 분석                                             │
│   2. KB 문서 생성/수정                                          │
│   3. System Prompt 개선                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 현재 버전 상태

| 기능 | 상태 | 설명 |
|------|------|------|
| Multi-Agent 협업 | ✅ 완료 | Supervisor + DevOps + Analytics |
| 실행 기록 저장 | ✅ 완료 | DynamoDB + 조회 API |
| 피드백 수집 | ✅ 완료 (v1.1) | 👍/👎 버튼 + 코멘트 + 변경 기능 |
| Agent 자동 생성 | ❌ 미구현 | 코드 직접 작성 필요 |
| 자동 개선 제안 | ❌ 미구현 | 피드백 데이터 축적 후 진행 |

---

## 개선 로드맵

### v1.1 - 피드백 수집 ✅ 완료

**목표**: 개선 사이클의 입력 데이터 확보

| 작업 | 상태 |
|------|------|
| 피드백 UI (👍/👎 버튼 + 코멘트) | ✅ |
| 피드백 저장 (DynamoDB) | ✅ |
| 피드백 조회 API | ✅ |
| 중복 방지 + 변경 기능 | ✅ |

---

### v1.2 - Agent Builder Agent ⭐ (다음 진행)

**목표**: 자연어로 Agent를 생성하고 개선

#### 구현 방안

**Option A: Kiro CLI 확장** (권장, 빠른 구현)
```
사용자가 Kiro CLI에서:
> "HR Agent 만들어줘"

Kiro가 자동으로:
1. src/tools/hr_tools.py 생성
2. src/agent/hr_agent.py 생성
3. supervisor_agent.py에 연결 추가
```

**Option B: AgentCore 기반** (프로덕션용)
- Agent Builder를 별도 AgentCore Agent로 배포
- API로 Agent 생성 요청

#### Agent Builder 기능

| 명령 예시 | 동작 |
|----------|------|
| "HR Agent 만들어줘" | 도구 + Agent 코드 생성 |
| "휴가 신청 도구 추가해줘" | 기존 Agent에 도구 추가 |
| "HR Agent 테스트해줘" | 자동 테스트 실행 |

#### 필요한 도구

```python
@tool
def create_tool(name: str, description: str, parameters: str, implementation: str) -> str:
    """새로운 도구를 생성합니다."""

@tool
def create_agent(name: str, tools: list[str], system_prompt: str) -> str:
    """새로운 Agent를 생성합니다."""

@tool
def add_to_supervisor(agent_name: str) -> str:
    """Agent를 Supervisor에 연결합니다."""
```

---

### v1.3 - 자동 개선 제안 (피드백 축적 후)

**목표**: 수집된 피드백을 분석하여 Agent 개선 방안 제안

**전제조건**: 충분한 피드백 데이터 축적 (최소 50건 이상 권장)

| 작업 | 설명 |
|------|------|
| 실패 패턴 분석 | 부정 피드백에서 공통 패턴 추출 |
| KB 문서 초안 생성 | 실패 케이스 → 가이드 문서 자동 생성 |
| System Prompt 제안 | 개선된 지침 제안 |

#### 필요한 도구

```python
@tool
def analyze_failures(agent_name: str, days: int = 7) -> str:
    """실패 로그를 분석하여 개선점을 찾습니다."""

@tool
def update_knowledge_base(topic: str, content: str) -> str:
    """Knowledge Base에 문서를 추가합니다."""

@tool
def improve_system_prompt(agent_name: str, suggestion: str) -> str:
    """Agent의 System Prompt를 개선합니다."""
```

---

### v2.0 - 자동화 워크플로우

**목표**: 정기 작업 자동 실행

| 작업 | 설명 |
|------|------|
| 스케줄러 | 일/주간 자동 분석 |
| 자동 개선 실행 | 제안된 개선 자동 적용 (승인 후) |
| 알림 연동 | Slack/이메일 알림 |

---

### v3.0 - 프로덕션

**목표**: 실제 운영 환경 배포

| 작업 | 설명 |
|------|------|
| 인증/권한 | Cognito + RBAC |
| 멀티 테넌트 | 조직별 격리 |
| AgentCore 배포 | 관리형 런타임 |

---

## 일정 요약

```
2026-01 Week 5 ──────────────────────────────────────────────
         v1.1 피드백 수집 ✅ 완료

2026-02 Week 1-3 ────────────────────────────────────────────
         v1.2 Agent Builder Agent ⭐ (진행 중)

2026-02 Week 4 ~ (피드백 축적 후) ────────────────────────────
         v1.3 자동 개선 제안

2026-03 ─────────────────────────────────────────────────────
         v2.0 자동화 워크플로우

2026-04 ─────────────────────────────────────────────────────
         v3.0 프로덕션
```

---

## 성공 지표

### v1.1 ✅
- [x] 피드백 수집 기능 구현
- [x] 중복 방지 + 변경 기능

### v1.2 (Agent Builder)
- [ ] 자연어로 Agent 생성 가능
- [ ] 자연어로 도구 추가 가능
- [ ] Supervisor 자동 연결

### v1.3 (자동 개선)
- [ ] 자동 제안 정확도 > 70%
- [ ] KB 문서 자동 생성

### v3.0
- [ ] 99.9% 가용성
- [ ] 동시 사용자 100명 지원

---

## 다음 단계

**즉시 시작**: v1.2 Agent Builder (Kiro CLI 확장)

Kiro CLI는 이미 파일 생성/수정이 가능하므로, Agent Builder 도구만 추가하면 바로 사용 가능합니다.

```bash
# Kiro CLI에서 바로 사용
> "HR Agent 만들어줘. 휴가 신청, 직원 조회, 급여 문의 기능으로"
```
