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

> ### 📖 이 프로젝트는 **학습용**입니다
>
> 이 프로젝트는 Agentic AIOps를 빠르게 시작하고 개선해 나가는 방법에 대한 **아이디어를 얻기 위한 학습 자료**입니다.
>
> **왜 학습용인가요?**
>
> 1. **AI 기술은 매우 빠르게 발전합니다.** 이 프로젝트의 내용을 참고하여 구현하더라도, 곧 더 나은 기술과 방법이 등장할 수 있습니다. 특정 구현에 고정되기보다 변화에 유연하게 대응하는 것이 중요합니다.
>
> 2. **이 프로젝트가 추구하는 방향:**
>    - 내부에서 **빠르게 아이디어를 검증**하면서 AI Agent 활용 방법을 파악하는 것
>    - 간단한 아이디어나 반복 작업에 **AI를 빠르게 적용**하여 업무 효율을 높이는 것
>
> 즉, 이 프로젝트의 내용을 그대로 따라 하라는 것이 아니라, **"AI Agent로 이런 것도 할 수 있구나"** 하는 감각을 익히고, 각자의 환경에 맞게 응용하시길 바랍니다.

---

## 🚀 빠른 시작

### 로컬 환경 - Docker (권장, 3분)

```bash
git clone https://github.com/hcsung-aws/ai-agent-automation-platform.git
cd ai-agent-automation-platform/templates/local
cp .env.example .env        # 환경변수 설정
touch feedback.json          # 피드백 저장 파일
docker compose up -d
```

브라우저에서 http://localhost:8000 접속

> Docker 없이 실행하려면 venv 방식을 사용하세요:
> ```bash
> ./setup.sh && source .venv/bin/activate && chainlit run app.py --port 8000
> ```

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
- **멀티모달 출력**: Agent가 생성한 이미지(차트, 메트릭 등)를 인라인 렌더링 (사이드채널 + 마크다운 이미지)

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

