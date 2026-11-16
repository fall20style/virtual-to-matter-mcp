import os
from contextlib import asynccontextmanager
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from interfaces import mcp_tools
from services.real_service import RealHomeService

RUN_MODE = os.getenv("RUN_MODE", "virtual")
real_service = RealHomeService(mode=RUN_MODE)
mcp_tools.home_service = real_service

mcp_http_app = mcp_tools.mcp.streamable_http_app(streamable_http_path="/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    real_service.start()
    async with mcp_tools.mcp.session_manager.run():
        yield
    real_service.stop()


app = FastAPI(title="Virtual-to-Matter MCP Home Controller", lifespan=lifespan)
app.mount("/mcp", mcp_http_app)


# 웹 GUI 대시보드 화면 제공
@app.get("/gui", response_class=HTMLResponse)
async def serve_dashboard():
    html_path = Path(__file__).parent / "templates" / "dashboard.html"
    return html_path.read_text(encoding="utf-8")


# 웹 GUI 버튼 클릭 시 백그라운드 워커 큐에 명령 등록
@app.post("/api/control")
async def gui_control_device(device_id: str, action: str, value: int | None = None):
    task_id = await real_service.execute_now(device_id, action, value)
    return {"status": "queued", "task_id": task_id}


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "mode": RUN_MODE,
        "devices": real_service.devices,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8100, reload=True)
