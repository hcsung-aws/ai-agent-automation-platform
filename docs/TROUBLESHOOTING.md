# 🔧 트러블슈팅 가이드

자주 발생하는 문제와 해결 방법을 정리했습니다.

---

## 설치 관련

### Python 버전 오류

**증상:**
```
❌ Python 3.10 이상이 필요합니다. 현재: 3.8
```

**해결:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv

# macOS (Homebrew)
brew install python@3.10

# 버전 확인
python3 --version
```

### pip 설치 실패

**증상:**
```
ModuleNotFoundError: No module named 'pip'
```

**해결:**
```bash
python3 -m ensurepip --upgrade
# 또는
curl https://bootstrap.pypa.io/get-pip.py | python3
```

### 가상환경 생성 실패

**증상:**
```
Error: Command '[...venv...]' returned non-zero exit status 1
```

**해결:**
```bash
# venv 모듈 설치
sudo apt install python3.10-venv  # Ubuntu
# 또는
pip3 install virtualenv
virtualenv .venv
```

---

## AWS 관련

### AWS 자격증명 오류

**증상:**
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**해결:**
```bash
# 자격증명 설정
aws configure
# Access Key ID, Secret Access Key, Region 입력

# 확인
aws sts get-caller-identity
```

### Bedrock 모델 접근 오류

**증상:**
```
AccessDeniedException: You don't have access to the model
```

**해결:**
1. AWS 콘솔 → Bedrock → Model access
2. Claude 3.5 Sonnet 모델 활성화 요청
3. 승인 후 재시도 (보통 즉시 승인)

### Bedrock KB 접근 실패

**증상:**
```
⚠️ Bedrock KB 접근 실패: ResourceNotFoundException
```

**해결:**
- `KNOWLEDGE_BASE_ID` 환경변수 확인
- KB가 실제로 존재하는지 AWS 콘솔에서 확인
- 미설정 시 로컬 KB 폴백 사용 (정상 동작)

---

## 실행 관련

### 포트 충돌

**증상:**
```
OSError: [Errno 98] Address already in use
```

**해결:**
```bash
# 다른 포트 사용
chainlit run app.py --port 8001

# 또는 기존 프로세스 종료
lsof -i :8000
kill -9 <PID>
```

### 모듈 import 오류

**증상:**
```
ModuleNotFoundError: No module named 'strands'
```

**해결:**
```bash
# 가상환경 활성화 확인
source .venv/bin/activate

# 의존성 재설치
pip install strands-agents chainlit boto3
```

### Agent 응답 없음

**증상:**
- 질문 후 응답이 오지 않음
- 로딩만 계속됨

**해결:**
1. AWS 자격증명 확인
2. Bedrock 모델 접근 권한 확인
3. 네트워크 연결 확인
4. 로그 확인: `chainlit run app.py --port 8000 --debug`

---

## Knowledge Base 관련

### 로컬 KB 검색 안 됨

**증상:**
```
관련 문서를 찾지 못했습니다.
```

**해결:**
1. `knowledge-base/` 디렉토리 존재 확인
2. `.md` 파일이 올바른 위치에 있는지 확인
3. 검색 키워드가 문서 내용에 포함되어 있는지 확인

```bash
# 디렉토리 구조 확인
ls -la knowledge-base/
ls -la knowledge-base/common/
```

### KB 동기화 실패 (AWS)

**증상:**
```
⚠️ KB 동기화 불가: KNOWLEDGE_BASE_ID가 설정되지 않았습니다.
```

**해결:**
```bash
# .env 파일에 설정 추가
KNOWLEDGE_BASE_ID=your-kb-id
KB_DATA_SOURCE_ID=your-ds-id
```

---

## 일반적인 디버깅 방법

### 1. 로그 확인

```bash
# 디버그 모드로 실행
chainlit run app.py --port 8000 --debug
```

### 2. 환경변수 확인

```bash
# 현재 설정 확인
cat .env
echo $KNOWLEDGE_BASE_ID
echo $LOCAL_KB_PATH
```

### 3. 테스트 실행

```bash
# 단위 테스트로 문제 범위 좁히기
pytest tests/test_kb_tools.py -v
pytest tests/test_guide_agent.py -v
```

### 4. Python 인터랙티브 테스트

```python
# 직접 함수 테스트
source .venv/bin/activate
python3

>>> from src.tools.kb_tools import _search_local
>>> _search_local("테스트", "devops")
```

---

## 도움 요청

위 방법으로 해결되지 않으면:

1. **GitHub Issues**: 에러 메시지와 환경 정보 포함하여 이슈 등록
2. **로그 첨부**: `--debug` 모드 로그 첨부
3. **환경 정보**: Python 버전, OS, AWS 리전 명시
