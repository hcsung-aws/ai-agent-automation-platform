# AgentCore 기반 Multi-Agent 협업 시스템 계획서

## 1. 프로젝트 개요

### 목표
조직의 업무 프로세스를 AI Agent 기반으로 전환하는 플랫폼 구축

### 핵심 가치
- **점진적 학습**: 사용할수록 똑똑해지는 Agent
- **협업 자동화**: Agent 간 협업(A2A)으로 복잡한 업무 자동화
- **지속적 개선**: 실행 기록 기반 사람의 피드백 → Agent 개선

### 조직 컨텍스트
- 온라인 수집형 게임 개발사
- 여러 게임 퍼블리싱 및 인프라 관리
- 초기 대상: DevOps팀 (우선), 데이터분석팀

### 구현 원칙
- **실제 AWS 연동**: 시뮬레이션 없이 실제 서비스 연동
- **DevOps Agent 우선**: 첫 번째 Agent 완성 후 확장

---

## 2. 요구사항 분석

### 2.1 핵심 요구사항 vs AgentCore 기능 매핑

| 요구사항 | AgentCore 기능 | 커스텀 필요 |
|---------|---------------|------------|
| 개별 Agent 챗봇 | AgentCore Runtime | ❌ |
| A2A 협업 | Multi-Agent Collaboration (Supervisor) | ❌ |
| 지식 RAG | Bedrock Knowledge Bases 연동 | ❌ |
| 행동 패턴 → 지침 자동 생성 | AgentCore Memory + 커스텀 로직 | ✅ |
| 실행 기록 및 검토 | AgentCore Observability + 커스텀 저장소 | ✅ |
| 도구 자동 분석/업데이트 제안 | AgentCore Gateway + 커스텀 분석 | ✅ |
| 오케스트레이터 | Bedrock Agents Supervisor Mode | ❌ |

### 2.2 결론
**AgentCore가 기본 프레임워크로 적합**. 커스텀 레이어 3개 추가 필요:
1. 행동 패턴 분석 및 지침 생성 모듈
2. 실행 기록 저장 및 검토 UI
3. 도구 분석 및 업데이트 제안 모듈

---

## 3. 아키텍처 설계

### 3.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                         사용자 인터페이스                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │ 챗봇 UI      │  │ 관리 대시보드 │  │ 실행 기록 검토 UI        │   │
│  │ (Streamlit)  │  │ (React)      │  │ (React)                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AgentCore Layer (AWS)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │ AgentCore    │  │ AgentCore    │  │ AgentCore                │   │
│  │ Runtime      │  │ Memory       │  │ Observability            │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │ AgentCore    │  │ AgentCore    │  │ Bedrock Knowledge        │   │
│  │ Gateway      │  │ Identity     │  │ Bases                    │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      커스텀 레이어                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 행동 패턴 분석 모듈                                            │   │
│  │ - 실행 로그 분석 (AgentCore Observability → DynamoDB)         │   │
│  │ - 패턴 추출 및 지침 생성 (Bedrock Claude)                      │   │
│  │ - 지침 저장 및 버전 관리 (S3 + DynamoDB)                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 도구 분석 모듈                                                 │   │
│  │ - 사용 패턴 분석                                               │   │
│  │ - 도구 추가/제거 제안                                          │   │
│  │ - 업데이트 큐 관리                                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Agent 정의                                      │
│  ┌──────────────────────┐  ┌──────────────────────────────────────┐ │
│  │ DevOps Agent         │  │ 데이터분석 Agent                      │ │
│  │ - 인프라 모니터링    │  │ - 데이터 파이프라인 생성              │ │
│  │ - 배포 자동화        │  │ - 대시보드 생성                       │ │
│  │ - 장애 대응          │  │ - 분석 쿼리 실행                      │ │
│  └──────────────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      오케스트레이터                                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Supervisor Agent (Bedrock Multi-Agent Collaboration)         │   │
│  │ - 복잡한 요청 분해                                            │   │
│  │ - 적절한 Agent에 태스크 위임                                   │   │
│  │ - 결과 통합 및 응답                                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 데이터 흐름

