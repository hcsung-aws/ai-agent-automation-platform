# 🚀 로컬 환경 빠른 시작 (5분)

이 가이드를 따라 로컬 환경에서 AIOps 스타터 킷을 실행합니다.

## 사전 요구사항

- Python 3.10+
- AWS 계정 및 자격증명 (Bedrock 모델 호출용)
- Kiro CLI (Agent Builder용)

## 1단계: 저장소 클론 (1분)

```bash
git clone https://github.com/your-org/aiops-starter-kit.git
cd aiops-starter-kit/templates/local
```

## 2단계: 설치 (2분)

```bash
./setup.sh
```

설치 스크립트가 자동으로:
- Python 가상환경 생성
- 의존성 설치 (strands-agents, chainlit, boto3)
- AWS 자격증명 확인

## 3단계: 서버 실행 (1분)

```bash
source .venv/bin/activate
chainlit run app.py --port 8000
```

## 4단계: 브라우저 접속 (1분)

`http://localhost:8000` 접속

**테스트 질문:**
- "어떻게 시작해요?"
- "Agent 어떻게 만들어요?"
- "프로젝트 구조 보여줘"

---

## 다음 단계: 첫 번째 Agent 만들기

### Agent Builder 실행

```bash
kiro chat --agent agent-builder
```

### 자연어로 요청

```
"CloudWatch 알람을 조회하는 Monitoring Agent 만들어줘"
```

Agent Builder가 자동으로:
1. Agent 코드 생성 (`agents/monitoring_agent.py`)
2. Supervisor에 연결
3. 테스트 방법 안내

---

## 트러블슈팅

### AWS 자격증명 오류

```bash
aws configure
# Access Key, Secret Key, Region 입력
```

### Bedrock 모델 접근 오류

AWS 콘솔에서 Bedrock 모델 접근 권한 활성화:
1. Bedrock 콘솔 → Model access
2. Claude 3.5 Sonnet 활성화

### 포트 충돌

```bash
chainlit run app.py --port 8001  # 다른 포트 사용
```

---

## 파일 구조

```
templates/local/
├── setup.sh              # 설치 스크립트
├── app.py                # Chainlit UI
├── agent-builder.json    # Kiro CLI Agent Builder 설정
└── agents/
    ├── supervisor.py     # Supervisor (Agent 조율)
    └── guide_agent.py    # 프로젝트 가이드 챗봇
```

---

**다음:** [AWS 배포 가이드](QUICKSTART-AWS.md)로 프로덕션 환경 구축

---

## 부록: Knowledge Base 없이 시작하기

로컬 환경에서는 Bedrock Knowledge Base 없이도 시작할 수 있습니다.

### 현재 구현 (하드코딩)

`agents/guide_agent.py`의 `search_project_docs` 함수는 하드코딩된 문서를 반환합니다.
빠른 테스트에는 충분하지만, 실제 운영에는 KB 연동이 권장됩니다.

### KB 연동 시점

다음 상황에서 Bedrock KB 연동을 고려하세요:
- 문서가 자주 업데이트되는 경우
- 문서 양이 많아 하드코딩이 어려운 경우
- AWS 배포 후 프로덕션 운영 시

KB 생성 방법은 [AWS 배포 가이드](QUICKSTART-AWS.md)의 "7단계: Knowledge Base 생성"을 참고하세요.
