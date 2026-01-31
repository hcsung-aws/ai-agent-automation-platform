FROM public.ecr.aws/docker/library/python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY agentcore_app.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the agent
CMD ["python", "agentcore_app.py"]