```
[사용자 명령]
     │
     ▼
[챗봇 UI] ──────────────────────────────────────────┐
     │                                              │
     ▼                                              ▼
[AgentCore Runtime]                          [실행 기록 저장]
     │                                         (DynamoDB)
     ├─── 단순 요청 ──→ [개별 Agent]                │
     │                      │                      │
     └─── 복잡 요청 ──→ [Supervisor Agent]         │
                            │                      │
                            ▼                      │
                    [Multi-Agent 협업]             │
                            │                      │
                            ▼                      ▼
                    [결과 반환] ←───────── [행동 패턴 분석]
                            │                      │
                            ▼                      ▼
                    [사용자 응답]           [지침 업데이트 제안]
```

---

## 4. 기술 스택

### 4.1 AWS 서비스

| 서비스 | 용도 |
|-------|------|
| Bedrock AgentCore Runtime | Agent 실행 환경 |
| Bedrock AgentCore Memory | 세션/장기 메모리 |
| Bedrock AgentCore Observability | 실행 추적 및 디버깅 |
| Bedrock AgentCore Gateway | API/Lambda → Agent 도구 변환 |
| Bedrock AgentCore Identity | Agent 권한 관리 |
| Bedrock Knowledge Bases | RAG 지식 저장소 |
| Bedrock (Claude 3.5 Sonnet) | LLM 추론 |
| DynamoDB | 실행 기록, 지침, 메타데이터 저장 |
| S3 | 지식 문서, 지침 파일 저장 |
| Lambda | 커스텀 도구 구현 |
| API Gateway | 챗봇 API 엔드포인트 |
| CloudWatch | 로깅 및 모니터링 |

### 4.2 프레임워크

| 프레임워크 | 용도 |
|-----------|------|
| Strands Agents | Agent 개발 프레임워크 (AgentCore 호환) |
| Streamlit | 빠른 챗봇 UI 프로토타이핑 |
| CDK (Python) | 인프라 코드 |

---

## 5. 보안 고려사항

### 5.1 필수 보안 조치

| 영역 | 조치 |
|-----|------|
| IAM | 최소 권한 원칙, Agent별 역할 분리 |
| 데이터 | S3/DynamoDB 암호화 (KMS) |
| 네트워크 | VPC 내 배포 (AgentCore VPC-only 모드 - 추후) |
| 인증 | Cognito 사용자 인증 |
| 감사 | CloudTrail 활성화, 모든 Agent 실행 로깅 |
| 비밀 관리 | Secrets Manager (API 키 등) |

### 5.2 Agent 특화 보안

| 위험 | 대응 |
|-----|------|
| Prompt Injection | Guardrails 설정, 입력 검증 |
| 과도한 권한 | Agent별 도구 접근 제한 |
| 민감 정보 노출 | PII 마스킹, 출력 필터링 |
| 비용 폭주 | 토큰 사용량 제한, 알림 설정 |

---

## 6. 2주 PoC 로드맵 (수정)

### Week 1: DevOps Agent 완성

| 일차 | 작업 | 산출물 |
|-----|------|-------|
| Day 1 | CDK 프로젝트 설정 + IAM 역할 | 기본 인프라 코드 |
| Day 2 | DynamoDB 테이블 + S3 버킷 | 데이터 저장소 |
| Day 3 | DevOps Agent 도구 구현 (CloudWatch, EC2) | 핵심 도구 2개 |
| Day 4 | 추가 도구 (CloudFormation, 티켓) + Agent 코드 | 도구 4개 + Agent |
| Day 5 | AgentCore 배포 + Chainlit UI | 동작하는 DevOps Agent |

### Week 2: 확장 + 협업

| 일차 | 작업 | 산출물 |
|-----|------|-------|
| Day 6 | Knowledge Base 생성 + 문서 업로드 + Agent 연동 | RAG 연동 완료 |
| Day 7 | 데이터분석 Agent 도구 (Athena, QuickSight) | 두 번째 Agent |
| Day 8 | Supervisor Agent 구현 | Multi-Agent 협업 |
| Day 9 | 실행 기록 저장 로직 | 기록 저장 |
| Day 10 | 테스트 + 버그 수정 | PoC 완료 |

