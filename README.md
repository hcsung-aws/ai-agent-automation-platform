# AIOps 스타터 킷

[English](#english-version) | 한국어

## 🎯 프로젝트 비전

**자연어로 AI Agent를 만들고, 로컬에서 테스트하고, AWS에 배포하여 AIOps를 시작하세요.**

이 프로젝트는 조직이 AI Agent 기반 운영 자동화를 **쉽고 빠르게 도입**할 수 있도록 돕는 스타터 킷입니다.

```
┌─────────────────────────────────────────────────────────────┐
│  "CloudWatch 알람 조회하는 Agent 만들어줘"                  │
│                         ↓                                   │
│  Agent Builder가 자동으로 코드 생성                         │
│                         ↓                                   │
│  로컬에서 테스트 → 피드백 → 개선                           │
│                         ↓                                   │
│  AWS AgentCore에 배포 → 프로덕션 운영                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 빠른 시작

### 로컬 환경 (5분)

```bash
git clone https://github.com/your-org/aiops-starter-kit.git
cd aiops-starter-kit/templates/local
./setup.sh
source .venv/bin/activate
chainlit run app.py --port 8000
```

브라우저에서 http://localhost:8000 접속

→ [상세 가이드: QUICKSTART-LOCAL.md](docs/QUICKSTART-LOCAL.md)

### AWS 배포 (30분)

```bash
cd templates/aws
./deploy.sh
```

→ [상세 가이드: QUICKSTART-AWS.md](docs/QUICKSTART-AWS.md)

### Agent Builder로 새 Agent 만들기

```bash
kiro chat --agent agent-builder
```

```
"HR Agent 만들어줘. 휴가 조회 기능으로"
```

---

## 🏗️ 아키텍처

### 로컬 환경

```
┌─────────────────────────────────────────────────────────┐
│  localhost:8000                                          │
│  ┌───────────┐    ┌────────────────────────────────┐    │
│  │ Chainlit  │───▶│ Supervisor Agent                │    │
│  │ UI        │    │   ├── Guide Agent              │    │
│  │ (app.py)  │◀───│   │    └── search_project_docs │    │
│  │ 👍👎 피드백│    │   ├── (HR Agent)               │    │
│  │ 🔍 추론   │    │   └── (추가 Agent...)           │    │
│  └───────────┘    └──────────┬─────────────────────┘    │
│                              │                          │
│  ┌───────────────┐    ┌──────▼──────┐  ┌────────────┐  │
│  │ knowledge-    │    │ Amazon      │  │ feedback   │  │
│  │ base/*.md     │    │ Bedrock     │  │ .json      │  │
│  │ (로컬 KB)     │    │ Claude 3.5  │  │ (피드백)   │  │
│  └───────────────┘    └─────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### Template UI 기능
- **추론 과정 표시**: Strands Hooks로 도구 호출 자동 캡처 → 처리 과정 + 상세 보기
- **피드백 버튼**: 👍/👎 cl.Action 버튼 → 로컬 JSON 저장 (AWS 시 S3)
- **동적 환영 메시지**: supervisor.py의 ask_*_agent 도구 자동 감지

### AWS 배포 (Hybrid Architecture)

```
┌─ AIOpsInfrastructure Stack ─────────────────────────────┐
│                                                         │
│  ┌─────────┐  ┌─────────────┐  ┌───────────────────┐   │
│  │ ECR     │  │ KMS         │  │ CloudWatch Logs   │   │
│  │ (Agent  │  │ (암호화 키) │  │ (1개월 보관)      │   │
│  │ 이미지) │  └──────┬──────┘  └───────────────────┘   │
│  └────┬────┘         │                                  │
│       │    ┌─────────▼──────────────────────────────┐   │
│       │    │ Bedrock KB (자동 생성)                  │   │
│       │    │  S3 Vectors + Titan Embeddings V2      │   │
│       │    │  S3 → SQS → Lambda 자동 Sync           │   │
│       │    └────────────────────────────────────────┘   │
│       │                                                 │
│  ┌────▼─────────────────────────────────────────────┐   │
│  │ S3 KB 버킷 + DynamoDB 피드백 + IAM Roles         │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

┌─ AIOpsAgentCore Stack ──────────────────────────────────┐
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ AgentCore Runtime (ARM64)                        │   │
│  │  ┌────────────────────────────────────────────┐  │   │
│  │  │ Supervisor Agent                           │  │   │
│  │  │   └── Guide Agent                         │  │   │
│  │  │        └── KB 검색 (Bedrock KB → S3 → 로컬)│  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  │  POST /invocations :8080  │  GET /ping           │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌───────────────────┐  ┌──────────────────────────┐   │
│  │ Amazon Bedrock     │  │ AgentCore Memory         │   │
│  │ Claude 3.5 Sonnet  │  │ (대화 컨텍스트 유지)     │   │
│  └───────────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

┌─ AIOpsUI Stack ─────────────────────────────────────────┐
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ ECS Fargate + Internal ALB                       │   │
│  │  ┌────────────────────────────────────────────┐  │   │
│  │  │ Chainlit UI (app.py :8000)                 │  │   │
│  │  │   → boto3.invoke_agent_runtime()           │  │   │
│  │  │   → AgentCore API 호출                     │  │   │
│  │  │   → 👍👎 피드백 → S3 저장                  │  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
│  SSM 포트포워딩으로 접속 (Internal ALB)                 │
└─────────────────────────────────────────────────────────┘
```

### KB 검색 폴백 체인

```
1. Bedrock KB (KNOWLEDGE_BASE_ID 설정 시) → 시맨틱 검색
       ↓ 미설정 또는 실패
2. S3 버킷 (KB_S3_BUCKET 설정 시) → 키워드 검색
       ↓ 미설정 또는 실패
3. 로컬 파일 (LOCAL_KB_PATH) → 키워드 검색
```

---

## 🎬 데모 시나리오

### 시나리오 1: 프로젝트 가이드 챗봇

로컬 환경 실행 후 다음 질문을 해보세요:

| 질문 | 예상 응답 |
|------|----------|
| "어떻게 시작해요?" | 설치 및 실행 방법 안내 |
| "Agent 어떻게 만들어요?" | Agent Builder 사용법 설명 |
| "프로젝트 구조 보여줘" | 디렉토리 구조 설명 |
| "AWS에 배포하려면?" | AWS 배포 가이드 안내 |

### 시나리오 2: Knowledge Base 활용

```bash
# 1. 새 문서 추가
cat > knowledge-base/devops/my-guide.md << 'EOF'
# 우리 팀 운영 가이드
서버 장애 시 담당자: 홍길동
에스컬레이션: 30분 내 팀장 보고
EOF

# 2. 질문하기
"서버 장애 시 누구한테 연락해야 해?"
→ Agent가 방금 추가한 문서를 검색하여 응답
```

### 시나리오 3: 새 Agent 생성

```bash
# Agent Builder 실행
kiro chat --agent agent-builder

# 요청
"비용 모니터링 Agent 만들어줘. AWS Cost Explorer 데이터 조회 기능으로"

# Agent Builder가 자동으로:
# 1. agents/cost_agent.py 생성
# 2. Supervisor에 연결
# 3. 테스트 방법 안내
```

---

## 🤖 Kiro CLI Agent 협업 워크플로

Agent Builder로 코드를 생성하면, Review Agent가 리뷰하고, Deployment Agent가 배포합니다.

```
┌─────────────────────────────────────────────────────────┐
│  kiro chat --agent agent-builder                        │
│                                                         │
│  "비용 모니터링 Agent 만들어줘"                         │
│           ↓                                             │
│  Agent Builder: 코드 생성                               │
│           ↓                                             │
│  "배포해줘" → delegate 워크플로 시작                    │
│           ↓                                             │
│  ┌─────────────────┐    ┌──────────────────────┐        │
│  │ Review Agent    │───▶│ Deployment Agent     │        │
│  │ 코드 리뷰       │    │ ECR → AgentCore 배포 │        │
│  │ (체크리스트 기반)│    │ (가이드 기반)        │        │
│  └─────────────────┘    └──────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

```bash
# Agent Builder (코드 생성 + delegate)
kiro chat --agent agent-builder

# Review Agent (코드 리뷰 단독 실행)
kiro chat --agent review

# Deployment Agent (배포 단독 실행)
kiro chat --agent deployment
```

→ Agent 정의 파일: `templates/local/*.json`
→ [배포 가이드: docs/deployment-guide.md](docs/deployment-guide.md)
→ [리뷰 체크리스트: docs/review-checklist.md](docs/review-checklist.md)

---

## 📁 프로젝트 구조

```
aiops-starter-kit/
├── templates/
│   ├── local/                    # 로컬 배포 템플릿
│   │   ├── setup.sh             # 원클릭 설치
│   │   ├── app.py               # Chainlit UI (로컬: 직접 호출, AWS: AgentCore API)
│   │   ├── config.py            # 모델/리전 설정
│   │   ├── feedback_store.py    # 피드백 저장 (로컬 JSON / DynamoDB / S3)
│   │   ├── Dockerfile.ui        # UI 전용 컨테이너 (Fargate 배포용)
│   │   ├── requirements-ui.txt  # UI 의존성
│   │   ├── agent-builder.json   # Kiro CLI Agent Builder
│   │   ├── review-agent.json    # Kiro CLI Review Agent
│   │   ├── deployment-agent.json # Kiro CLI Deployment Agent
│   │   └── agents/
│   │       ├── supervisor.py    # Multi-Agent 조율
│   │       ├── guide_agent.py   # 프로젝트 가이드 챗봇
│   │       ├── mcp_agent.py     # MCP 연동 예시 Agent
│   │       ├── case_tools.py    # 사례 저장 도구
│   │       ├── main.py          # AgentCore HTTP 서버
│   │       ├── Dockerfile       # AgentCore 컨테이너 (ARM64)
│   │       └── requirements.txt # Agent 의존성
│   │
│   └── aws/                      # AWS 배포 템플릿 (Hybrid Architecture)
│       ├── deploy.sh            # 3개 스택 배포 스크립트
│       └── cdk/
│           └── stacks/
│               ├── infrastructure_stack.py  # ECR, IAM, KMS, KB, S3 Vectors
│               ├── agentcore_stack.py       # Runtime, Memory
│               └── ui_stack.py              # Fargate + Chainlit UI
│
├── knowledge-base/               # 로컬 Knowledge Base
│   ├── common/                  # 공통 지식
│   ├── devops/                  # DevOps 가이드
│   ├── analytics/               # Analytics 가이드
│   └── monitoring/              # Monitoring 가이드
│
├── src/                          # PoC 구현 (게임 운영 시나리오, 참고용)
│   ├── agent/                   # Agent 구현 예시
│   └── tools/                   # 도구 구현 예시
│
├── tests/                        # 테스트
│   ├── test_kb_tools.py         # KB 도구 테스트
│   └── test_guide_agent.py      # Guide Agent 테스트
│
└── docs/                         # 문서
    ├── QUICKSTART-LOCAL.md      # 로컬 배포 가이드
    ├── QUICKSTART-AWS.md        # AWS 배포 가이드
    ├── deployment-guide.md      # Agent 배포 절차
    └── review-checklist.md      # 코드 리뷰 체크리스트
```

---

## 📚 문서

| 문서 | 설명 | 소요 시간 |
|------|------|----------|
| [QUICKSTART-LOCAL.md](docs/QUICKSTART-LOCAL.md) | 로컬 환경 빠른 시작 | 5분 |
| [QUICKSTART-AWS.md](docs/QUICKSTART-AWS.md) | AWS AgentCore 배포 | 30분 |
| [TUTORIAL-FIRST-AGENT.md](docs/TUTORIAL-FIRST-AGENT.md) | 자연어로 첫 Agent 만들기 | 30분 |
| [TUTORIAL-FEEDBACK.md](docs/TUTORIAL-FEEDBACK.md) | 피드백 루프 설정 | 20분 |
| [TUTORIAL-MULTI-AGENT.md](docs/TUTORIAL-MULTI-AGENT.md) | Multi-Agent 구성 | 30분 |
| [BEST-PRACTICES.md](docs/BEST-PRACTICES.md) | 실패 사례와 교훈 | 15분 |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | 문제 해결 가이드 | - |
| [deployment-guide.md](docs/deployment-guide.md) | Agent 배포 절차 (ECR/AgentCore) | 15분 |
| [review-checklist.md](docs/review-checklist.md) | Agent 코드 리뷰 체크리스트 | 10분 |
| [TUTORIAL-MCP-AGENT.md](docs/TUTORIAL-MCP-AGENT.md) | MCP 연동 Agent 만들기 | 30분 |
| [TUTORIAL-NEWS-AGENT.md](docs/TUTORIAL-NEWS-AGENT.md) | 뉴스 Agent 시나리오 (Agent Builder 활용) | 30분 |

---

## 🧪 테스트

```bash
# 테스트 실행
source .venv/bin/activate
pytest tests/ -v

# 15개 테스트 항목:
# - KB 로컬 폴백 동작
# - Agent 검색 기능
# - 문서 저장 기능
```

→ [테스트 가이드: tests/README.md](tests/README.md)

---

## 점진적 도입 로드맵

### Phase 0: 환경 준비 (1일)
```
저장소 클론 → 의존성 설치 → 샘플 Agent 실행
```

### Phase 1: 첫 번째 Agent (1-2일)
```
가장 단순한 업무 선정 → Agent Builder로 생성 → 테스트
```
→ [TUTORIAL-FIRST-AGENT.md](docs/TUTORIAL-FIRST-AGENT.md)

### Phase 2: 피드백 루프 (1일)
```
피드백 수집 설정 → 1주일 축적 → 패턴 분석 → 개선
```
→ [TUTORIAL-FEEDBACK.md](docs/TUTORIAL-FEEDBACK.md)

### Phase 3: 기능 확장 (1-2주)
```
같은 영역 도구 추가 → 테스트 → 안정화
```

### Phase 4: Multi-Agent (1주)
```
두 번째 Agent 추가 → Supervisor 연결 → 협업 테스트
```
→ [TUTORIAL-MULTI-AGENT.md](docs/TUTORIAL-MULTI-AGENT.md)

### Phase 5: 지속적 개선
```
피드백 분석 → Agent Builder로 개선 → 반복
```

---

## 핵심 원칙

```
"코드를 직접 작성하지 마세요. Agent Builder에게 시키세요."

1. 작게 시작 - 가장 단순한 기능 하나로
2. 피드백 먼저 - 피드백 없이 추측하지 않기
3. 점진적 확장 - 한 번에 완벽하려 하지 않기
4. 테스트 필수 - 테스트 없이 배포하지 않기
```

---

## 프로젝트 구조

```
ai-agent-platform/
├── app.py                      # Chainlit UI (PoC용)
├── logs_api.py                 # 로그/피드백 API (PoC용)
├── src/                        # PoC 구현 (게임 운영 시나리오)
│   ├── agent/
│   │   ├── supervisor_agent.py # Supervisor
│   │   ├── devops_agent.py     # DevOps Agent (예시)
│   │   └── analytics_agent.py  # Analytics Agent (예시)
│   ├── tools/
│   │   └── *.py                # 도구 모음
│   └── utils/
│       └── execution_logger.py # 실행 로그
├── context_rule/
│   └── agent-builder-guide.md  # Agent Builder 가이드
├── docs/                       # 문서
└── infra/                      # CDK/Terraform
```

---

## PoC 예시: 게임 운영 Agent

이 저장소에는 게임 운영 시나리오의 PoC가 포함되어 있습니다.

| Agent | 도구 | 담당 영역 |
|-------|------|----------|
| DevOps | 6개 | CloudWatch, EC2, 장애 티켓 |
| Analytics | 10개 | DAU, 가챠 확률, 재화 흐름 |
| Godot Review | 5개 | GDScript 코드 리뷰 |
| Monitoring | 3개 | CloudWatch 알람 현황, 추이 분석, 이슈 리포팅 |

```bash
# 테스트
chainlit run app.py

# 질문 예시
"장애 티켓 목록 보여줘"
"가챠 등급별 확률 분석해줘"
"알람 현황 확인해줘"
"알람 분석해서 이슈 리포팅해줘"
```

---

## 로드맵

### v1.0 - 기본 템플릿 ✅
- [x] Multi-Agent 협업 구조
- [x] 실행 기록 저장
- [x] CDK/Terraform 배포

### v1.1 - 피드백 수집 ✅
- [x] 👍/👎 피드백 버튼
- [x] 피드백 저장 및 조회

### v1.2 - Agent Builder Agent ✅
- [x] 자연어로 Agent 생성
- [x] 기존 Agent 수정
- [x] KB 연동 패턴

### v1.3 - 자동 개선 제안 ✅
- [x] 부정 피드백 분석 도구
- [x] 개선 제안 자동화

### v1.4 - Kiro CLI Agent 체계화 ✅
- [x] deployment-agent (배포 전문)
- [x] review-agent (코드 리뷰 전문)
- [x] agent-builder 개선 (delegate 패턴)
- [x] Agent 간 위임 워크플로 (review → deployment)

### v1.5 - MCP 연동 지원 ✅
- [x] MCP 연동 예시 Agent (AWS Docs MCP Server)
- [x] TUTORIAL-MCP-AGENT.md
- [x] Agent Builder MCP 패턴 지원

### v1.6 - Template UI 개선 ✅
- [x] 추론 과정 표시 (Strands Hooks → ToolCallTracker)
- [x] 피드백 버튼 (cl.Action → 로컬 JSON / AWS DynamoDB)
- [x] 동적 환영 메시지 (supervisor의 ask_*_agent 자동 감지)
- [x] 뉴스 Agent 시나리오 + 튜토리얼

### v2.0 - 자동화 워크플로우 (예정)
- [ ] 스케줄러 (정기 분석)
- [ ] 알림 연동 (Slack/이메일)

---

## 기여 방법

1. 이슈 등록 또는 기존 이슈 확인
2. Fork 후 feature 브랜치 생성
3. 변경사항 커밋
4. Pull Request 생성

---

## 라이선스

MIT License

---

# English Version

## What is this project?

**A platform for creating AI Agents with natural language and improving them incrementally.**

Key features:
- **No-code Agent creation**: Request Agent Builder in natural language
- **Incremental improvement**: Auto-improve Agents based on feedback
- **Multi-Agent collaboration**: Multiple specialist Agents working together

---

## Quick Start

### 1. Setup (10 min)

```bash
git clone https://github.com/hcsung-aws/ai-agent-automation-platform.git
cd ai-agent-automation-platform

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Sample Agent (5 min)

```bash
chainlit run app.py --port 8000
```

### 3. Create Your Own Agent (15 min)

```bash
kiro chat --agent agent-builder
```

```
"Create a Monitoring Agent that queries CloudWatch alarms"
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](docs/QUICKSTART.md) | Quick start guide |
| [TUTORIAL-FIRST-AGENT.md](docs/TUTORIAL-FIRST-AGENT.md) | Create first Agent with natural language |
| [TUTORIAL-FEEDBACK.md](docs/TUTORIAL-FEEDBACK.md) | Setup feedback loop |
| [TUTORIAL-MULTI-AGENT.md](docs/TUTORIAL-MULTI-AGENT.md) | Multi-Agent configuration |
| [BEST-PRACTICES.md](docs/BEST-PRACTICES.md) | Failure cases and lessons |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | AWS deployment guide |

---

## Core Principle

```
"Don't write code yourself. Ask Agent Builder to do it."

1. Start small - One simple function first
2. Feedback first - Don't guess without feedback
3. Incremental expansion - Don't try to be perfect at once
4. Test required - Don't deploy without testing
```

---

## Roadmap

### v1.0 - Basic Template ✅
### v1.1 - Feedback Collection ✅
### v1.2 - Agent Builder Agent ✅
### v1.3 - Auto Improvement Suggestions ✅
### v1.4 - Kiro CLI Agent Orchestration ✅
### v1.5 - MCP Integration ✅
### v1.6 - Template UI Improvements ✅
### v2.0 - Automation Workflow (Planned)

---

## License

MIT License
