# 튜토리얼: 뉴스 Agent 시스템 구축

Agent Builder를 사용하여 뉴스 크롤링 → 분석/요약 → 챗봇 웹서비스를 단계별로 구축하는 예제입니다.

## 완성 후 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│  localhost:8000 (Chainlit)                              │
│  ┌───────────┐    ┌────────────────────────────────┐    │
│  │ Chainlit  │───▶│ Supervisor Agent                │    │
│  │ UI        │    │   ├── Guide Agent              │    │
│  │ (app.py)  │◀───│   ├── News Crawler Agent       │    │
│  └───────────┘    │   │    ├── crawl_headlines     │    │
│                   │   │    ├── list_news_files      │    │
│                   │   │    └── get_news_by_date     │    │
│                   │   └── News Analyst Agent        │    │
│                   │        └── load_news            │    │
│                   └──────────┬─────────────────────┘    │
│                              │                          │
│  ┌───────────────┐    ┌──────▼──────┐                   │
│  │ news-data/    │    │ Amazon      │                   │
│  │ YYYY-MM-DD.json│   │ Bedrock     │                   │
│  └───────────────┘    └─────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

## 사전 준비

```bash
# 1. 로컬 환경 설치 (아직 안 했다면)
cd templates/local
./setup.sh
source ../../.venv/bin/activate

# 2. feedparser 설치
pip install feedparser

# 3. 프로젝트 생성
./templates/new-project.sh local news-agent
cd examples/local/news-agent
```

## 소요 시간

| Phase | 작업 | 소요 |
|-------|------|------|
| 1 | 뉴스 크롤링 Agent | 15분 |
| 2 | 뉴스 분석 Agent | 15분 |
| 3 | Supervisor 연결 + 웹서비스 | 10분 |
| 4 | 피드백 기반 개선 | 지속적 |

---

## Phase 1: 뉴스 크롤링 Agent

### 목표

Google News RSS에서 헤드라인을 가져와 날짜별 JSON 파일로 저장하는 Agent

### Agent Builder 실행

```bash
cd examples/local/news-agent
source ../../../.venv/bin/activate
kiro chat --agent agent-builder
```

### 프롬프트 (복사해서 입력)

```
뉴스 크롤링 Agent를 만들어줘.

파일 위치: templates/local/agents/news_crawler_agent.py

기능 (각각 @tool로):
1. crawl_headlines: Google News RSS(https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko)에서 
   헤드라인을 가져와서 news-data/YYYY-MM-DD.json에 저장. feedparser 사용.
   저장 형식: [{"title": "...", "link": "...", "published": "..."}]
2. list_news_files: news-data/ 폴더의 파일 목록 조회
3. get_news_by_date: 특정 날짜의 뉴스 헤드라인 조회

Agent 생성 함수: create_news_crawler_agent()
config.py에서 MODEL_ID, REGION_NAME import 필수.
NEWS_DATA_DIR = "news-data" 상수 사용.
```

### 예상 결과

Agent Builder가 `templates/local/agents/news_crawler_agent.py`를 생성합니다.

### 테스트

```bash
cd examples/local/news-agent
python -c "
import sys; sys.path.insert(0, '.')
from agents.news_crawler_agent import crawl_headlines, list_news_files
print(crawl_headlines())
print(list_news_files())
"
```

확인 사항:
- [ ] `news-data/YYYY-MM-DD.json` 파일이 생성되었는가
- [ ] JSON에 title, link, published 필드가 있는가
- [ ] `list_news_files()`가 파일 목록을 반환하는가

### 문제 발생 시

Agent Builder에게 추가 요청:

```
crawl_headlines 실행 시 [에러 메시지] 에러가 발생해.
news-data/ 디렉토리가 없으면 자동 생성하도록 수정해줘.
```

---

## Phase 2: 뉴스 분석/요약 Agent

### 목표

크롤링된 뉴스 데이터를 읽어서 LLM이 카테고리 분류 + 주요 뉴스 요약을 수행하는 Agent

### 프롬프트 (같은 agent-builder 세션에서 계속)

```
뉴스 분석 Agent를 만들어줘.

파일 위치: templates/local/agents/news_analyst_agent.py

기능 (@tool):
1. load_news: news-data/YYYY-MM-DD.json에서 뉴스 데이터를 읽어서 반환.
   날짜 파라미터 필수. 파일이 없으면 안내 메시지 반환.

Agent 생성 함수: create_news_analyst_agent()
config.py에서 MODEL_ID, REGION_NAME import 필수.

SYSTEM_PROMPT에 다음 분석 형식을 지정:
1. 📰 오늘의 주요 뉴스 TOP 5 (중요도 순)
2. 📊 카테고리별 분류 (정치/경제/사회/IT·과학/국제/연예·스포츠)
3. 💡 핵심 키워드 3개

도구는 데이터 로딩만 담당하고, 분석은 LLM이 수행하도록 설계해줘.
```

### 테스트

```bash
cd examples/local/news-agent
python -c "
import sys; sys.path.insert(0, '.')
from agents.news_analyst_agent import create_news_analyst_agent
agent = create_news_analyst_agent()
from datetime import datetime
today = datetime.now().strftime('%Y-%m-%d')
print(agent(f'{today} 뉴스 분석해줘'))
"
```

