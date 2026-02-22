# Project Context for Mickey Agents

## Environment
- OS: Linux (WSL2)
- Region: us-east-1
- 주요 서비스: Bedrock AgentCore, Knowledge Bases, DynamoDB, S3

## Goal
조직 업무를 AI Agent 기반으로 전환하는 플랫폼 구축
- 점진적 학습 + A2A 협업 + 자기 개선

## Constraints
- 2주 PoC 일정
- AWS Bedrock 기반
- 초기 Agent 2개 (DevOps, 데이터분석)

## Key Decisions

### 2026-01-30: 프레임워크 선택
- Chosen: AgentCore + Strands Agents
- Reasoning: AWS 공식 지원, 요구사항 대부분 충족

### 2026-01-30: 챗봇 UI
- Chosen: Chainlit
- Reasoning: LLM 챗봇 특화, 스트리밍 기본 지원

### 2026-01-30: A2A 아키텍처
- PoC: AgentCore Multi-Agent Collaboration (HTTP 기반)
- Phase 3: Kafka Hub-Spoke 도입 검토 (확장성 필요 시)

## Known Issues
- Docker Hub rate limit → ECR Public 이미지 사용
- AgentCore IAM 역할에 도구 권한 별도 추가 필요

## Lessons Learned

### Mickey 1: AgentCore 배포
- Problem: Docker Hub rate limit으로 빌드 실패
- Cause: CodeBuild에서 Docker Hub 이미지 pull 제한
- Solution: `public.ecr.aws/docker/library/python:3.10-slim` 사용
- Avoid: Docker Hub 이미지 직접 사용

### Mickey 1: IAM 권한
- Problem: Agent 도구 실행 시 권한 오류
- Cause: AgentCore 자동 생성 역할에 도구 권한 없음
- Solution: `DevOpsAgentToolsPolicy` 인라인 정책 추가
- Avoid: 자동 생성 역할만 의존

### Mickey 9: LLM 응답에 메타데이터 의존 금지
- Problem: 테스트 모드 표시를 LLM 응답에 포함시켰으나 Supervisor가 생략
- Cause: LLM은 "중요하지 않다"고 판단한 내용을 요약/생략함
- Solution: 코드 레벨에서 플래그 관리 (`IS_TEST_MODE` + 튜플 반환)
- Avoid: 중요한 메타데이터를 LLM 응답 텍스트에 의존

### Mickey 9: 테스트 모드 Agent 패턴
- Pattern: `IS_TEST_MODE = True` 플래그 + `create_agent() -> (agent, is_test_mode)` 튜플 반환
- app.py에서 플래그 확인 후 경고 배너 자동 출력
- 실제 API 연동 시 `IS_TEST_MODE = False`로 변경

### Mickey 9: app.py 수정 시 9개 항목 체크
- import 추가
- agent 변수 추가
- ask_{name}_agent 도구 함수 추가
- SYSTEM_PROMPT에 Agent 설명 추가
- tools 리스트에 추가
- 시작 메시지에 Agent 영역 추가
- 처리 과정 표시에 emoji/label 추가
- 상세 보기 버튼 label 추가
- 상세 보기 title 추가

### Mickey 10: KB 문서 추가 절차
- S3 업로드 → 메타데이터 파일 생성 → KB Sync 3단계 필수
- 메타데이터 파일: `{filename}.metadata.json` 형식
- category 태그: common, devops, analytics, monitoring
```bash
# 1. 문서 업로드
aws s3 cp doc.md s3://devops-agent-kb-965037532757/knowledge-base/[category]/

# 2. 메타데이터 생성
echo '{"metadataAttributes":{"category":"[category]"}}' | \
  aws s3 cp - s3://devops-agent-kb-965037532757/knowledge-base/[category]/doc.md.metadata.json

# 3. KB Sync
aws bedrock-agent start-ingestion-job --knowledge-base-id H50SNRJBFF --data-source-id OSFG10XDDN --region us-east-1
```

