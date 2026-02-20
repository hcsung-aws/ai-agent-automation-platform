# Kiro CLI Agent Guide

## Agent JSON 파일 규칙

### 필수 필드
```json
{
  "name": "agent-name",
  "description": "설명",
  "prompt": "시스템 프롬프트",
  "tools": ["*"],
  "resources": ["file://path/to/file"]
}
```

### tools 필드
- `["*"]`: 모든 도구 허용 (권장)
- `[]`: 도구 없음
- `[""]`: ❌ 오류 — 빈 문자열은 무효

### allowedTools 필드 (선택)
- `[]`: 제한 없음 (기본)
- `["fs_read", "code"]`: 화이트리스트

## Agent 등록

Agent JSON 파일은 `~/.kiro/agents/`에 있어야 Kiro CLI에 등록됨.

```bash
# 소스 → 런타임 복사
cp templates/local/*.json ~/.kiro/agents/
```

- 소스: `templates/local/` (git 관리)
- 런타임: `~/.kiro/agents/` (Kiro CLI가 읽는 위치)
- 수정 시 양쪽 동기화 필요

## ListAgents 캐싱

- ListAgents는 세션 시작 시 캐싱됨
- 새 Agent 추가 후 현재 세션에서는 ListAgents에 안 나옴
- InvokeSubagents는 캐시와 무관하게 즉시 동작 가능
- 새 Agent 확인: 새 세션 시작 또는 InvokeSubagents로 직접 호출

## 현재 등록된 Agent

| Agent | 파일 | 역할 |
|-------|------|------|
| agent-builder | agent-builder.json | 코드 생성 + delegate |
| review | review-agent.json | 코드 리뷰 (체크리스트 기반) |
| deployment | deployment-agent.json | ECR/AgentCore 배포 |

## delegate 워크플로

```
agent-builder → review-agent → deployment-agent
```

- agent-builder가 use_subagent로 review/deployment에 위임
- subagent는 독립 context → relevant_context로 정보 전달

## Last Updated
Mickey 17 - 2026-02-19
