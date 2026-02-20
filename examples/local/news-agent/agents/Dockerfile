# AgentCore Runtime용 Strands Agent 컨테이너 (ARM64)
FROM --platform=linux/arm64 python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Agent 코드 복사
COPY . .

# AgentCore Runtime 요구사항: 0.0.0.0:8080
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