### Mickey 10: S3 경로 변경 시 IAM 정책 확인
- Problem: KB Sync 실패 (403 Access Denied)
- Cause: IAM 정책이 기존 경로만 허용
- Solution: 새 경로를 IAM 정책 Resource에 추가
- 관련 정책: `AmazonBedrockS3PolicyForKnowledgeBase_p2y8n`

### Mickey 15: AgentCore Runtime ARM64 전용
- Problem: x86_64 이미지로 AgentCore Runtime 생성 실패
- Cause: AgentCore Runtime은 ARM64 아키텍처만 지원
- Solution: Dockerfile에 `--platform=linux/arm64` 추가
- Avoid: x86_64 이미지로 AgentCore 배포 시도

### Mickey 15: KMS + CloudWatch Logs 권한
- Problem: KMS 키로 암호화된 LogGroup 생성 실패
- Cause: KMS 키 정책에 CloudWatch Logs 서비스 권한 없음
- Solution: `kms_key.grant_encrypt_decrypt(iam.ServicePrincipal(f"logs.{region}.amazonaws.com"))`
- Avoid: KMS 암호화 LogGroup 생성 시 키 정책 확인 누락

### Mickey 15: IAM description ASCII 제한
- Problem: IAM Role 생성 시 한글 description으로 실패
- Cause: IAM은 ASCII 문자만 허용 (정규식: `[\u0009\u000A\u000D\u0020-\u007E\u00A1-\u00FF]*`)
- Solution: description을 영어로 작성
- Avoid: IAM Role/Policy description에 한글 사용

### Mickey 16: AgentCore Runtime = HTTP 서버
- Problem: Lambda 핸들러 방식으로 시도 → 404 에러
- Cause: AgentCore Runtime은 Lambda가 아닌 HTTP 서버 방식 기대
- Solution: FastAPI + uvicorn으로 HTTP 서버 구현
- 필수 엔드포인트:
  - `POST /invocations`: Agent 호출 (JSON 입출력)
  - `GET /ping`: 헬스체크 (`{"status": "Healthy", "time_of_last_update": <unix_timestamp>}`)
- 포트: 8080, 호스트: 0.0.0.0
- Reference: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-http-protocol-contract.html

### Mickey 16: Bedrock inference-profile 권한 필요
- Problem: Agent 호출 시 500 에러 (AccessDeniedException)
- Cause: IAM 정책에 `foundation-model/*`만 허용, `inference-profile/*` 누락
- Solution: IAM 정책에 inference-profile 리소스 추가
```python
resources=[
    "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
    "arn:aws:bedrock:*:*:inference-profile/*",
]
```
- Avoid: foundation-model만 허용하고 inference-profile 누락

### Mickey 16: AgentCore 로그 확인 명령어
```bash
# 최근 로그
AWS_REGION=us-east-1 aws logs filter-log-events \
  --log-group-name "/aws/bedrock-agentcore/runtimes/{RUNTIME_ID}-DEFAULT" \
  --start-time $(($(date +%s) - 3600))000 --limit 30

# 에러 로그만
AWS_REGION=us-east-1 aws logs filter-log-events \
  --log-group-name "/aws/bedrock-agentcore/runtimes/{RUNTIME_ID}-DEFAULT" \
  --filter-pattern "ERROR" --limit 20
```

### Mickey 19: Chainlit 2.9.6 피드백 API
- `@cl.on_feedback` 콜백 등록만으로 👍/👎 버튼 자동 표시
- config.toml에 `human_feedback` 키 없음 (존재하지 않는 설정)
- Feedback 타입: `cl.types.Feedback` (`cl.Feedback`는 KeyError)
- 필드: `forId`(메시지 참조), `value`(0=negative, 1=positive), `comment`, `id`(피드백 자체 ID)
- Avoid: `cl.Feedback` 직접 참조, config.toml에 human_feedback 설정

