# Agent Builder Guide

## 목적
자연어 명령으로 Agent를 생성/수정하고 Supervisor에 연결

## 지원 작업
1. **새 Agent 생성**: 도구 + Agent + Supervisor 연결
2. **기존 Agent 수정**: 도구 추가, 시스템 프롬프트 개선, KB 연동
3. **Knowledge Base 연동**: 참조 자료를 KB로 구축하여 Agent에 연결

## 워크플로우

### A. 새 Agent 생성

```
사용자: "HR Agent 만들어줘. 휴가 신청, 직원 조회 기능으로"
                    ↓
1. 도구 파일 생성: src/tools/{name}_tools.py
2. Agent 파일 생성: src/agent/{name}_agent.py
3. Supervisor 수정: supervisor_agent.py
4. 테스트 안내
```

### B. 기존 Agent 수정

```
사용자: "Godot Review Agent에 KB 검색 기능 추가해줘"
                    ↓
1. 현재 Agent 파일 분석: src/agent/{name}_agent.py
2. 현재 도구 파일 분석: src/tools/{name}_tools.py
3. 필요한 수정 계획 제시
4. 사용자 확인 후 수정 실행
5. 테스트 안내
```

### C. Knowledge Base 연동

```
사용자: "Godot 프로젝트를 KB로 만들어서 Agent에 연결해줘"
                    ↓
1. KB용 도구 생성: src/tools/{name}_kb_tools.py
2. Agent에 KB 도구 추가
3. 시스템 프롬프트에 KB 활용 지침 추가
4. 테스트 안내
```

---

## 도구 템플릿

```python
"""[Name] Tools - [Description]."""
from strands import tool

@tool
def tool_name(param: str) -> str:
    """도구 설명.
    
    Args:
        param: 파라미터 설명
    
    Returns:
        반환값 설명
    """
    # 구현
    return "결과"
```

**규칙:**
- `@tool` 데코레이터 필수
- docstring에 Args, Returns 명시 (Agent가 도구 선택 시 참조)
- 반환값은 항상 `str`
- URL/링크를 포함하는 도구는 마크다운 `[텍스트](URL)` 형식으로 반환

---

## Agent 템플릿

```python
"""[Name] Agent - [Description]."""
from strands import Agent
from strands.models import BedrockModel

from src.tools.{name}_tools import tool1, tool2

SYSTEM_PROMPT = """당신은 [역할] 전문가 AI 에이전트입니다.

주요 역할:
1. [역할 1]
2. [역할 2]

응답 원칙:
- 한국어로 응답
- [추가 원칙]
- 도구가 반환하는 URL/링크는 마크다운 [텍스트](URL) 형식으로 응답에 반드시 포함
"""

def create_{name}_agent() -> Agent:
    """Create and return [Name] Agent instance."""
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
    )
    
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[tool1, tool2],
    )
```

---

## Supervisor 연결

### 1. Import 추가
```python
from src.agent.{name}_agent import create_{name}_agent
```

### 2. Lazy initialization 추가
```python
_{name}_agent = None

def _get_{name}_agent():
    global _{name}_agent
    if _{name}_agent is None:
        _{name}_agent = create_{name}_agent()
    return _{name}_agent
```

### 3. Tool 함수 추가
```python
@tool
def ask_{name}_agent(query: str) -> str:
    """[Name] 전문가 에이전트에게 질문합니다.
    
    [담당 영역 설명]
    
    Args:
        query: [Name] 관련 질문 또는 요청
    
    Returns:
        [Name] Agent의 응답
    """
    global _current_sub_agents
    _current_sub_agents.append("{name}")
    agent = _get_{name}_agent()
    response = agent(query)
    return str(response)
```

### 4. tools 배열에 추가
```python
agent = Agent(
    ...
    tools=[
        ask_devops_agent,
        ask_analytics_agent,
        ask_{name}_agent,  # 추가
    ],
)
```

### 5. SYSTEM_PROMPT에 설명 추가
```
### [Name] Agent (ask_{name}_agent)
담당 영역:
- [영역 1]
- [영역 2]
```

### 6. Supervisor SYSTEM_PROMPT 응답 원칙에 링크 보존 추가
```
## 응답 원칙
- 하위 Agent가 제공한 URL/링크를 그대로 보존 (요약 시에도 생략 금지)
```

---

## 체크리스트

