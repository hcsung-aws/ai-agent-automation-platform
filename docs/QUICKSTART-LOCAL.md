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

## 2-1단계: 환경 변수 설정 (선택)

```bash
cp .env.example .env
```

`.env` 파일 편집:

```bash
# AWS 리전
AWS_REGION=us-east-1

# Bedrock KB 사용 시 (선택 - 미설정 시 로컬 KB 사용)
KNOWLEDGE_BASE_ID=your-kb-id
KB_DATA_SOURCE_ID=your-datasource-id
KB_S3_BUCKET=your-bucket-name

# 로컬 KB 경로 (기본값: ./knowledge-base)
LOCAL_KB_PATH=./knowledge-base
```

> 💡 **KB 미설정 시**: 로컬 `knowledge-base/` 디렉토리의 마크다운 파일을 검색합니다.

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
    ├── guide_agent.py    # 프로젝트 가이드 챗봇
    ├── main.py           # AgentCore HTTP 서버
    ├── handler.py        # 요청 핸들러
    ├── Dockerfile        # 컨테이너 빌드
    └── requirements.txt  # Agent 의존성
```

---

**다음:** [AWS 배포 가이드](QUICKSTART-AWS.md)로 프로덕션 환경 구축

---

## 부록: Knowledge Base 없이 시작하기

로컬 환경에서는 Bedrock Knowledge Base 없이도 시작할 수 있습니다.

### KB 검색 우선순위

```
1. KNOWLEDGE_BASE_ID 설정 → Bedrock KB (시맨틱 검색)
2. KB_S3_BUCKET 설정 → S3 직접 검색 (키워드)
3. LOCAL_KB_PATH 존재 → 로컬 파일 검색 (키워드)
```

### 환경별 권장 설정

| 환경 | 설정 | 장점 |
|------|------|------|
| 로컬 개발 | `LOCAL_KB_PATH` | 빠른 테스트, 즉시 반영 |
| AWS (초기) | `KB_S3_BUCKET` | 영속성, Bedrock KB 전환 준비 |
| AWS (프로덕션) | `KNOWLEDGE_BASE_ID` | 시맨틱 검색, 대용량 지원 |

### 점진적 전환 경로

```
Phase 1: 로컬 KB (개발)
    knowledge-base/*.md
        ↓
Phase 2: S3 KB (AWS 배포)
    aws s3 sync knowledge-base/ s3://kb-bucket/knowledge-base/
    → Agent가 S3에서 직접 검색
        ↓
Phase 3: Bedrock KB (프로덕션)
    S3 버킷을 Bedrock KB 데이터 소스로 연결
    → 시맨틱 검색 활성화
```

### 로컬 KB 구조

```
knowledge-base/
├── common/       # 공통 지식
├── devops/       # DevOps 가이드
├── analytics/    # Analytics 가이드
└── monitoring/   # Monitoring 가이드
```

각 폴더에 `.md` 파일을 추가하면 자동으로 검색 대상이 됩니다.

KB 생성 방법은 [AWS 배포 가이드](QUICKSTART-AWS.md)의 "7단계: Knowledge Base 생성"을 참고하세요.

---

## 부록: Knowledge Base에 정보 추가하기

Agent가 참조하는 지식을 추가하고 확인하는 방법입니다.

### 로컬 환경 (즉시 반영)

**1. 마크다운 파일 추가**

```bash
# 예: 새 운영 가이드 추가
cat > knowledge-base/devops/new-guide.md << 'EOF'
# 새 운영 가이드

## 개요
이 문서는 새로운 운영 절차를 설명합니다.

## 절차
1. 첫 번째 단계
2. 두 번째 단계
EOF
```

**2. 즉시 확인 (서버 재시작 불필요)**

```
질문: "새 운영 가이드 알려줘"
→ Agent가 방금 추가한 문서 내용을 검색하여 응답
```

**3. 카테고리별 폴더 구조**

| 폴더 | 용도 | 예시 |
|------|------|------|
| `common/` | 공통 지식, 정책 | 조직 정보, 에스컬레이션 |
| `devops/` | 운영 가이드 | 장애 대응, 배포 절차 |
| `analytics/` | 분석 가이드 | 쿼리 패턴, 지표 정의 |
| `monitoring/` | 모니터링 가이드 | 알람 설정, 임계값 |

### AWS 환경 (Bedrock KB)

**1. S3에 문서 업로드**

```bash
# 문서 작성
echo "# 새 가이드 내용" > new-guide.md

# S3 업로드
aws s3 cp new-guide.md s3://$KB_S3_BUCKET/docs/
```

**2. KB 동기화 실행**

```bash
# 동기화 시작
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id $KNOWLEDGE_BASE_ID \
  --data-source-id $KB_DATA_SOURCE_ID

# 상태 확인 (COMPLETE가 될 때까지 대기)
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id $KNOWLEDGE_BASE_ID \
  --data-source-id $KB_DATA_SOURCE_ID \
  --query "ingestionJobSummaries[0].status"
```

> ⏱️ 동기화에 30초~1분 소요됩니다.

**3. 검색 테스트**

```bash
aws bedrock-agent-runtime retrieve \
  --knowledge-base-id $KNOWLEDGE_BASE_ID \
  --retrieval-query '{"text": "새 가이드"}'
```

### 로컬 ↔ AWS 동기화

로컬에서 작성한 문서를 AWS에도 반영하려면:

```bash
# 로컬 KB → S3 업로드
aws s3 sync ./knowledge-base s3://$KB_S3_BUCKET/knowledge-base/

# KB 동기화
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id $KNOWLEDGE_BASE_ID \
  --data-source-id $KB_DATA_SOURCE_ID
```
