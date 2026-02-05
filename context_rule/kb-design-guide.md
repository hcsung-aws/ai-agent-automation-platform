# Knowledge Base 설계 지침

## 핵심 원칙

1. **KB 없이도 동작해야 한다** - 어떤 환경에서든 KB 설정 없이 바로 시작 가능
2. **KB는 나중에 쉽게 연결할 수 있어야 한다** - 환경변수만 설정하면 전환 완료

## 검색 우선순위 (폴백 체인)

```
1. Bedrock KB (KNOWLEDGE_BASE_ID 설정 시) → 시맨틱 검색
2. S3 (KB_S3_BUCKET 설정 시) → 키워드 검색
3. 로컬 파일 (LOCAL_KB_PATH) → 키워드 검색
```

## 환경별 권장 설정

| 환경 | 설정 | 검색 방식 |
|------|------|----------|
| 로컬 개발 | 없음 (기본값) | 로컬 파일 |
| AWS 초기 | KB_S3_BUCKET | S3 직접 검색 |
| AWS 프로덕션 | KNOWLEDGE_BASE_ID | Bedrock KB |

## 점진적 전환 경로

```
Phase 1: 로컬 개발
    knowledge-base/*.md 파일 추가
    → 즉시 검색 가능, 서버 재시작 불필요
        ↓
Phase 2: AWS 배포 (S3)
    aws s3 sync knowledge-base/ s3://bucket/knowledge-base/
    KB_S3_BUCKET=bucket 설정
    → 영속성 확보, 컨테이너 재시작과 무관
        ↓
Phase 3: Bedrock KB 연결 (선택)
    같은 S3 버킷을 Bedrock KB 데이터 소스로 연결
    KNOWLEDGE_BASE_ID=xxx 설정
    → 시맨틱 검색 활성화
```

## 환경변수

```bash
# Bedrock KB (선택 - 시맨틱 검색 필요 시)
KNOWLEDGE_BASE_ID=
KB_DATA_SOURCE_ID=

# S3 KB (선택 - AWS 환경에서 영속성 필요 시)
KB_S3_BUCKET=
KB_S3_PREFIX=knowledge-base

# 로컬 KB (기본값: ./knowledge-base)
LOCAL_KB_PATH=./knowledge-base
```

## 문서 추가 방법

### 로컬
```bash
echo "# 새 가이드" > knowledge-base/devops/new-guide.md
# 즉시 검색 가능
```

### S3
```bash
aws s3 cp new-guide.md s3://$KB_S3_BUCKET/knowledge-base/devops/
# 즉시 검색 가능
```

### Bedrock KB
```bash
# S3에 업로드 후 동기화 필요
aws bedrock-agent start-ingestion-job --knowledge-base-id $KNOWLEDGE_BASE_ID --data-source-id $KB_DATA_SOURCE_ID
# 30초~1분 후 검색 가능
```

## 설계 의도

- **진입 장벽 최소화**: 설정 없이 바로 시작
- **점진적 확장**: 필요에 따라 S3 → Bedrock KB로 전환
- **데이터 재사용**: S3 버킷을 Bedrock KB 데이터 소스로 그대로 연결
- **인터페이스 일관성**: 어떤 백엔드를 사용하든 동일한 API
