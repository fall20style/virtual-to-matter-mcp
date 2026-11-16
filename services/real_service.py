import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional

from core.ports import HomeControllerPort
from services.worker_pool import (
    WORKER_POOL_SIZE,
    enqueue_device_task,
    enqueue_device_task_after_delay,
    start_worker_pool,
    stop_worker_pool,
    task_db,
)


class RealHomeService(HomeControllerPort):
    """비동기 워커 풀과 Matter/IoTivity 프로토콜 라우터를 결합한 실제 구현체"""

    def __init__(self, mode: str = "actual"):
        self.mode = mode  # "actual" 또는 "virtual"
        self.workers: list[asyncio.Task] = []
        self.devices = {
            "light_living": {
                "name": "거실 전등",
                "protocol": "matter",
                "endpoint": "matter://node-01",
                "power": "OFF",
                "brightness": 0,
            },
            "tv_main": {
                "name": "거실 스마트 TV",
                "protocol": "iotivity",
                "endpoint": "ocf://tv/main",
                "power": "OFF",
                "channel": 11,
            },
            "sensor_env": {
                "name": "거실 온습도 센서",
                "protocol": "matter",
                "endpoint": "matter://node-02",
                "temperature": 23.5,
                "humidity": 45,
            },
        }

    def start(self):
        if not self.workers:
            self.workers = start_worker_pool(executor=self._dispatch_to_protocol, pool_size=WORKER_POOL_SIZE)

    def stop(self):
        if self.workers:
            stop_worker_pool(self.workers)
            self.workers.clear()

    async def get_devices_summary(self) -> str:
        return f"[{self.mode.upper()} MODE] 등록된 기기 및 현재 상태: {self.devices}"

    async def execute_now(self, device_id: str, action: str, value: Optional[int] = None) -> str:
        task_id = str(uuid.uuid4())[:8]
        await enqueue_device_task(task_id, device_id, action, value)
        return task_id

    async def schedule_later(
        self, device_id: str, action: str, delay_seconds: int, value: Optional[int] = None
    ) -> str:
        task_id = str(uuid.uuid4())[:8]
        run_time = datetime.now() + timedelta(seconds=delay_seconds)
        task_db[task_id] = {
            "status": f"SCHEDULED ({run_time.strftime('%H:%M:%S')})",
            "worker": None,
            "result": None,
        }
        asyncio.create_task(
            enqueue_device_task_after_delay(delay_seconds, task_id, device_id, action, value)
        )
        return task_id

    async def get_task_status(self, task_id: str) -> dict:
        return task_db.get(
            task_id,
            {"status": "NOT_FOUND", "worker": None, "result": "존재하지 않는 작업 ID입니다."},
        )

    async def _dispatch_to_protocol(self, device_id: str, action: str, value: Optional[int]) -> str:
        device = self.devices.get(device_id)
        if not device:
            raise ValueError(f"등록되지 않은 기기 ID입니다: {device_id}")

        protocol = device["protocol"]

        if self.mode == "actual":
            if protocol == "matter":
                await asyncio.sleep(0.5)
                proto_log = f"[Matter ACK -> {device['endpoint']}]"
            elif protocol == "iotivity":
                await asyncio.sleep(0.5)
                proto_log = f"[IoTivity OCF_OK -> {device['endpoint']}]"
            else:
                raise NotImplementedError(f"지원하지 않는 프로토콜입니다: {protocol}")
        else:
            await asyncio.sleep(0.3)
            proto_log = "[Virtual GUI Sync]"

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
            device["temperature"] = 24.2
            device["humidity"] = 48

        return f"{proto_log} {device['name']}({device_id}) '{action}' 완료 -> 현재 상태: {device}"
