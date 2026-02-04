# Mickey 10 Session Log
Date: 2026-02-04 13:28 ~ 16:06

## Session Goal
공통 Knowledge Base 구현 (메타데이터 필터링 기반)

## Previous Context (Mickey 9)
- 테스트 모드 표시 아키텍처 구현 완료
- Mickey 시스템 프롬프트 v5.3 업데이트

## Progress

### Completed
- ✅ 현재 KB 구조 분석 및 문제점 파악
- ✅ AWS Bedrock KB 메타데이터 필터링 기능 조사
- ✅ 공통 KB 구현 계획 수립
- ✅ S3 knowledge-base/ 폴더 구조 생성
  - common/ (공통 지식)
  - devops/ (기존 문서 이동)
- ✅ 메타데이터 파일 생성 (category 태그)
- ✅ Data Source inclusionPrefix 변경
- ✅ IAM 정책 업데이트 (knowledge-base/* 경로 추가)
- ✅ KB Sync 실행 (3개 문서 인덱싱 성공)
- ✅ kb_tools.py 확장 (메타데이터 필터링 함수)
- ✅ 각 Agent에 도메인별 KB 도구 연결
- ✅ 테스트 및 검증
- ✅ Git 커밋 및 푸시

## Key Decisions

### Decision 1: KB 문서 분류 방식
- Problem: 하나의 KB에서 Agent별로 필요한 문서만 검색하고 싶음
- Options:
  - A: AWS Bedrock KB 메타데이터 필터링 (선택)
  - B: 로컬 파일 기반 KB
- Chosen: Option A
- Reasoning: 벡터 검색 품질, 확장성, 기존 인프라 활용

### Decision 2: Agent별 KB 접근 범위
- Problem: 공통 지식은 모든 Agent가, 도메인 지식은 해당 Agent만 접근
- Chosen: 도메인 검색 시 common + 해당 도메인 문서 모두 반환
- Reasoning: 공통 맥락 없이 도메인 지식만으로는 불완전

## Files Modified

### Modified
- src/tools/kb_tools.py (메타데이터 필터링 함수 추가)
- src/agent/devops_agent.py (search_devops_knowledge 연결)
- src/agent/analytics_agent.py (search_analytics_knowledge 연결)
- src/agent/monitoring_agent.py (search_monitoring_knowledge 연결)
- src/agent/supervisor_agent.py (search_common_knowledge 연결)

### AWS Resources
- S3: knowledge-base/ 폴더 구조 생성
- IAM: AmazonBedrockS3PolicyForKnowledgeBase_p2y8n v2 (경로 추가)
- Bedrock KB: Data Source inclusionPrefix 변경

## Lessons Learned

### Lesson 1: IAM 정책 경로 제한
- Problem: KB Sync 실패 (403 Access Denied)
- Cause: IAM 정책이 기존 경로(game-log-analytics/*)만 허용
- Solution: 새 경로(knowledge-base/*) 추가
- Avoid: 경로 변경 시 IAM 정책 확인 누락

## Context Window
- Current: ~25%
- Status: Safe

## Next Steps
1. analytics/, monitoring/ 폴더에 도메인별 문서 추가
2. 공통 문서 확장 (용어집, 에스컬레이션 정책 등)
3. 실제 운영 중 KB 활용 패턴 모니터링
