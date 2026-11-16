import re
import asyncio
import pytest_asyncio

from interfaces import mcp_tools
from services.real_service import RealHomeService
from services.worker_pool import task_db


@pytest_asyncio.fixture(autouse=True)
async def setup_real_service():
    service = RealHomeService(mode="actual")
    service.start()
    mcp_tools.home_service = service
    yield service
    service.stop()


def extract_task_id(response_text: str) -> str:
    match = re.search(r"작업 ID:\s*([a-f0-9]{8})", response_text)
    assert match is not None
    return match.group(1)


# TC-REAL-01: Matter 프로토콜 전등 제어 및 워커 풀 실행 검증
async def test_real_matter_light_control(setup_real_service):
    res = await mcp_tools.control_device(device_id="light_living", action="set_brightness", value=75)
    task_id = extract_task_id(res)

    await asyncio.sleep(0.8)

    status_text = await mcp_tools.get_task_result(task_id)
    assert "COMPLETED" in status_text
    assert "[Matter ACK -> matter://node-01]" in status_text
    assert setup_real_service.devices["light_living"]["brightness"] == 75


# TC-REAL-02: IoTivity 프로토콜 TV 채널 변경 검증
async def test_real_iotivity_tv_control(setup_real_service):
    res = await mcp_tools.control_device(device_id="tv_main", action="set_channel", value=24)
    task_id = extract_task_id(res)

    await asyncio.sleep(0.8)

    status_text = await mcp_tools.get_task_result(task_id)
    assert "COMPLETED" in status_text
    assert "[IoTivity OCF_OK -> ocf://tv/main]" in status_text
    assert setup_real_service.devices["tv_main"]["channel"] == 24


# TC-REAL-03: 워커 풀 동시성 제어 (3개 워커 병렬 처리, 초과 2개 큐 대기)
async def test_real_worker_pool_concurrency():
    task_ids = []
    for _ in range(5):
        res = await mcp_tools.control_device(device_id="sensor_env", action="read")
        task_ids.append(extract_task_id(res))

    await asyncio.sleep(0.1)

    statuses = [task_db[tid]["status"] for tid in task_ids]
    assert statuses.count("RUNNING") == 3
    assert statuses.count("QUEUED") == 2

    await asyncio.sleep(1.2)
    assert all(task_db[tid]["status"] == "COMPLETED" for tid in task_ids)
