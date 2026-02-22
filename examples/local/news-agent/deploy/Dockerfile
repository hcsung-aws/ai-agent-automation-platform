FROM python:3.12-slim

WORKDIR /app

# 의존성 설치
COPY deploy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY config.py .
COPY app.py .
COPY feedback_store.py .
COPY chainlit.md .
COPY agents/ agents/
COPY .chainlit/ .chainlit/

# news-data 디렉토리 생성 (런타임 저장용)
RUN mkdir -p news-data knowledge-base/cases

EXPOSE 8000
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