### PoC 완료 시 결과물

1. **DevOps Agent** (실제 AWS 연동)
   - CloudWatch 메트릭 조회
   - EC2 상태 조회
   - CloudFormation 스택 이벤트 조회
   - 장애 티켓 생성 (DynamoDB)
2. **데이터분석 Agent** (기본)
3. **Multi-Agent 협업** (Supervisor)
4. **Chainlit 챗봇 UI**
5. **실행 기록 저장**

---

## 7. 상세 구현 계획

### 7.1 DevOps Agent (우선 구현)

**역할**: 게임 인프라 모니터링 및 운영 자동화

**도구 (실제 AWS 연동)**:

| 도구 | 기능 | AWS 서비스 | 우선순위 |
|-----|------|-----------|---------|
| `get_cloudwatch_metrics` | 게임별 주요 메트릭 조회 | CloudWatch | Day 3 |
| `get_ec2_status` | EC2 인스턴스 상태 조회 | EC2 | Day 3 |
| `get_stack_events` | CloudFormation 스택 이벤트/배포 이력 | CloudFormation | Day 4 |
| `create_incident_ticket` | 장애 티켓 생성 | DynamoDB | Day 4 |

**도구 상세 스펙**:

```python
# 1. get_cloudwatch_metrics
@tool
def get_cloudwatch_metrics(
    game_name: str,           # 게임 이름 (태그 기반 필터)
    metric_name: str,         # CPUUtilization, NetworkIn, etc.
    period_minutes: int = 60  # 조회 기간
) -> str:
    """게임 인프라의 CloudWatch 메트릭 조회"""
    # boto3 cloudwatch.get_metric_statistics()

# 2. get_ec2_status
@tool
def get_ec2_status(
    game_name: str = None,    # 특정 게임 필터 (선택)
    instance_ids: list = None # 특정 인스턴스 (선택)
) -> str:
    """EC2 인스턴스 상태 조회"""
    # boto3 ec2.describe_instances()

# 3. get_stack_events
@tool
def get_stack_events(
    stack_name: str,          # CloudFormation 스택 이름
    limit: int = 10           # 최근 N개 이벤트
) -> str:
    """CloudFormation 스택 이벤트 조회 (배포 이력)"""
    # boto3 cloudformation.describe_stack_events()

# 4. create_incident_ticket
@tool
def create_incident_ticket(
    title: str,
    description: str,
    severity: str,            # low, medium, high, critical
    game_name: str
) -> str:
    """장애 티켓 생성 (DynamoDB 저장)"""
    # boto3 dynamodb.put_item()
```

**필요 IAM 권한**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/incident-tickets"
    }
  ]
}
```

**지식 베이스 (Week 2)**:
- 게임별 인프라 구성 문서
- 장애 대응 런북
- 배포 절차 문서

---

## 7.4 지식 관리 시스템 (Knowledge Base)

### 개요

사용자가 기존 지식 문서를 업로드하면 Agent가 참조할 수 있도록 **Bedrock Knowledge Bases**를 사용합니다.

### 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    지식 관리 흐름                         │
│                                                         │
│  [사용자]                                                │
│     │ 1. 문서 업로드                                     │
│     ▼                                                   │
│  ┌─────────────┐     2. 자동      ┌─────────────┐       │
│  │ S3 버킷     │ ──────────────→  │ Bedrock     │       │
│  │ (원본 문서)  │     인덱싱       │ Knowledge   │       │
│  └─────────────┘                  │ Base        │       │
│                                   └──────┬──────┘       │
│                                          │ 3. 검색      │
│                                          ▼              │
│                                   ┌─────────────┐       │
│                                   │ DevOps      │       │
│                                   │ Agent       │       │
│                                   └─────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### 지식 저장 위치

| 저장소 | 용도 | 경로 예시 |
|-------|------|----------|
| S3 버킷 | 원본 문서 저장 | `s3://devops-agent-kb-{account}/documents/` |
| Bedrock KB | 벡터 인덱스 (자동) | Bedrock 관리형 |

### 지원 문서 형식

