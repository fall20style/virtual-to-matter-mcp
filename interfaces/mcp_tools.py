from typing import Literal, Optional
from pydantic import Field
from mcp.server.mcpserver import MCPServer

from core.ports import HomeControllerPort
from services.real_service import RealHomeService

mcp = MCPServer("SmartHomeController")
home_service: HomeControllerPort = RealHomeService(mode="virtual")

DeviceID = Literal["light_living", "tv_main", "sensor_env"]
DeviceAction = Literal["turn_on", "turn_off", "set_brightness", "set_channel", "read"]


@mcp.tool()
async def get_home_devices() -> str:
    """현재 집에 등록된 스마트 기기(전등, TV, 센서)의 목록과 현재 상태를 조회합니다."""
    return await home_service.get_devices_summary()


@mcp.tool()
async def control_device(
    device_id: DeviceID = Field(..., description="제어할 대상 기기 ID ('light_living', 'tv_main', 'sensor_env')."),
    action: DeviceAction = Field(..., description="수행할 동작 ('turn_on', 'turn_off', 'set_brightness', 'set_channel', 'read')."),
    value: Optional[int] = Field(default=None, description="밝기(1~100) 또는 TV 채널 번호 등 필요한 숫자 값.")
) -> str:
    """스마트홈 기기(전등, TV, 센서)에 즉시 제어 명령을 내립니다."""
    task_id = await home_service.execute_now(device_id, action, value)
    return f"[{device_id}] 기기에 '{action}' 명령을 즉시 실행하도록 등록했습니다. (작업 ID: {task_id})"


@mcp.tool()
async def schedule_device(
    device_id: DeviceID = Field(..., description="예약 제어할 대상 기기 ID ('light_living', 'tv_main', 'sensor_env')."),
    action: DeviceAction = Field(..., description="예약 시간에 수행할 동작 ('turn_on', 'turn_off', 'set_brightness', 'set_channel', 'read')."),
    delay_seconds: int = Field(..., ge=1, le=86400, description="현재 시각으로부터 몇 초 뒤에 실행할지 지정합니다."),
    value: Optional[int] = Field(default=None, description="밝기(1~100) 또는 TV 채널 번호 등 필요한 경우에만 입력하세요.")
) -> str:
    """지정된 시간(초) 이후에 스마트홈 기기가 자동으로 동작하도록 예약합니다."""
    task_id = await home_service.schedule_later(device_id, action, delay_seconds, value)
    return f"[{device_id}] 기기의 '{action}' 동작이 {delay_seconds}초 뒤에 실행되도록 예약되었습니다. (작업 ID: {task_id})"


@mcp.tool()
async def get_task_result(
    task_id: str = Field(..., description="발급받은 8자리 작업 ID")
) -> str:
    """작업의 진행 상태(QUEUED, RUNNING, COMPLETED)와 최종 결과를 조회합니다."""
    info = await home_service.get_task_status(task_id)
    return f"작업({task_id}) 상태: {info['status']}, 담당 워커: {info.get('worker')}, 결과: {info.get('result')}"
