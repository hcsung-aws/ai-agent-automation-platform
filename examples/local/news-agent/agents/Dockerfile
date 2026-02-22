# AgentCore Runtime용 Strands Agent 컨테이너 (ARM64)
# Build context: news-agent/ (config.py 포함을 위해 상위 디렉토리 사용)
FROM --platform=linux/arm64 python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY agents/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Agent 코드 + 공유 설정 복사
COPY agents/ .
COPY config.py .

# AgentCore Runtime 요구사항: 0.0.0.0:8080
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