확인 사항:
- [ ] Phase 1에서 저장한 뉴스 데이터를 정상적으로 로딩하는가
- [ ] TOP 5 / 카테고리 / 키워드 형식으로 응답하는가
- [ ] 뉴스가 없는 날짜 요청 시 안내 메시지가 나오는가

### 개선 요청 예시

```
분석 결과에서 카테고리 분류가 부정확해.
SYSTEM_PROMPT에 각 카테고리의 판단 기준을 더 구체적으로 추가해줘.
예: IT·과학 = AI, 반도체, 스마트폰, 소프트웨어, 우주 등
```

---

## Phase 3: Supervisor 연결 + 웹서비스

### 목표

두 Agent를 Supervisor에 연결하여 Chainlit 웹 UI에서 대화형으로 사용

### 프롬프트

```
news_crawler_agent와 news_analyst_agent를 Supervisor에 연결해줘.

수정 파일: templates/local/agents/supervisor.py

추가할 내용:
1. news_crawler_agent의 lazy init + ask_news_crawler 도구
2. news_analyst_agent의 lazy init + ask_news_analyst 도구
3. tools 배열에 두 도구 추가
4. SYSTEM_PROMPT에 Agent 설명 추가:
   - News Crawler: 뉴스 수집, 크롤링, 저장된 뉴스 목록 조회
   - News Analyst: 뉴스 요약, 분석, 카테고리 분류

위임 규칙:
- "뉴스 가져와", "크롤링" → ask_news_crawler
- "뉴스 분석", "요약", "트렌드" → ask_news_analyst
- "뉴스 가져와서 분석해줘" → ask_news_crawler → ask_news_analyst 순차 호출
```

### 테스트

```bash
cd examples/local/news-agent
chainlit run app.py --port 8000
```

브라우저에서 http://localhost:8000 접속 후 테스트:

| 입력 | 예상 동작 |
|------|----------|
| "오늘 뉴스 가져와" | Crawler → RSS 크롤링 → 저장 |
| "오늘 뉴스 분석해줘" | Analyst → 데이터 로딩 → LLM 분석 |
| "저장된 뉴스 목록 보여줘" | Crawler → 파일 목록 반환 |
| "뉴스 가져와서 분석해줘" | Crawler → Analyst 순차 호출 |
| "최근 IT 뉴스 트렌드는?" | Analyst → 분석 |

확인 사항:
- [ ] Supervisor가 요청을 올바른 Agent에게 위임하는가
- [ ] 순차 호출(크롤링 → 분석)이 정상 동작하는가
- [ ] 👍/👎 피드백 버튼이 표시되는가

---

## Phase 4: 피드백 기반 개선

### 피드백 수집

Chainlit UI에서 응답에 👍/👎를 클릭하면 자동으로 피드백이 수집됩니다.
👍 클릭 시 사례 저장을 제안합니다.

### 개선 사이클

```
1. 사용 중 불만족스러운 응답에 👎
2. 패턴 파악 (예: "카테고리가 부정확", "요약이 너무 길다")
3. Agent Builder에게 개선 요청:
```

개선 프롬프트 예시:

```
news_analyst_agent의 SYSTEM_PROMPT를 개선해줘.

현재 문제:
- 요약이 너무 길어서 핵심을 파악하기 어려움
- 카테고리 분류가 부정확함

개선 방향:
- TOP 5 뉴스는 각각 1줄 요약으로 제한
- 카테고리별 뉴스 수를 표시
- 전체 응답을 500자 이내로 제한
```

### 기능 확장 예시

```
news_crawler_agent에 도구를 추가해줘.

새 도구: crawl_by_topic
- Google News RSS의 토픽별 URL 지원
  - 경제: https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNR2RtY0hNUkEoQUFQAQ?hl=ko&gl=KR&ceid=KR:ko
  - IT: https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNREp0Y0RjUkEoQUFQAQ?hl=ko&gl=KR&ceid=KR:ko
- topic 파라미터로 카테고리 선택
- 저장 파일명: news-data/YYYY-MM-DD-{topic}.json
```

---

## 주의사항

1. **RSS vs 크롤링**: Google News HTML 직접 크롤링은 ToS 위반 가능성이 있으므로 RSS 피드를 사용합니다
2. **RSS 제한**: RSS는 최신 헤드라인만 제공합니다. 과거 뉴스는 매일 크롤링하여 축적하는 방식이 현실적입니다
3. **의존성**: `feedparser`를 `templates/local/agents/requirements.txt`에 추가해야 합니다
4. **AWS 배포 시**: `news-data/`를 S3로 전환하면 영속적 저장이 가능합니다 (기존 KB S3 패턴 활용)

## 프로젝트 생성 명령어

```bash
# 프로젝트 생성
./templates/new-project.sh local news-agent

# 디렉토리 이동
cd examples/local/news-agent
source ../../../.venv/bin/activate
```

## 관련 문서

- [QUICKSTART-LOCAL.md](QUICKSTART-LOCAL.md) — 로컬 환경 설치
- [TUTORIAL-FIRST-AGENT.md](TUTORIAL-FIRST-AGENT.md) — Agent Builder 기본 사용법
- [TUTORIAL-FEEDBACK.md](TUTORIAL-FEEDBACK.md) — 피드백 루프 설정
- [TUTORIAL-MULTI-AGENT.md](TUTORIAL-MULTI-AGENT.md) — Multi-Agent 구성
