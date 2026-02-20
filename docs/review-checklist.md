# Agent Code Review Checklist

review-agent가 코드 리뷰 시 확인할 항목입니다.

## 1. config.py 사용

- [ ] 모델 ID가 `config.MODEL_ID`를 사용하는가 (하드코딩 금지)
- [ ] region이 `config.REGION_NAME`을 사용하는가 (하드코딩 금지)
- [ ] `from config import MODEL_ID, REGION_NAME` import가 있는가

**위반 예시:**
```python
# ❌ 하드코딩
model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
region_name="us-east-1"

# ✅ config 사용
from config import MODEL_ID, REGION_NAME
model_id=MODEL_ID
region_name=REGION_NAME
```

## 2. @tool 데코레이터 및 docstring

- [ ] 모든 도구 함수에 `@tool` 데코레이터가 있는가
- [ ] docstring에 함수 설명이 있는가
- [ ] docstring에 `Args:` 섹션이 있는가 (파라미터 설명)
- [ ] docstring에 `Returns:` 섹션이 있는가
- [ ] 반환 타입이 `str`인가

**필수 패턴:**
```python
@tool
def my_tool(param: str) -> str:
    """도구 설명.
    
    Args:
        param: 파라미터 설명
    
    Returns:
        반환값 설명
    """
```

## 3. SYSTEM_PROMPT 품질

- [ ] 역할과 담당 영역이 명시되어 있는가
- [ ] 각 도구를 **언제** 사용해야 하는지 명시되어 있는가
- [ ] 응답 원칙 (언어, 형식)이 있는가

**핵심**: 도구를 tools에 등록해도 SYSTEM_PROMPT에 사용 지침이 없으면 Agent가 호출하지 않음

## 4. Agent 생성 패턴

- [ ] `create_xxx_agent() -> Agent` 함수가 있는가
- [ ] Agent만 반환하는가 (tuple 아님)
- [ ] `BedrockModel` 사용 시 config에서 import하는가

**필수 패턴:**
```python
def create_xxx_agent() -> Agent:
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION_NAME)
    return Agent(model=model, system_prompt=SYSTEM_PROMPT, tools=[...])
```

## 5. Supervisor 연결

- [ ] `ask_xxx_agent` 도구 함수가 있는가
- [ ] supervisor.py의 tools 리스트에 추가되었는가
- [ ] SYSTEM_PROMPT에 새 Agent 설명이 추가되었는가

## 6. 보안

- [ ] 하드코딩된 AWS 키/시크릿이 없는가
- [ ] IAM 권한이 최소 권한 원칙을 따르는가
- [ ] 민감 정보가 로그에 출력되지 않는가

## 7. 에러 핸들링

- [ ] boto3 호출에 try/except가 있는가
- [ ] 에러 시 사용자에게 의미 있는 메시지를 반환하는가
- [ ] 외부 API 호출 실패 시 폴백이 있는가

## 8. 기존 패턴 일관성

- [ ] 파일 위치가 `templates/local/agents/`인가
- [ ] 모듈 docstring이 있는가 (파일 상단 설명)
- [ ] logging 설정이 기존 Agent와 동일한가
- [ ] boto3 client를 싱글톤 패턴으로 생성하는가 (`_get_xxx_client()`)

## 리뷰 결과 형식

```
## 리뷰 결과: [파일명]

### ✅ 통과 항목
- (통과한 항목 나열)

### ⚠️ 수정 필요
- (수정이 필요한 항목 + 구체적 수정 방법)

### 💡 개선 제안 (선택)
- (필수는 아니지만 개선하면 좋은 항목)
```
