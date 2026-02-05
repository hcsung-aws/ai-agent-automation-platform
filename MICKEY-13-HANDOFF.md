# Mickey 13 Handoff Document

## Quick Start for Mickey 14

### 1. Current Status
- 로컬 템플릿 테스트 완료 ✅
- 문서/테스트 보강 완료 ✅
- S3 KB 직접 검색 지원 추가 ✅

### 2. What's Done This Session

**KB 시스템 개선:**
- 폴백 순서: Bedrock KB → S3 → 로컬
- 점진적 전환 경로 설계 (로컬 → S3 → Bedrock KB)
- CDK에 KB용 S3 버킷 추가

**문서/테스트:**
- pytest 15개 테스트 작성
- README 데모 시나리오 추가
- TROUBLESHOOTING.md 생성
- setup.sh 에러 처리 강화

### 3. KB 검색 우선순위

```
1. KNOWLEDGE_BASE_ID 설정 → Bedrock KB (시맨틱 검색)
2. KB_S3_BUCKET 설정 → S3 직접 검색 (키워드)
3. LOCAL_KB_PATH 존재 → 로컬 파일 검색 (키워드)
```

### 4. 로드맵 현황

```
v1.1 피드백 수집      ████████████ 100% ✅
v1.2 Agent Builder   ████████████ 100% ✅
v1.3 자동 개선        ████████████ 100% ✅
스타터 킷 패키징      ████████████ 100% ✅
로컬 템플릿 테스트    ████████████ 100% ✅
문서/테스트 보강      ████████████ 100% ✅
AWS CDK 배포 테스트   ░░░░░░░░░░░░   0%
v2.0 스케줄러/알림    ░░░░░░░░░░░░   0%
```

### 5. Next Steps
1. AWS CDK 배포 테스트
2. v2.0 스케줄러 구현 (EventBridge + Lambda)

### 6. Key Files
```
src/tools/kb_tools.py                    # KB 검색 (Bedrock/S3/로컬)
templates/local/agents/guide_agent.py    # Guide Agent (KB 연동)
templates/aws/cdk/stacks/infrastructure_stack.py  # KB S3 버킷
tests/                                   # pytest 테스트
docs/TROUBLESHOOTING.md                  # 문제 해결 가이드
```

### 7. Useful Commands
```bash
# 로컬 실행
cd templates/local
./setup.sh
chainlit run app.py --port 8000

# 테스트
pytest tests/ -v

# AWS 배포
cd templates/aws
./deploy.sh

# KB S3 동기화
aws s3 sync knowledge-base/ s3://$KB_BUCKET/knowledge-base/
```

### 8. Lessons Learned
- 점진적 전환 설계: S3 직접 검색을 중간 단계로 추가하면 Bedrock KB 없이도 AWS 환경에서 영속적 KB 사용 가능

---
Mickey 13 → Mickey 14
