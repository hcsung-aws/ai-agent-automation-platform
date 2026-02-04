# AI Agent 기반 업무 자동화 플랫폼

[English](#english-version) | 한국어

## 이 프로젝트는 무엇인가요?

**자연어로 AI Agent를 만들고 점진적으로 개선하는 플랫폼**입니다.

핵심 특징:
- **코드 없이 Agent 생성**: Agent Builder에게 자연어로 요청
- **점진적 개선**: 피드백 기반으로 Agent 자동 개선
- **Multi-Agent 협업**: 여러 전문 Agent가 협업

```
사용자: "HR Agent 만들어줘. 휴가 조회 기능으로"
    ↓
Agent Builder가 자동으로 코드 생성
    ↓
테스트 → 피드백 → 개선 요청
    ↓
점점 똑똑해지는 Agent
```

---

## 빠른 시작

### 1. 환경 설정 (10분)

```bash
git clone https://github.com/hcsung-aws/ai-agent-automation-platform.git
cd ai-agent-automation-platform

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 샘플 Agent 실행 (5분)

```bash
chainlit run app.py --port 8000
```

브라우저에서 `http://localhost:8000` 접속

### 3. 나만의 Agent 만들기 (15분)

Agent Builder 실행:
```bash
kiro chat --agent agent-builder
```

자연어로 요청:
```
"CloudWatch 알람을 조회하는 Monitoring Agent 만들어줘"
```

Agent Builder가 단계별로 안내합니다:
- 처음 1-2개 핵심 기능으로 시작 권장
- 테스트 데이터로 먼저 동작 확인
- 테스트 후 실제 API 연동

상세 가이드: [docs/QUICKSTART.md](docs/QUICKSTART.md)

---

## 문서 구조

| 문서 | 설명 | 소요 시간 |
|------|------|----------|
| [QUICKSTART.md](docs/QUICKSTART.md) | 빠른 시작 가이드 | 30분 |
| [TUTORIAL-FIRST-AGENT.md](docs/TUTORIAL-FIRST-AGENT.md) | 자연어로 첫 Agent 만들기 | 30분 |
| [TUTORIAL-FEEDBACK.md](docs/TUTORIAL-FEEDBACK.md) | 피드백 루프 설정 | 20분 |
| [TUTORIAL-MULTI-AGENT.md](docs/TUTORIAL-MULTI-AGENT.md) | Multi-Agent 구성 | 30분 |
| [BEST-PRACTICES.md](docs/BEST-PRACTICES.md) | 실패 사례와 교훈 | 15분 |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | AWS 배포 가이드 | 1시간 |

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