### Mickey 17: KB 검색은 단어 단위 매칭 필수
- Problem: 전체 문자열 매칭(`query in content`)은 LLM이 생성하는 query와 매칭 실패
- Cause: LLM은 자연어 query를 생성하지만 KB 문서에 정확한 문자열이 없음
- Solution: 단어 단위로 분리하여 키워드 매칭 (2자 이상, 하나라도 매칭되면 포함)
- Avoid: `query in content` 방식의 전체 문자열 매칭

### Mickey 17: invoke_agent_runtime 호출 방법
- boto3 클라이언트: `bedrock-agentcore`
- API: `invoke_agent_runtime(agentRuntimeArn, runtimeSessionId, payload)`
- runtimeSessionId: 최소 33자 (UUID 권장)
- read_timeout: 300초 이상 권장
- ARN: `arn:aws:bedrock-agentcore:{region}:{account}:runtime/{runtime_id}`

### Mickey 19: Chainlit 피드백 버튼은 Data Layer 필수
- Problem: @cl.on_feedback 등록해도 👍/👎 버튼이 안 보임
- Cause: server.py PUT /feedback에서 get_data_layer() 체크 → None이면 프론트엔드가 버튼 미렌더링
- Solution: cl.Action 버튼으로 자체 구현 (PoC 패턴: feedback_positive/feedback_negative 액션)
- Avoid: Data Layer 없이 @cl.on_feedback 사용

### Mickey 19: Chainlit HTML 렌더링 불가
- config.toml `unsafe_allow_html = false`가 기본값
- `<details>`, `<summary>` 등 HTML 태그는 텍스트로 출력됨
- cl.Text(display="side")는 가시성 낮음 → 중요 내용은 인라인 마크다운으로
- Avoid: HTML 태그 사용, cl.Text 사이드 패널에 핵심 내용 숨기기

### Mickey 19: Strands Agent.hooks 외부 접근
- Agent 생성 후 `agent.hooks.add_hook(provider)`로 외부에서 hook 추가 가능
- supervisor.py 수정 없이 app.py에서 ToolCallTracker로 추론 과정 캡처
- Pattern: HookProvider 구현 → BeforeToolCallEvent/AfterToolCallEvent 콜백

### Mickey 20: Chainlit에서 Strands Agent 호출은 asyncio.to_thread 필수
- Problem: async 함수 안에서 supervisor() 동기 호출 → 이벤트 루프 블록 → WebSocket 끊김 → 세션 재시작 → 환영 메시지 재출력
- Solution: `response = await asyncio.to_thread(supervisor, message.content)`
- Avoid: Chainlit on_message 안에서 Strands Agent를 직접 동기 호출

### Mickey 20: Chainlit cl.Action에 disabled 없음
- 비활성화 대안: `msg.remove_actions()` + `msg.actions = []` + content 추가 + `msg.update()`
- Avoid: cl.Action에 disabled 속성 기대

### Mickey 20: Multi-Agent에서 URL/링크 소실 방지
- Problem: Sub-Agent LLM → Supervisor LLM 2단계 요약 시 URL이 "링크 참고"로 축약됨
- Solution: 3계층 SYSTEM_PROMPT에 링크 보존 원칙 명시 (도구→Sub-Agent→Supervisor)
- Rule: URL/데이터 보존이 필요하면 각 계층 SYSTEM_PROMPT에 명시 필수

## File Locations
- Source: src/ (예정)
- Infrastructure: infra/ (예정)
- Tests: tests/ (예정)
- Docs: docs/ (예정)

## Common Commands
```bash
# (구현 후 추가 예정)
```

### Mickey 14: KB 검색 로직 중복 방지
- Problem: kb_tools.py(전체 문자열 매칭)와 guide_agent.py(단어 매칭)에서 같은 폴백 체인을 각각 구현, 검색 품질 차이 발생
- Solution: 단어 매칭으로 통일
- Rule: 같은 검색 로직을 여러 파일에 구현하지 말 것. 새 검색 로직 추가 시 기존 구현과 통일 확인 필수

