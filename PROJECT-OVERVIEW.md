# Project Overview

## Project Name
AI Developer Mickey Agents - AgentCore 기반 Multi-Agent 협업 시스템

## Goal
조직의 업무 프로세스를 AI Agent 기반으로 전환하는 플랫폼 구축
- 개별 Agent: 챗봇 + A2A 협업
- 점진적 학습: 지식 누적 + 행동 패턴 기반 지침 생성
- 자기 개선: 실행 기록 → 사람 검토 → 개선

## Scope
- In scope:
  - DevOps Agent, 데이터분석 Agent 구현
  - Multi-Agent 협업 (Supervisor)
  - 실행 기록 저장 및 검토 UI
  - 지식 베이스 연동 (RAG)
- Out of scope (PoC):
  - 행동 패턴 자동 분석 (Phase 2)
  - 도구 자동 업데이트 제안 (Phase 2)
  - 프로덕션 보안 강화 (Phase 4)

## Constraints
- Technical: AWS Bedrock 기반, us-east-1 리전
- Time: 2주 PoC
- Resources: 제한 없음 (PoC 예산)

## Success Criteria
- [x] DevOps Agent 동작 (도구 6개)
- [x] 데이터분석 Agent 동작 (도구 10개)
- [x] Multi-Agent 협업 시나리오 동작
- [x] 실행 기록 저장 및 조회 가능
- [x] 챗봇 UI로 Agent와 대화 가능

## Current Status
- Session: Mickey 7
- Progress: v1.2 Agent Builder 완료
- Next: v1.3 자동 개선 제안

## Last Updated
Mickey 7 - 2026-02-01
