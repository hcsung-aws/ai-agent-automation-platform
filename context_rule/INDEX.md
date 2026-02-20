# Context Rule Index

프로젝트 특화 규칙의 지식 지도. Mickey는 세션 시작 시 이 INDEX를 읽고, 작업 중 트리거 조건에 매칭되면 해당 파일만 로딩한다.

## Rule Map

| 트리거 | 파일 | 요약 |
|--------|------|------|
| 세션 시작 (T2 자동 로딩) | project-context.md | 환경, 목표, 제약, 주요 결정, Known Issues, 누적 교훈 |
| KB 설계, 검색 로직, 폴백 체인, 환경변수 설정 | kb-design-guide.md | KB 3단계 폴백 (Bedrock→S3→로컬), 환경별 설정, 점진적 전환 경로 |
| Agent 생성, Agent 수정, Supervisor 연결, KB 연동 | agent-builder-guide.md | Agent/도구 템플릿, Supervisor 연결 체크리스트, KB 연동 패턴 |
| Kiro CLI Agent, Agent JSON, ~/.kiro/agents, ListAgents, delegate, InvokeSubagents | kiro-cli-agent-guide.md | Kiro CLI Agent JSON 규칙, 등록 방법, delegate 워크플로 |

## 사용 규칙

1. project-context.md는 T2로 매 세션 자동 로딩 (INDEX 트리거 불필요)
2. 나머지 파일은 작업 내용이 트리거 키워드에 매칭될 때만 로딩
3. 새 규칙 파일 추가 시 이 INDEX에 반드시 등록

## Last Updated
Mickey 17 - 2026-02-19