### Mickey 21: Docker 빌드 시 agents/ 외부 파일 누락 주의
- Problem: config.py가 agents/ 밖에 있어 Docker COPY . . 시 누락 → 런타임 import 에러
- Cause: Dockerfile이 agents/ 디렉토리 기준, config.py는 상위 디렉토리
- Rule: Docker 빌드 대상 디렉토리 안에 필요한 모든 파일이 있는지 확인 필수

### Mickey 21: CDK 스택에서 경로 하드코딩 금지
- Problem: agentcore_stack.py의 agent_path가 하드코딩 → 커스텀 agent 배포 불가
- Rule: CDK context 또는 환경변수로 경로를 받아야 유연한 배포 가능

### Mickey 20: 피드백과 사례는 보완 관계
- 피드백: "뭘 고칠지" 신호 (👍/👎) → 스케줄러가 분석하여 개선 방향 도출
- 사례: "어떻게 해결했는지" 지식 → KB에 축적하여 RAG로 직접 재활용
- 둘 다 필요하며 역할이 다름

### Mickey 20: 자동 저장 시 후속 처리 경로 필수
- Problem: drafts/에 자동 저장만 하고 후속 처리(검토/승격) 없으면 dead-end
- Solution: 스케줄러 없이 운영 시 저장 시점에 사용자 확인 거쳐야 함
- Pattern: 👍 → LLM 요약 → 미리보기 → ✅저장/❌취소

### Mickey 15: config.py 위치와 테스트 sys.path
- Problem: `templates/local/agents/config.py`에 두니 테스트에서 `ModuleNotFoundError`
- Cause: 테스트가 `templates/local/`을 sys.path에 추가하므로 `from config import ...`는 `templates/local/config.py`를 찾음
- Solution: config.py를 `templates/local/`에 배치 (테스트 sys.path와 일치)
- Rule: 공유 config는 테스트의 sys.path 루트에 배치할 것

### Mickey 15: 하드코딩 환경변수 매핑
- `BEDROCK_MODEL_ID`: 모델 ID (기본값: us.anthropic.claude-3-5-sonnet-20241022-v2:0)
- `BEDROCK_REGION`: AWS region (기본값: us-east-1)
- `MONITORING_TEST_MODE`: monitoring agent 테스트 모드 (기본값: true, false로 해제)
- `CDK_DEFAULT_REGION`: CDK 배포 region

### Mickey 22: CDK from_asset() file 옵션으로 build context 분리
- Problem: config.py가 agents/ 밖에 있어 Docker 빌드 시 누락
- Cause: build context가 agents/이면 상위 파일 접근 불가
- Solution: `from_asset(directory="local/", file="agents/Dockerfile")`로 build context를 상위로 변경
- Rule: Docker 빌드 시 외부 파일 의존성이 있으면 build context를 상위로 올리고 file 옵션으로 Dockerfile 위치 지정

### Mickey 23: S3 Vectors가 OpenSearch Serverless보다 CDK 자동화에 유리
- Context: Bedrock KB 벡터 스토어 선택
- S3 Vectors: CfnVectorBucket + CfnIndex (CloudFormation 네이티브, 2개 리소스)
- OpenSearch Serverless: vector index가 CloudFormation 미지원 → Custom Resource Lambda 필요
- Rule: CDK 자동화 우선이면 S3 Vectors 선택

### Mickey 23: CfnIndex metadata_configuration에 Bedrock 키 필수
- Problem: Bedrock KB가 S3 Vectors에 메타데이터를 저장하려면 키 설정 필요
- Solution: nonFilterableMetadataKeys에 "AMAZON_BEDROCK_TEXT", "AMAZON_BEDROCK_METADATA" 추가
- Rule: Bedrock KB + S3 Vectors 조합 시 CfnIndex에 메타데이터 키 설정 필수

## Last Updated
Mickey 23 - 2026-02-21
