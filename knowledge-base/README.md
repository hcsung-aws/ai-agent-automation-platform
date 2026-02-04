# 로컬 Knowledge Base

Bedrock KB 접근 실패 시 폴백으로 사용되는 로컬 문서 저장소입니다.

## 디렉토리 구조

```
knowledge-base/
├── common/       # 공통 지식 (조직 정보, 정책 등)
├── devops/       # DevOps 가이드
├── analytics/    # Analytics 가이드
└── monitoring/   # Monitoring 가이드
```

## 사용 방법

1. 각 카테고리 폴더에 `.md` 파일 추가
2. `add_kb_document()` 도구 사용 시 자동으로 로컬 + S3 동시 저장

## 환경 변수

```bash
# 기본값: ./knowledge-base
export LOCAL_KB_PATH=/path/to/custom/kb
```

## 동작 방식

- Bedrock KB 접근 성공 → Bedrock 결과 반환
- Bedrock KB 접근 실패 → 로컬 파일에서 키워드 검색
