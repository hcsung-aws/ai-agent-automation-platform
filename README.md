# AI Agent 기반 업무 자동화 플랫폼

[English](#english-version) | 한국어

## 프로젝트 비전

조직의 업무 프로세스를 AI Agent 기반으로 점진적으로 자동화하는 플랫폼입니다.

### 핵심 아이디어

```
┌─────────────────────────────────────────────────────────────────┐
│                    점진적 자동화 사이클                           │
│                                                                 │
│   1. 사람이 Agent에게 업무 지시                                  │
│          ↓                                                      │
│   2. Agent가 도구를 활용하여 업무 수행                           │
│          ↓                                                      │
│   3. 실행 기록 저장 및 사람의 검토                               │
│          ↓                                                      │
│   4. 검토 결과를 Knowledge Base/지침/도구로 반영                 │
│          ↓                                                      │
│   5. 개선된 Agent가 더 나은 업무 수행 (1번으로 반복)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 왜 이 방식인가?

| 기존 자동화 | Agent 기반 자동화 |
|------------|------------------|
| 모든 케이스를 미리 정의 | 자연어로 유연하게 지시 |
| 변경 시 코드 수정 필요 | Knowledge Base 업데이트로 대응 |
| 예외 상황 처리 어려움 | LLM이 맥락 파악하여 판단 |
| 초기 구축 비용 높음 | 점진적으로 확장 가능 |

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                      Chainlit UI (챗봇)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                   Supervisor Agent                               │
│              (요청 분석 및 전문가 Agent 위임)                     │
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐              │
│  │   DevOps Agent   │         │ Analytics Agent  │              │
│  │                  │         │                  │              │
│  │ • CloudWatch     │         │ • Athena 쿼리    │              │
│  │ • EC2 상태       │         │ • 가챠 분석      │              │
│  │ • 배포 이력      │         │ • 재화 흐름      │              │
│  │ • 장애 티켓      │         │ • 유저 리텐션    │              │
│  │ • KB 검색        │         │ • 퀘스트/출석    │              │
│  └──────────────────┘         └──────────────────┘              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      AWS Services                                │
│                                                                  │
│  Bedrock (LLM)  │  DynamoDB  │  S3  │  Athena  │  CloudWatch    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 빠른 시작

### 사전 요구사항

- Python 3.10+
- AWS CLI 설정 완료 (Bedrock 접근 권한 필요)
- AWS 계정 (us-east-1 리전)

### 로컬 환경 설치

```bash
# 1. 저장소 클론
git clone https://github.com/your-org/ai-agent-platform.git
cd ai-agent-platform

# 2. 가상환경 설정
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. AWS 인프라 배포 (CDK 또는 Terraform 선택)
cd infra
cdk deploy  # 또는: cd terraform && terraform apply

# 5. 샘플 데이터 생성
cd ..
python scripts/setup_mmorpg_tables.py

# 6. Agent 실행
chainlit run app.py
```

브라우저에서 `http://localhost:8000` 접속

### AWS 환경 배포

상세 가이드: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

```bash
# CDK 배포
cd infra && cdk deploy

# 또는 Terraform 배포
cd infra/terraform && terraform init && terraform apply
```

> **Note**: Knowledge Base는 콘솔에서 수동 생성 필요 (S3 Vectors 타입)

---

## 사용 방법

### 1단계: 기본 사용

Agent에게 자연어로 업무를 지시합니다.

```
사용자: "현재 장애 티켓 목록 보여줘"
Agent: DevOps Agent에게 위임 → 티켓 목록 조회 → 결과 반환

사용자: "오늘 가챠 확률 분석해줘"
Agent: Analytics Agent에게 위임 → Athena 쿼리 실행 → 분석 결과 반환
```

### 2단계: 실행 기록 검토

모든 Agent 실행은 자동으로 기록됩니다.

```bash
# 로그 조회 API 실행
python logs_api.py
# http://localhost:8001 에서 확인
```

저장되는 정보:
- 사용자 입력
- Agent 응답
- 사용된 도구
- 실행 시간
- 성공/실패 여부

### 3단계: Knowledge Base 개선

Agent가 잘못된 답변을 하거나 더 나은 방법이 있다면:

1. **운영 가이드 추가**: `docs/kb/` 폴더에 마크다운 문서 추가
2. **KB 동기화**: Bedrock 콘솔에서 Data Source Sync 실행
3. **Agent가 새 지식 활용**: `search_operations_guide` 도구로 검색

예시 - 장애 대응 가이드 추가:
```markdown
# docs/kb/incident-response-guide.md

## CPU 사용률 급증 시 대응

1. CloudWatch에서 해당 인스턴스 메트릭 확인
2. 프로세스별 CPU 사용량 확인: `top -c`
3. 원인 프로세스 식별 후 조치
4. 장애 티켓 생성 및 기록
```

### 4단계: 도구 확장

새로운 업무 영역이 필요하면 도구를 추가합니다.

```python
# src/tools/new_tools.py
from strands import tool

@tool
def my_new_tool(param: str) -> str:
    """새로운 도구 설명 (Agent가 이 설명을 보고 도구 선택)
    
    Args:
        param: 파라미터 설명
    
    Returns:
        결과 설명
    """
    # 구현
    return result
```

---

## 점진적 개선 가이드

### Phase 1: 도입기 (현재)

**목표**: Agent 기본 동작 확인 및 팀 적응

| 활동 | 설명 |
|------|------|
| 기본 질문 테스트 | 간단한 조회 업무부터 시작 |
| 실행 기록 검토 | 주 1회 로그 검토하여 개선점 파악 |
| KB 문서 작성 | 자주 묻는 질문에 대한 가이드 추가 |

**주의사항**:
- Agent 응답을 맹신하지 말고 검증 필요
- 중요한 작업(티켓 생성 등)은 확인 후 실행
- 민감한 정보는 KB에 포함하지 않기

### Phase 2: 확장기

**목표**: 업무 범위 확대 및 자동화 수준 향상

| 활동 | 설명 |
|------|------|
| 새 도구 추가 | 반복 업무를 도구로 구현 |
| 지침 고도화 | System Prompt에 업무 규칙 추가 |
| 복합 시나리오 | 여러 Agent 협업 시나리오 구현 |

### Phase 3: 자동화기

**목표**: 사람 개입 최소화

| 활동 | 설명 |
|------|------|
| 스케줄 실행 | 정기 리포트 자동 생성 |
| 알림 연동 | Slack/이메일 알림 추가 |
| 승인 워크플로우 | 중요 작업은 사람 승인 후 실행 |

---

## 프로젝트 구조

```
ai-agent-platform/
├── app.py                      # Chainlit UI 진입점
├── logs_api.py                 # 실행 기록 조회 API
├── src/
│   ├── agent/
│   │   ├── supervisor_agent.py # Supervisor (Multi-Agent 조율)
│   │   ├── devops_agent.py     # DevOps 전문가
│   │   └── analytics_agent.py  # 데이터 분석 전문가
│   ├── tools/
│   │   ├── cloudwatch_tools.py # CloudWatch 메트릭
│   │   ├── ec2_tools.py        # EC2 상태
│   │   ├── ticket_tools.py     # 장애 티켓
│   │   ├── athena_tools.py     # Athena 쿼리
│   │   └── mmorpg_analytics.py # MMORPG 분석
│   └── utils/
│       └── execution_logger.py # 실행 기록
├── scripts/
│   └── setup_mmorpg_tables.py  # 샘플 데이터 생성
├── infra/
│   ├── stacks/                 # CDK 스택
│   └── terraform/              # Terraform 설정
└── docs/
    ├── DEPLOYMENT.md           # 배포 가이드
    └── kb/                     # Knowledge Base 문서
```

---

## 로드맵

### v1.0 (현재) - PoC 완료
- [x] DevOps Agent (6개 도구)
- [x] Analytics Agent (10개 도구)
- [x] Multi-Agent 협업 (Supervisor)
- [x] 실행 기록 저장
- [x] CDK/Terraform 배포 스크립트

### v1.1 - 검토 기능 강화
- [ ] 실행 기록 검토 UI 개선
- [ ] 피드백 수집 기능 (좋아요/싫어요)
- [ ] 피드백 기반 KB 문서 제안

### v1.2 - 자동 개선
- [ ] 실행 패턴 분석
- [ ] 자주 실패하는 케이스 리포트
- [ ] System Prompt 개선 제안

### v2.0 - 프로덕션
- [ ] 인증/권한 관리
- [ ] 멀티 테넌트 지원
- [ ] AgentCore 런타임 배포
- [ ] A2A 프로토콜 연동

---

## 기여 방법

1. 이슈 등록 또는 기존 이슈 확인
2. Fork 후 feature 브랜치 생성
3. 변경사항 커밋
4. Pull Request 생성

---

## 라이선스

Internal Use Only

---

# English Version

## Project Vision

A platform for gradually automating organizational workflows using AI Agents.

### Core Concept

```
┌─────────────────────────────────────────────────────────────────┐
│                 Gradual Automation Cycle                         │
│                                                                 │
│   1. Human instructs Agent on tasks                             │
│          ↓                                                      │
│   2. Agent performs tasks using tools                           │
│          ↓                                                      │
│   3. Execution logs saved & reviewed by humans                  │
│          ↓                                                      │
│   4. Feedback reflected in KB/guidelines/tools                  │
│          ↓                                                      │
│   5. Improved Agent performs better (repeat from 1)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- AWS CLI configured (Bedrock access required)
- AWS Account (us-east-1 region)

### Local Installation

```bash
# 1. Clone repository
git clone https://github.com/your-org/ai-agent-platform.git
cd ai-agent-platform

# 2. Setup virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Deploy AWS infrastructure
cd infra && cdk deploy

# 5. Generate sample data
cd .. && python scripts/setup_mmorpg_tables.py

# 6. Run Agent
chainlit run app.py
```

Access `http://localhost:8000` in browser.

### AWS Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed guide.

## Usage

### Basic Usage

Instruct the Agent in natural language:

```
User: "Show me current incident tickets"
Agent: Delegates to DevOps Agent → Queries tickets → Returns results

User: "Analyze today's gacha rates"
Agent: Delegates to Analytics Agent → Runs Athena query → Returns analysis
```

### Improving Knowledge Base

When Agent gives incorrect answers or better methods exist:

1. Add markdown docs to `docs/kb/`
2. Sync Data Source in Bedrock console
3. Agent uses new knowledge via `search_operations_guide`

### Adding New Tools

```python
from strands import tool

@tool
def my_new_tool(param: str) -> str:
    """Tool description (Agent reads this to select tools)"""
    return result
```

## Roadmap

### v1.0 (Current) - PoC Complete
- [x] DevOps Agent (6 tools)
- [x] Analytics Agent (10 tools)
- [x] Multi-Agent collaboration
- [x] Execution logging
- [x] CDK/Terraform deployment

### v1.1 - Enhanced Review
- [ ] Improved log review UI
- [ ] Feedback collection (like/dislike)
- [ ] KB document suggestions

### v2.0 - Production
- [ ] Authentication/Authorization
- [ ] Multi-tenant support
- [ ] AgentCore runtime deployment

## License

Internal Use Only