Bedrock Knowledge Bases가 지원하는 형식:
- **텍스트**: `.txt`, `.md`, `.html`
- **문서**: `.pdf`, `.docx`
- **데이터**: `.csv`, `.json`

### 문서 업로드 방법

**방법 1: AWS 콘솔 (가장 쉬움)**
```
1. S3 콘솔 접속
2. devops-agent-kb-{account} 버킷 선택
3. documents/ 폴더에 파일 업로드
4. Bedrock 콘솔에서 "Sync" 클릭 (자동 인덱싱)
```

**방법 2: AWS CLI**
```bash
# 단일 파일 업로드
aws s3 cp 장애대응런북.md s3://devops-agent-kb-{account}/documents/

# 폴더 전체 업로드
aws s3 sync ./docs/ s3://devops-agent-kb-{account}/documents/

# Knowledge Base 동기화 트리거
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id {kb-id} \
  --data-source-id {ds-id}
```

**방법 3: Chainlit UI (PoC 이후 구현 예정)**
- 챗봇 UI에서 파일 드래그앤드롭
- 자동으로 S3 업로드 + KB 동기화

### 권장 문서 구조

```
documents/
├── runbooks/                    # 장애 대응 런북
│   ├── ec2-high-cpu.md
│   ├── rds-connection-issue.md
│   └── deployment-rollback.md
├── infrastructure/              # 인프라 구성
│   ├── toadstone-game-infra.md
│   └── network-topology.md
├── procedures/                  # 운영 절차
│   ├── deployment-process.md
│   └── scaling-guide.md
└── troubleshooting/             # 트러블슈팅 가이드
    ├── common-errors.md
    └── monitoring-alerts.md
```

### Agent가 지식을 참조하는 방식

Agent 코드에서 Knowledge Base 연동:

```python
from strands import Agent
from strands.tools import retrieve_from_knowledge_base

agent = Agent(
    model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    system_prompt="""당신은 DevOps 전문가입니다.
    질문에 답할 때 Knowledge Base에서 관련 문서를 검색하여 참고하세요.""",
    tools=[
        retrieve_from_knowledge_base,  # KB 검색 도구
        get_cloudwatch_metrics,
        get_ec2_status,
        # ...
    ],
    knowledge_base_id="{kb-id}"  # Knowledge Base 연결
)
```

사용자 질문 예시:
```
사용자: "EC2 CPU가 90% 넘으면 어떻게 대응해야 해?"

Agent 동작:
1. Knowledge Base에서 "EC2 CPU 대응" 검색
2. runbooks/ec2-high-cpu.md 문서 발견
3. 문서 내용 + LLM 추론으로 답변 생성
```

### 구현 일정

| 일차 | 작업 | 상세 |
|-----|------|------|
| Day 2 | S3 버킷 생성 | CDK로 KB용 버킷 생성 |
| Day 6 | Knowledge Base 생성 | Bedrock KB 설정, S3 연동 |
| Day 6 | 샘플 문서 업로드 | 테스트용 런북 3-4개 |
| Day 6 | Agent에 KB 연동 | retrieve 도구 추가 |

### 7.2 데이터분석 Agent (Week 2)

**역할**: 게임 데이터 분석 및 대시보드 생성

**도구 (실제 AWS 연동)**:

| 도구 | 기능 | AWS 서비스 |
|-----|------|-----------|
| `run_athena_query` | Athena 쿼리 실행 | Athena |
| `get_query_results` | 쿼리 결과 조회 | Athena |
| `list_dashboards` | QuickSight 대시보드 목록 | QuickSight |
| `get_game_kpis` | 게임별 KPI 조회 | Athena + 사전 정의 쿼리 |

**지식 베이스**:
- 데이터 스키마 문서
- 분석 쿼리 템플릿
- KPI 정의 문서

### 7.3 Supervisor Agent (Week 2)

**역할**: 복잡한 요청을 분해하여 적절한 Agent에 위임

**구현**: Bedrock Multi-Agent Collaboration (Supervisor Mode)

