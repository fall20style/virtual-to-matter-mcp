import os
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from interfaces import mcp_tools
from services.real_service import RealHomeService

# 환경 변수(RUN_MODE=actual 또는 virtual)에 따라 실행 모드 결정
RUN_MODE = os.getenv("RUN_MODE", "virtual")
real_service = RealHomeService(mode=RUN_MODE)
mcp_tools.home_service = real_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 워커 풀 가동
    real_service.start()
    yield
    # 서버 종료 시 워커 풀 정리
    real_service.stop()


app = FastAPI(title="Virtual-to-Matter MCP Home Controller", lifespan=lifespan)

# MCP v2 Streamable HTTP 앱 마운트 (/mcp 경로로 AI 에이전트 접속 가능)
app.mount("/mcp", mcp_tools.mcp.streamable_http_app())


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "mode": RUN_MODE,
        "devices": real_service.devices,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
