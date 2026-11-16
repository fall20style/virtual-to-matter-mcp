import asyncio
import uuid
from typing import Optional
from core.ports import HomeControllerPort


class FakeHomeService(HomeControllerPort):
    """개발 및 테스트용 가짜(Simulation) 스마트홈 제어 객체"""

    def __init__(self):
        # 가상 기기 초기 상태
        self.virtual_devices = {
            "light_living": {"name": "거실 전등", "power": "OFF", "brightness": 0},
            "tv_main": {"name": "거실 스마트 TV", "power": "OFF", "channel": 11},
            "sensor_env": {"name": "거실 온습도 센서", "temperature": 23.5, "humidity": 45},
        }
        self.fake_tasks: dict = {}

    async def get_devices_summary(self) -> str:
        return f"[SIMULATION MODE] 현재 가상 기기 상태: {self.virtual_devices}"

    async def execute_now(self, device_id: str, action: str, value: Optional[int] = None) -> str:
        task_id = str(uuid.uuid4())[:8]
        self.fake_tasks[task_id] = {"status": "RUNNING", "worker": "FakeWorker-1", "result": None}

        # 가짜 비동기 실행 시뮬레이션 (백그라운드 태스크로 상태 변경)
        asyncio.create_task(self._simulate_execution(task_id, device_id, action, value, delay=0))
        return task_id

    async def schedule_later(
        self, device_id: str, action: str, delay_seconds: int, value: Optional[int] = None
    ) -> str:
        task_id = str(uuid.uuid4())[:8]
        self.fake_tasks[task_id] = {"status": f"SCHEDULED ({delay_seconds}s)", "worker": None, "result": None}

        asyncio.create_task(self._simulate_execution(task_id, device_id, action, value, delay=delay_seconds))
        return task_id

    async def get_task_status(self, task_id: str) -> dict:
        return self.fake_tasks.get(task_id, {"status": "NOT_FOUND", "worker": None, "result": "존재하지 않는 작업 ID입니다."})

    async def _simulate_execution(
        self, task_id: str, device_id: str, action: str, value: Optional[int], delay: int
    ):
        if delay > 0:
            await asyncio.sleep(delay)
        self.fake_tasks[task_id]["status"] = "RUNNING"
        self.fake_tasks[task_id]["worker"] = "FakeWorker-1"

        await asyncio.sleep(1)  # 가짜 처리 지연

        device = self.virtual_devices.get(device_id)
        if device:
            if action == "turn_on":
                device["power"] = "ON"
            elif action == "turn_off":
                device["power"] = "OFF"
            elif action == "set_brightness" and value is not None:
                device["power"] = "ON"
                device["brightness"] = value
            elif action == "set_channel" and value is not None:
                device["power"] = "ON"
                device["channel"] = value
            elif action == "read":
                device["temperature"] = 24.0

        self.fake_tasks[task_id]["status"] = "COMPLETED"
        self.fake_tasks[task_id]["result"] = f"[Simulated] {device_id} -> {action} 완료 (현재 상태: {device})"

