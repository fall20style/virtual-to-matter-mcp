import asyncio
import re
import pytest

from interfaces import mcp_tools
from services.fake_service import FakeHomeService


# 각 테스트마다 깨끗한 상태의 FakeHomeService 객체를 mcp_tools에 주입하는 픽스처
@pytest.fixture(autouse=True)
def inject_fresh_fake_service():
    fresh_service = FakeHomeService()
    mcp_tools.home_service = fresh_service
    return fresh_service


def extract_task_id(response_text: str) -> str:
    """MCP Tool 응답 문자열에서 8자리 작업 ID를 추출하는 헬퍼 함수"""
    match = re.search(r"작업 ID:\s*([a-f0-9]{8})", response_text)
    assert match is not None, f"응답에서 작업 ID를 찾을 수 없습니다: {response_text}"
    return match.group(1)


# TC-MCP-01: 전체 가상 기기 목록 및 초기 상태 조회 검증
async def test_tc01_get_home_devices():
    result = await mcp_tools.get_home_devices()
    assert "[SIMULATION MODE]" in result
    assert "light_living" in result
    assert "tv_main" in result
    assert "sensor_env" in result


# TC-MCP-02: 전등 즉시 제어 및 밝기 조절 검증
async def test_tc02_control_light_immediately(inject_fresh_fake_service):
    res = await mcp_tools.control_device(device_id="light_living", action="set_brightness", value=80)
    task_id = extract_task_id(res)

    # FakeHomeService의 1초 시뮬레이션 대기
    await asyncio.sleep(1.3)

    # 1. 작업 결과 조회 검증
    task_status = await mcp_tools.get_task_result(task_id=task_id)
    assert "COMPLETED" in task_status

    # 2. 실제 가상 전등 객체의 내부 상태가 변경되었는지 검증
    light_state = inject_fresh_fake_service.virtual_devices["light_living"]
    assert light_state["power"] == "ON"
    assert light_state["brightness"] == 80


# TC-MCP-03: 스마트 TV 채널 변경 제어 검증
async def test_tc03_control_tv_channel(inject_fresh_fake_service):
    res = await mcp_tools.control_device(device_id="tv_main", action="set_channel", value=7)
    task_id = extract_task_id(res)

    await asyncio.sleep(1.3)

    tv_state = inject_fresh_fake_service.virtual_devices["tv_main"]
    assert tv_state["power"] == "ON"
    assert tv_state["channel"] == 7

    task_status = await mcp_tools.get_task_result(task_id=task_id)
    assert "COMPLETED" in task_status


# TC-MCP-04: 온습도 센서 값 측정(read) 검증
async def test_tc04_read_sensor_data(inject_fresh_fake_service):
    res = await mcp_tools.control_device(device_id="sensor_env", action="read")
    task_id = extract_task_id(res)

    await asyncio.sleep(1.3)

    sensor_state = inject_fresh_fake_service.virtual_devices["sensor_env"]
    assert sensor_state["temperature"] == 24.0

    task_status = await mcp_tools.get_task_result(task_id=task_id)
    assert "COMPLETED" in task_status


# TC-MCP-05: 지연 스케줄링(예약 실행) 및 상태 전이 검증
async def test_tc05_schedule_device_later(inject_fresh_fake_service):
    # 먼저 전등을 켜둔 상태로 설정
    inject_fresh_fake_service.virtual_devices["light_living"]["power"] = "ON"

    # 2초 뒤에 거실 전등을 끄도록 예약
    res = await mcp_tools.schedule_device(device_id="light_living", action="turn_off", delay_seconds=2)
    task_id = extract_task_id(res)

    # 1단계 (0.5초 시점): 아직 예약 대기 중이어야 하며 전등은 여전히 ON 상태여야 함
    await asyncio.sleep(0.5)
    status_early = await mcp_tools.get_task_result(task_id=task_id)
    assert "SCHEDULED" in status_early
    assert inject_fresh_fake_service.virtual_devices["light_living"]["power"] == "ON"

    # 2단계 (3.5초 시점): 지연 2초 + 실행 1초 경과 후 완료 및 전등 OFF 확인
    await asyncio.sleep(3.0)
    status_done = await mcp_tools.get_task_result(task_id=task_id)
    assert "COMPLETED" in status_done
    assert inject_fresh_fake_service.virtual_devices["light_living"]["power"] == "OFF"


# TC-MCP-06: 존재하지 않는 작업 ID 조회 예외 처리 검증
async def test_tc06_invalid_task_id():
    status = await mcp_tools.get_task_result(task_id="00000000")
    assert "NOT_FOUND" in status
    assert "존재하지 않는 작업 ID입니다." in status

