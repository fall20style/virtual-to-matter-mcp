import os
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from interfaces import mcp_tools
from services.real_service import RealHomeService

RUN_MODE = os.getenv("RUN_MODE", "virtual")
real_service = RealHomeService(mode=RUN_MODE)
mcp_tools.home_service = real_service

# MCP Streamable HTTP 서브 앱 생성 (경로: /mcp)
mcp_http_app = mcp_tools.mcp.streamable_http_app(streamable_http_path="/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 백그라운드 워커 풀(3개 워커) 시작
    real_service.start()
    # 2. MCP v2 세션 매니저 시작
    async with mcp_tools.mcp.session_manager.run():
        yield
    # 3. 서버 종료 시 워커 풀 정리
    real_service.stop()


app = FastAPI(title="Virtual-to-Matter MCP Home Controller", lifespan=lifespan)

# /mcp 경로로 외부 MCP 클라이언트 접속 허용
app.mount("/mcp", mcp_http_app)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "mode": RUN_MODE,
        "devices": real_service.devices,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