```bash
# UI 접속 (SSM 포트포워딩)
./scripts/ssm-port-forward.sh us-west-2 8000
# → http://localhost:8000 으로 접속
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
│   │   ├── docker-compose.yml   # Docker 원클릭 실행 (권장)
│   │   ├── Dockerfile.local     # 로컬 All-in-One 컨테이너
│   │   ├── setup.sh             # venv 설치 (Docker 없을 때)
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
│   │       ├── media_utils.py   # 멀티모달 출력 유틸리티 (사이드채널)
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
├── scripts/                      # 유틸리티 스크립트
│   └── ssm-port-forward.sh     # SSM 포트포워딩 (ECS UI 접속)
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

## 📦 PoC 참고: 게임 운영 Agent

> `src/` 디렉토리에 게임 운영 시나리오의 PoC가 포함되어 있습니다. 이 프로젝트의 출발점이었으며, 현재 템플릿(`templates/`)은 이 PoC의 교훈을 반영하여 재설계한 것입니다.

| Agent | 도구 | 담당 영역 |
|-------|------|----------|
| DevOps | 6개 | CloudWatch, EC2, 장애 티켓 |
| Analytics | 10개 | DAU, 가챠 확률, 재화 흐름 |
| Monitoring | 3개 | CloudWatch 알람 현황, 추이 분석, 이슈 리포팅 |

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

### v1.7 - 멀티모달 출력 지원 ✅
- [x] 사이드채널 유틸리티 (media_utils.py: add_image/flush)
- [x] 마크다운 이미지 추출 + cl.Image 인라인 렌더링
- [x] Agent Builder 멀티모달 패턴 통합 (URL 이미지 + 생성 이미지)

### v2.0 - 자동화 워크플로우 (예정)
- [ ] 스케줄러 (정기 분석)
- [ ] 알림 연동 (Slack/이메일)

---

## 💡 개발 교훈

이 프로젝트를 32세션에 걸쳐 AI와 협업하며 개발하면서 얻은 핵심 교훈입니다.

→ [상세 사례: BEST-PRACTICES.md](docs/BEST-PRACTICES.md)

### Agent 설계

| 교훈 | 설명 |
|------|------|
| **LLM 응답에 메타데이터를 의존하지 마세요** | LLM은 "중요하지 않다"고 판단한 내용을 생략합니다. 테스트 모드 표시, 상태 플래그 등은 코드 레벨에서 관리하세요. |
| **도구 설명이 곧 Agent의 판단 기준입니다** | 모호한 docstring은 도구 미호출로 이어집니다. "언제, 왜" 사용하는지 명시하세요. |
| **Multi-Agent에서 URL/링크가 소실됩니다** | Sub-Agent → Supervisor 2단계 요약 시 URL이 "링크 참고"로 축약됩니다. 각 계층 SYSTEM_PROMPT에 "링크 보존" 원칙을 명시하세요. |
| **KB 검색은 단어 단위 매칭이 필수입니다** | 전체 문자열 매칭(`query in content`)은 LLM이 생성하는 자연어 query와 매칭 실패합니다. 단어 단위로 분리하여 키워드 매칭하세요. |

### AWS 배포

| 교훈 | 설명 |
|------|------|
| **AgentCore Runtime은 HTTP 서버입니다** | Lambda 핸들러가 아닙니다. FastAPI + uvicorn으로 `POST /invocations` + `GET /ping`을 구현하세요. |
| **AgentCore는 ARM64 전용입니다** | x86_64 이미지로 배포하면 실패합니다. Dockerfile에 `--platform=linux/arm64`를 추가하세요. |
| **IAM에 inference-profile 권한이 필요합니다** | `foundation-model/*`만 허용하면 AccessDeniedException이 발생합니다. `inference-profile/*`도 추가하세요. |
| **S3 Vectors가 CDK 자동화에 유리합니다** | OpenSearch Serverless는 vector index가 CloudFormation 미지원이라 Custom Resource Lambda가 필요합니다. |
| **KMS + CloudWatch Logs는 키 정책 확인 필수** | KMS 키 정책에 CloudWatch Logs 서비스 권한이 없으면 암호화된 LogGroup 생성이 실패합니다. |

### Chainlit UI

| 교훈 | 설명 |
|------|------|
| **Strands Agent 호출은 `asyncio.to_thread` 필수** | async 함수 안에서 동기 호출하면 이벤트 루프가 블록되어 WebSocket이 끊깁니다. |
| **피드백 버튼은 Data Layer 없이 동작하지 않습니다** | `@cl.on_feedback`은 Data Layer가 필요합니다. PoC에서는 `cl.Action` 버튼으로 자체 구현하세요. |
| **cl.Image는 `content=bytes` 직접 전달이 안정적** | Docker 환경에서 tempfile + path 방식은 파일 서빙 이슈가 발생합니다. |
| **Python 이중 임포트로 모듈 상태가 공유되지 않습니다** | `media_utils`와 `agents.media_utils`는 별개 인스턴스입니다. PYTHONPATH 경유로 임포트 경로를 통일하세요. |

### 개발 프로세스

| 교훈 | 설명 |
|------|------|
| **프로토타입 → 검증 → 병합 사이클을 지키세요** | 새 기능은 `prototypes/`에서 먼저 검증하고, 통과 후 `templates/`에 병합합니다. |
| **Docker 빌드 시 build context 외부 파일을 확인하세요** | `agents/` 밖의 `config.py` 같은 파일이 누락되면 런타임 import 에러가 발생합니다. |
| **피드백과 사례는 보완 관계입니다** | 피드백(👍/👎)은 "뭘 고칠지" 신호, 사례는 "어떻게 해결했는지" 지식입니다. 둘 다 필요합니다. |

---

## 기여 방법

1. 이슈 등록 또는 기존 이슈 확인
2. Fork 후 feature 브랜치 생성
3. 변경사항 커밋
4. Pull Request 생성

---

## 🤖 이 프로젝트는 AI와 함께 만들었습니다

이 프로젝트는 [ai-developer-mickey](https://github.com/hcsung-aws/ai-developer-mickey) 시스템 프롬프트를 활용하여 AI 개발 에이전트와 협업하며 만들었습니다. 세션 간 컨텍스트 유지, 지식 누적, 점진적 개선 등의 방법론이 적용되어 있습니다.

---

## 라이선스

MIT License

---

# English Version

## What is this project?

**A platform for creating AI Agents with natural language and improving them incrementally.**

> ### 📖 This project is for **learning purposes**
>
> This project is a **learning resource** for getting ideas on how to quickly start and improve Agentic AIOps.
>
> **Why is it for learning?**
>
> 1. **AI technology evolves extremely fast.** Even if you build something based on this project, better technologies and approaches may emerge soon. It's more important to stay flexible than to lock into a specific implementation.
>
> 2. **What this project aims for:**
>    - **Quickly validate ideas** internally to understand how AI Agents can be utilized
>    - **Rapidly apply AI** to simple ideas and repetitive tasks to improve work efficiency
>
> In other words, this project is not meant to be followed exactly as-is. Rather, it's about developing a sense of **"Oh, AI Agents can do this too!"** and adapting it to your own environment.

Key features:
- **No-code Agent creation**: Request Agent Builder in natural language
- **Incremental improvement**: Auto-improve Agents based on feedback
- **Multi-Agent collaboration**: Multiple specialist Agents working together
- **Multimodal output**: Inline rendering of Agent-generated images (charts, metrics)

---

## Quick Start

### 1. Setup - Docker (Recommended, 3 min)

```bash
git clone https://github.com/hcsung-aws/ai-agent-automation-platform.git
cd ai-agent-automation-platform/templates/local
cp .env.example .env
touch feedback.json
docker compose up -d
```

Open http://localhost:8000 in your browser.

> Without Docker, use venv:
> ```bash
> ./setup.sh && source .venv/bin/activate && chainlit run app.py --port 8000
> ```

### 2. Create Your Own Agent

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
| [QUICKSTART-LOCAL.md](docs/QUICKSTART-LOCAL.md) | Local quick start guide |
| [QUICKSTART-AWS.md](docs/QUICKSTART-AWS.md) | AWS AgentCore deployment |
| [TUTORIAL-FIRST-AGENT.md](docs/TUTORIAL-FIRST-AGENT.md) | Create first Agent with natural language |
| [TUTORIAL-FEEDBACK.md](docs/TUTORIAL-FEEDBACK.md) | Setup feedback loop |
| [TUTORIAL-MULTI-AGENT.md](docs/TUTORIAL-MULTI-AGENT.md) | Multi-Agent configuration |
| [BEST-PRACTICES.md](docs/BEST-PRACTICES.md) | Failure cases and lessons |
| [deployment-guide.md](docs/deployment-guide.md) | Agent deployment procedure |

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
### v1.7 - Multimodal Output ✅
### v2.0 - Automation Workflow (Planned)

---

## License

MIT License
