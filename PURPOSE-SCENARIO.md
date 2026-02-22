# PURPOSE-SCENARIO

## Ultimate Purpose

처음 접하는 사람이라도 AI Agent 기반 운영 자동화(AIOps)를 **로컬에서 시작하여 AWS 프로덕션까지** 쉽고 빠르게 도입할 수 있는 완전한 스타터 킷을 제공한다.

핵심은 **"로컬 체험 → Agent 생성 → 개선 → AWS 배포 → 조직 서비스화"** 의 전체 여정을 템플릿과 도구로 지원하는 것이다.

## Usage Scenarios

### 시나리오 1: 로컬 환경 구축 (5분)
- 템플릿 기반으로 멀티에이전트 플랫폼을 로컬에 설치
- Supervisor + Guide Agent로 즉시 체험 가능
- `setup.sh` 원클릭 설치 → Chainlit UI로 대화

### 시나리오 2: 자연어로 Agent 생성
- Agent Builder를 Kiro CLI에 설치
- "비용 모니터링 Agent 만들어줘" 같은 자연어 요청으로 Agent 생성
- Supervisor에 자동 연결, 즉시 테스트

### 시나리오 3: 피드백 루프로 개선
- 👍/👎 피드백 수집 → 패턴 분석 → Agent 개선
- 로컬에서 충분히 검증한 뒤 배포 단계로 진행

### 시나리오 4: AWS 프로덕션 배포
- 로컬에서 개선한 Agent + 플랫폼을 AWS 템플릿으로 AgentCore에 배포
- CDK 기반 원클릭 배포 (`deploy.sh`)
- 조직 내 활용 가능한 서비스로 확장

### 시나리오 5: 지속적 Agent 확장
배포 이후 신규 Agent 추가는 두 가지 경로:

**경로 A: 로컬 → AWS 이관**
- 로컬에서 Agent 생성 → 피드백으로 개선 → AWS에 배포

**경로 B: AWS 직접 배포**
- AWS 환경에서 Agent Builder로 직접 생성 → 개선

어느 경로든 동일한 도구(Agent Builder, Review Agent, Deployment Agent)로 운영.

## Acceptance Criteria

- [ ] 처음 접하는 사용자가 README만 보고 로컬 실행까지 5분 이내
- [ ] Agent Builder로 자연어 Agent 생성 → 테스트까지 15분 이내
- [ ] 로컬 Agent를 AWS AgentCore에 배포까지 30분 이내
- [ ] AWS 환경에서 신규 Agent 직접 생성/배포 가능
- [ ] 피드백 루프가 로컬(JSON)/AWS(DynamoDB) 모두 동작

## Last Confirmed
2026-02-21 Mickey 24

## Last Updated
2026-02-21 Mickey 24
