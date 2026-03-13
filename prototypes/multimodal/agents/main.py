"""AgentCore Runtime HTTP 엔트리포인트.

AgentCore Runtime 요구사항:
- POST /invocations: Agent 호출
- GET /ping: 헬스체크
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import sys
import os

# 컨테이너 환경에서 모듈 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supervisor import create_supervisor

app = FastAPI(title="AIOps Supervisor Agent")

# Supervisor Agent 인스턴스 (싱글톤)
_supervisor = None


def get_supervisor():
    global _supervisor
    if _supervisor is None:
        _supervisor = create_supervisor()
    return _supervisor


@app.post("/invocations")
async def invocations(request: Request):
    """AgentCore Runtime 메인 엔드포인트."""
    body = await request.json()
    prompt = body.get("prompt", "")
    
    supervisor = get_supervisor()
    response = supervisor(prompt)
    
    return JSONResponse(content={
        "response": str(response),
        "status": "success"
    })


@app.get("/ping")
async def ping():
    """AgentCore Runtime 헬스체크."""
    import time
    return JSONResponse(content={
        "status": "Healthy",
        "time_of_last_update": int(time.time())
    })