**예시 시나리오**:
```
사용자: "게임 A의 서버 상태 확인하고, 문제 있으면 최근 배포 이력도 확인해줘"

Supervisor 분해:
1. DevOps Agent → get_ec2_status(game_name="A")
2. 문제 발견 시 → get_stack_events(stack_name="game-a-stack")
3. 결과 통합 → 사용자 응답
```

---

## 8. 챗봇 UI 추천

### 옵션 비교

| 항목 | Streamlit | Chainlit | React + API |
|-----|-----------|----------|-------------|
| 개발 속도 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| 챗봇 UX | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 스트리밍 응답 | 수동 구현 | 기본 지원 | 수동 구현 |
| 대화 이력 관리 | 수동 구현 | 기본 지원 | 수동 구현 |
| 커스터마이징 | 제한적 | 중간 | 자유로움 |
| Agent 특화 기능 | ❌ | ✅ | ❌ |

### 추천: Chainlit

**이유**:
1. **LLM 챗봇 특화**: Agent 대화에 최적화된 UX
2. **스트리밍 기본 지원**: 긴 응답도 실시간 표시
3. **대화 이력 자동 관리**: 세션 관리 내장
4. **개발 속도**: Streamlit과 비슷하게 빠름
5. **Agent 통합**: LangChain, Strands 등과 쉽게 연동

**Chainlit 예시 코드**:
```python
import chainlit as cl
from agent import devops_agent

@cl.on_message
async def main(message: cl.Message):
    response = await devops_agent.ainvoke(message.content)
    await cl.Message(content=response).send()
```

**결정 필요**: Streamlit vs Chainlit 중 선택

---

## 9. A2A 협업 아키텍처 검토: AgentCore vs Kafka Hub-Spoke

### 9.1 두 가지 옵션 비교

