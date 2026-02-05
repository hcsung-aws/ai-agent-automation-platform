# 테스트 가이드

## 테스트 실행

```bash
# 가상환경 활성화
source .venv/bin/activate

# 전체 테스트 실행
pytest tests/ -v

# 특정 파일만 실행
pytest tests/test_kb_tools.py -v
pytest tests/test_guide_agent.py -v
```

## 테스트 구조

```
tests/
├── conftest.py           # 공통 fixtures
├── test_kb_tools.py      # KB 도구 테스트
└── test_guide_agent.py   # Guide Agent 테스트
```

## 테스트 항목

### test_kb_tools.py

| 테스트 | 설명 |
|--------|------|
| `test_search_finds_matching_content` | 로컬 KB 키워드 검색 |
| `test_search_with_category_filter` | 카테고리별 검색 |
| `test_uses_local_when_kb_id_not_set` | Bedrock 미설정 시 로컬 폴백 |
| `test_falls_back_to_local_on_bedrock_error` | Bedrock 오류 시 로컬 폴백 |
| `test_saves_to_local_kb` | 문서 저장 |

### test_guide_agent.py

| 테스트 | 설명 |
|--------|------|
| `test_search_finds_documents` | 로컬 KB 검색 |
| `test_uses_local_kb_when_no_bedrock` | Bedrock 미설정 시 동작 |
| `test_returns_structure` | 프로젝트 구조 반환 |
| `test_returns_next_step_for_install` | 다음 단계 안내 |

## 새 테스트 추가

```python
# tests/test_new_feature.py
import pytest

class TestNewFeature:
    def test_something(self, temp_kb_dir):
        """테스트 설명."""
        # temp_kb_dir: 임시 KB 디렉토리 fixture
        assert True
```
