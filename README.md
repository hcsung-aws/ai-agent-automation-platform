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

## 📁 프로젝트 구조

```
aiops-starter-kit/
├── templates/
│   ├── local/                    # 로컬 배포 템플릿
│   │   ├── setup.sh             # 원클릭 설치
│   │   ├── app.py               # Chainlit UI
│   │   ├── agent-builder.json   # Kiro CLI 연동
│   │   └── agents/
│   │       ├── supervisor.py    # Multi-Agent 조율
│   │       └── guide_agent.py   # 프로젝트 가이드 챗봇
│   │
│   └── aws/                      # AWS 배포 템플릿
│       ├── deploy.sh            # 배포 스크립트
│       └── cdk/
│           └── stacks/
│               ├── infrastructure_stack.py  # ECR, IAM, KMS
│               └── agentcore_stack.py       # Runtime, Gateway, Memory
│
├── knowledge-base/               # 로컬 Knowledge Base
│   ├── common/                  # 공통 지식
│   ├── devops/                  # DevOps 가이드
│   ├── analytics/               # Analytics 가이드
│   └── monitoring/              # Monitoring 가이드
│
├── src/                          # PoC 구현 (참고용)
│   ├── agent/                   # Agent 구현 예시
│   └── tools/                   # 도구 구현 예시
│
├── tests/                        # 테스트
│   ├── test_kb_tools.py         # KB 도구 테스트
│   └── test_guide_agent.py      # Guide Agent 테스트
│
└── docs/                         # 문서
    ├── QUICKSTART-LOCAL.md      # 로컬 배포 가이드
    └── QUICKSTART-AWS.md        # AWS 배포 가이드
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
├── app.py                      # Chainlit UI
├── logs_api.py                 # 로그/피드백 API
├── src/
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
### v2.0 - Automation Workflow (Planned)

---

## License

MIT License