참고 프로젝트([A2A-Strands-Kafka-GameBalance](https://github.com/blait/A2A-Strands-Kafka-GameBalance))를 분석한 결과, Agent 간 협업에 두 가지 접근법이 있습니다.

**Option A: AgentCore Multi-Agent Collaboration (기본)**
```
┌─────────────────────────────────────────┐
│         Bedrock Multi-Agent             │
│  ┌─────────┐    HTTP    ┌─────────┐    │
│  │Supervisor│◄─────────►│ DevOps  │    │
│  │  Agent   │           │ Agent   │    │
│  └─────────┘            └─────────┘    │
│       │                                 │
│       │ HTTP                            │
│       ▼                                 │
│  ┌─────────┐                           │
│  │  Data   │                           │
│  │ Agent   │                           │
│  └─────────┘                           │
└─────────────────────────────────────────┘
```

**Option B: Kafka Hub-Spoke (A2A 프로토콜)**
```
┌─────────────────────────────────────────┐
│              Kafka Hub (MSK)            │
│  agent.devops.requests/responses        │
│  agent.data.requests/responses          │
│  agent.registry                         │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌───────┐   ┌───────┐   ┌───────┐
│DevOps │   │ Data  │   │  CS   │
│Agent  │   │Agent  │   │Agent  │
└───────┘   └───────┘   └───────┘
```

### 9.2 상세 비교

| 항목 | AgentCore (Option A) | Kafka A2A (Option B) |
|-----|---------------------|---------------------|
| **연결 복잡도** | N² (10개 Agent = 90개 연결) | N+M (10개 Agent = 10개 연결) |
| **확장성** | 제한적 | 선형 확장 |
| **메시지 내구성** | 없음 (휘발성) | Kafka 디스크 저장 |
| **장애 격리** | 제한적 (장애 전파) | 우수 (Hub가 버퍼) |
| **구현 복잡도** | 낮음 (관리형) | 중간 (MSK 설정 필요) |
| **비용** | Bedrock 호출만 | MSK 추가 (~$200/월 dev) |
| **PoC 적합성** | ⭐⭐⭐ | ⭐⭐ |
| **프로덕션 적합성** | ⭐⭐ | ⭐⭐⭐ |

### 9.3 Kafka A2A의 핵심 장점

1. **선형 확장**: Agent 수가 늘어도 연결 수가 선형으로만 증가
2. **비동기 처리**: Agent가 즉시 응답 못해도 메시지 큐에 보관
3. **장애 격리**: 한 Agent 장애가 다른 Agent에 영향 없음
4. **관찰성**: 모든 메시지가 Kafka 통과 → 중앙 모니터링 용이
5. **멀티턴 대화**: Context ID로 대화 맥락 유지

### 9.4 권장 전략: 단계적 도입

**PoC (Week 1-2): AgentCore 기본 사용**
- 이유: 빠른 구현, 관리형 서비스, 2주 일정에 적합
- Bedrock Multi-Agent Collaboration (Supervisor Mode)

**Phase 3 (Week 5-6): Kafka A2A 도입 검토**
- 조건: Agent 수 5개 이상 또는 트래픽 증가 시
- MSK 설정 + KafkaTransport 구현
- 기존 Agent 코드 변경 최소화 (Transport 레이어만 교체)

### 9.5 Kafka A2A 도입 시 추가 작업

```
Week 5-6 (Phase 3) 예상 작업:
├── MSK 클러스터 생성 (CDK)
├── Kafka 토픽 설정
│   ├── agent.devops.requests/responses
│   ├── agent.data.requests/responses
│   └── agent.registry
├── KafkaTransport 구현 (A2A ClientTransport)
├── KafkaConsumerHandler 구현
└── Agent Registry 연동
```

**예상 비용 (MSK)**:
| 환경 | 인스턴스 | 브로커 수 | 월 비용 |
|-----|---------|----------|--------|
| 개발 | kafka.t3.small | 3 | ~$200 |
| 프로덕션 | kafka.m5.large | 3-6 | ~$1,500 |

---

## 10. 확장 계획 (PoC 이후)

### Phase 2 (Week 3-4): 학습 기능

- 행동 패턴 분석 모듈 구현
- 지침 자동 생성 및 버전 관리
- 도구 사용 패턴 분석

### Phase 3 (Week 5-6): Kafka A2A 도입 + 고도화

- **Kafka Hub-Spoke 아키텍처 도입** (Agent 확장 대비)
  - MSK 클러스터 설정
  - KafkaTransport 구현
  - Agent Registry 연동
- 도구 추가/제거 제안 기능
- 검토 UI 고도화
- 추가 Agent 확장 (QA팀, 기획팀 등)

### Phase 4 (Week 7-8): 프로덕션 준비

- VPC 내 배포
- 모니터링/알림 강화
- 비용 최적화

---

## 11. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|-------|-----|------|
| AgentCore Preview 제약 | 일부 기능 미지원 가능 | 대안 준비 (LangGraph 등) |
| LLM 응답 품질 | Agent 신뢰도 저하 | Guardrails, 프롬프트 튜닝 |
| 비용 예측 어려움 | 예산 초과 | 토큰 제한, 모니터링 |
| 2주 일정 촉박 | 범위 축소 필요 | MVP 우선, 기능 단계적 추가 |

---

## 12. 다음 단계

계획서 검토 완료. 확정 사항:

1. **챗봇 UI**: Chainlit 사용
2. **게임 태그**: `ToadstoneGame` 태그로 리소스 필터링
3. **테스트 환경**: 실제 AWS 리소스 연동 (제한 없음)
4. **A2A 아키텍처**: PoC는 AgentCore 기본, Phase 3에서 Kafka 도입 검토

---

## 13. 부록: AgentCore 주요 기능 요약

### AgentCore Runtime
- 서버리스 Agent 실행 환경
- 세션 격리 (데이터 누출 방지)
- 오픈소스 프레임워크 호환 (Strands, LangGraph, CrewAI 등)

### AgentCore Memory
- 세션 메모리: 대화 컨텍스트 유지
- 장기 메모리: 과거 상호작용 학습

### AgentCore Observability
- 실행 단계별 시각화
- 메타데이터 태깅
- 디버깅 필터

### AgentCore Gateway
- API/Lambda → Agent 도구 변환
- MCP 프로토콜 지원
- 런타임 도구 검색

### AgentCore Identity
- AWS 서비스 접근 권한
- 서드파티 도구 연동 (GitHub, Slack 등)

---

*작성: Mickey 1*
*날짜: 2026-01-30*
*버전: 1.0*
