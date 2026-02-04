# Mickey 10 Handoff Document

## Quick Start for Mickey 11

### 1. Current Status
- 공통 Knowledge Base 구현 완료 ✅
- 메타데이터 필터링 기반 문서 분류 동작 확인

### 2. What's Done This Session
- S3 knowledge-base/ 폴더 구조 (common/, devops/)
- 메타데이터 기반 문서 분류 (category 태그)
- kb_tools.py 확장: 도메인별 검색 함수
- 각 Agent에 KB 도구 연결

### 3. KB 구조

```
S3: devops-agent-kb-965037532757/knowledge-base/
├── common/
│   └── org-overview.md (category=common)
└── devops/
    ├── game-log-analytics-operations-manual.md (category=devops)
    └── game-log-analytics-troubleshooting.md (category=devops)
```

### 4. Agent별 KB 접근

| Agent | KB 도구 | 검색 범위 |
|-------|---------|----------|
| Supervisor | search_common_knowledge | common만 |
| DevOps | search_devops_knowledge | common + devops |
| Analytics | search_analytics_knowledge | common + analytics |
| Monitoring | search_monitoring_knowledge | common + monitoring |

### 5. 문서 추가 방법

```bash
# 1. 문서 업로드
aws s3 cp new-doc.md s3://devops-agent-kb-965037532757/knowledge-base/[category]/

# 2. 메타데이터 파일 생성
echo '{"metadataAttributes":{"category":"[category]","doc_type":"guide"}}' | \
  aws s3 cp - s3://devops-agent-kb-965037532757/knowledge-base/[category]/new-doc.md.metadata.json

# 3. KB Sync
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id H50SNRJBFF \
  --data-source-id OSFG10XDDN \
  --region us-east-1
```

### 6. Next Steps
1. analytics/, monitoring/ 폴더에 도메인별 문서 추가
2. 공통 문서 확장 (용어집, 에스컬레이션 정책)
3. KB 활용 패턴 모니터링

### 7. Key Files
```
src/tools/kb_tools.py              # KB 검색 함수 (메타데이터 필터링)
src/agent/*_agent.py               # 각 Agent (KB 도구 연결됨)
```

---
Mickey 10 → Mickey 11