생성 완료 후 확인:
- [ ] src/tools/{name}_tools.py 생성됨
- [ ] src/agent/{name}_agent.py 생성됨
- [ ] supervisor_agent.py에 import 추가됨
- [ ] supervisor_agent.py에 _get_{name}_agent() 추가됨
- [ ] supervisor_agent.py에 ask_{name}_agent() 추가됨
- [ ] supervisor_agent.py의 tools 배열에 추가됨
- [ ] supervisor_agent.py의 SYSTEM_PROMPT에 설명 추가됨

---

## 테스트 명령어

```bash
# Agent 실행
chainlit run app.py --port 8000

# 테스트 질문
"[Name] Agent에게 [테스트 질문]"
```

---

## 참고 파일

기존 구현 참고:
- src/agent/devops_agent.py
- src/agent/analytics_agent.py
- src/agent/supervisor_agent.py
- src/tools/cloudwatch_tools.py
- src/tools/kb_tools.py (KB 연동 패턴)

---

## AWS KB 자동 생성 + Sync

### 개요

`deploy.sh`로 AWS 배포 시 KB 인프라가 자동 생성됩니다:
- S3 Vectors 벡터 스토어 + Bedrock Knowledge Base + DataSource
- S3 → SQS → Lambda 자동 Sync 파이프라인

Agent 코드에서 수동 KB 생성은 불필요합니다.

### 동작 흐름

```
deploy.sh 실행
  → CDK: S3 Vectors + Bedrock KB + DataSource 자동 생성
  → CDK: S3 이벤트 → SQS → Lambda (자동 Sync) 파이프라인 생성
  → knowledge-base/ → S3 sync → 자동 ingestion
  → AgentCore Runtime에 KNOWLEDGE_BASE_ID 환경변수 자동 설정
```

### KB 연동 Agent의 환경변수 폴백 패턴

guide_agent.py에 구현된 3단계 폴백 체인을 따릅니다:

```python
import os
from pathlib import Path

KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")
KB_S3_BUCKET = os.environ.get("KB_S3_BUCKET", "")
LOCAL_KB_PATH = Path(os.environ.get("LOCAL_KB_PATH", "knowledge-base"))
```

```
1. KNOWLEDGE_BASE_ID 설정 시 → Bedrock KB 시맨틱 검색 (AWS 배포 시 자동)
2. KB_S3_BUCKET 설정 시 → S3 키워드 검색 (폴백)
3. LOCAL_KB_PATH → 로컬 파일 키워드 검색 (개발 환경)
```

로컬에서는 `knowledge-base/` 폴더로 동작하고, AWS 배포 시 CDK가 KNOWLEDGE_BASE_ID를 자동 주입하므로 **코드 변경 없이** 시맨틱 검색으로 전환됩니다.

### KB 문서 추가 (배포 후)

자동 Sync가 설정되어 있으므로 S3에 파일만 업로드하면 됩니다:

```bash
aws s3 cp my-doc.md s3://{KB_BUCKET}/knowledge-base/devops/
# → S3 이벤트 → SQS → Lambda → StartIngestionJob 자동 실행
```

---

## Knowledge Base 연동 패턴

### KB 도구 템플릿 (Bedrock KB 사용)

```python
"""[Name] KB Tools - Knowledge Base 검색."""
import boto3
from strands import tool

KNOWLEDGE_BASE_ID = "[KB_ID]"  # Bedrock KB ID

@tool
def search_{name}_kb(query: str) -> str:
    """[Name] 관련 지식을 검색합니다.
    
    Args:
        query: 검색할 내용
    
    Returns:
        관련 지식 검색 결과
    """
    client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
    
    response = client.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": 5}
        }
    )
    
    results = []
    for i, result in enumerate(response.get("retrievalResults", []), 1):
        content = result.get("content", {}).get("text", "")
        score = result.get("score", 0)
        if score > 0.3:
            if len(content) > 2000:
                content = content[:2000] + "..."
            results.append(f"[결과 {i}] (관련도: {score:.2f})\n{content}")
    
    return "\n\n---\n\n".join(results) if results else "관련 내용을 찾지 못했습니다."
```

### KB 도구 템플릿 (로컬 파일 기반)

