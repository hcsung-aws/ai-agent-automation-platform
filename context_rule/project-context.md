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

## File Locations
- Source: src/ (예정)
- Infrastructure: infra/ (예정)
- Tests: tests/ (예정)
- Docs: docs/ (예정)

## Common Commands
```bash
# (구현 후 추가 예정)
```

## Last Updated
Mickey 17 - 2026-02-08