```python
"""[Name] KB Tools - 로컬 파일 기반 지식 검색."""
import os
from strands import tool

KB_ROOT = "[경로]"  # 지식 베이스 루트 디렉토리

@tool
def search_{name}_files(query: str, file_extension: str = ".gd") -> str:
    """[Name] 프로젝트에서 관련 파일을 검색합니다.
    
    Args:
        query: 검색할 키워드
        file_extension: 파일 확장자 (기본: .gd)
    
    Returns:
        검색 결과
    """
    results = []
    for root, dirs, files in os.walk(KB_ROOT):
        for file in files:
            if file.endswith(file_extension):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if query.lower() in content.lower():
                    results.append(f"파일: {path}\n매칭된 내용 포함")
    
    return "\n".join(results) if results else "관련 파일을 찾지 못했습니다."

@tool
def get_{name}_file_content(file_path: str) -> str:
    """특정 파일의 내용을 가져옵니다.
    
    Args:
        file_path: 파일 경로
    
    Returns:
        파일 내용
    """
    full_path = os.path.join(KB_ROOT, file_path) if not file_path.startswith(KB_ROOT) else file_path
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    return f"파일을 찾을 수 없습니다: {file_path}"
```

### KB 컨텍스트 문서 작성 가이드

KB에는 단순 코드뿐 아니라 **컨벤션과 맥락 정보**를 함께 포함해야 합니다.

**KB 컨텍스트 문서 구조:**
```markdown
# [프로젝트명] 코드 리뷰 컨텍스트

## Part 1: [기술/엔진] 기초
- 기본 개념, 문법, 주요 API

## Part 2: 프로젝트 개요
- 프로젝트 목적, 특징

## Part 3: 코드 컨벤션
- 네이밍 규칙, 타입 힌트, 권장/비권장 패턴

## Part 4: 프로젝트 구조
- 디렉토리 구조, 파일별 역할

## Part 5: 핵심 패턴
- 프로젝트 특유의 패턴 (예: 리플레이 모드 분기)
- 각 패턴의 맥락 설명

## Part 6: 성능 고려사항
- 권장/주의 사항

## Part 7: 리뷰 체크리스트
- 코드 리뷰 시 확인할 항목

## Part 8: 코드 예시
- 실제 프로젝트의 모범 코드
```

**KB 활용 원칙:**
- KB는 리뷰 **참고용** (리뷰 대상 코드는 사용자가 제공)
- 컨벤션 일관성 검토에 활용
- 프로젝트 맥락 파악에 활용

### Agent에 KB 연동 시 시스템 프롬프트 추가 사항

```
## Knowledge Base 활용

이 Agent는 [Name] Knowledge Base에 접근할 수 있습니다.

KB 활용 원칙:
1. 질문에 답하기 전 관련 지식 먼저 검색
2. KB 검색 결과를 바탕으로 구체적인 답변 제공
3. KB에 없는 내용은 일반 지식으로 보완
4. 출처(파일명/문서명) 명시
```

---

## Agent 수정 체크리스트

기존 Agent 수정 시 확인:
- [ ] 현재 도구 목록 파악
- [ ] 현재 시스템 프롬프트 분석
- [ ] 수정 계획 사용자에게 제시
- [ ] 사용자 확인 후 수정 진행
- [ ] 새 도구 추가 시 import 및 tools 배열 업데이트
- [ ] 시스템 프롬프트 수정 시 기존 내용 유지하며 추가

---

## AWS 배포

### 프로젝트 구조 (Docker 빌드 관점)

```
templates/local/          ← Docker build context
├── config.py             ← COPY config.py . (Dockerfile에서 복사)
├── .dockerignore         ← 불필요 파일 제외
├── agents/
│   ├── Dockerfile        ← from_asset(local/, file="agents/Dockerfile")
│   ├── main.py           ← AgentCore HTTP 엔트리포인트
│   ├── supervisor.py
│   ├── guide_agent.py
│   └── requirements.txt
```

- build context가 `templates/local/`이므로 config.py가 자동 포함됨
- `from config import MODEL_ID, REGION_NAME`이 Docker 컨테이너에서도 동작

### 새 Agent 추가 후 AWS 재배포

1. `agents/` 안에 새 agent 파일 생성
2. `agents/supervisor.py`에 연결 (체크리스트 참조)
3. pip 패키지 추가 시 `agents/requirements.txt` 업데이트
4. 재배포:
   ```bash
   cd templates/aws && ./deploy.sh
   ```
   CDK가 자동으로 Docker 빌드 → ECR 푸시 → Runtime 업데이트

### 커스텀 프로젝트 배포

기본 template이 아닌 별도 프로젝트를 배포할 때:
```bash
cd templates/aws && ./deploy.sh /path/to/my-project
```
- `/path/to/my-project/` 안에 `agents/` 디렉토리와 `config.py`가 있어야 함
- `agents/Dockerfile`, `agents/main.py` 필수
