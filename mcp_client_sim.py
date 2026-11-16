import asyncio
import re
from mcp.client import Client

#MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"
MCP_SERVER_URL = "http://127.0.0.1:8100/mcp"


def extract_task_id(text: str) -> str:
    match = re.search(r"작업 ID:\s*([a-f0-9]{8})", text)
    return match.group(1) if match else ""


async def run_agent_simulation():
    print(f"=== 외부 MCP 에이전트 클라이언트 시작 (대상: {MCP_SERVER_URL}) ===\n")

    # MCP v2 표준 Client로 원격 HTTP 서버에 접속
    async with Client(MCP_SERVER_URL) as client:
        # 1. 서버가 제공하는 MCP Tool 목록 탐색 (Discovery)
        tools = await client.list_tools()
        print(f"[1단계] 서버에서 발견된 MCP Tools ({len(tools.tools)}개):")
        for t in tools.tools:
            first_line = t.description.strip().splitlines()[0] if t.description else ""
            print(f"  - {t.name}: {first_line}")
        print("-" * 60)
        
        # 2. 현재 집안 기기 초기 상태 조회
        print("\n[2단계] 초기 기기 상태 조회 (get_home_devices 호출)")
        res_devices = await client.call_tool("get_home_devices", {})
        print(f"  응답: {res_devices.content[0].text}")

        # 3. 거실 전등 즉시 켜기 및 밝기 85% 설정
        print("\n[3단계] 거실 전등 제어 요청 (control_device 호출)")
        res_light = await client.call_tool(
            "control_device",
            {"device_id": "light_living", "action": "set_brightness", "value": 85},
        )
        light_text = res_light.content[0].text
        print(f"  응답: {light_text}")
        light_task_id = extract_task_id(light_text)
        
        # 4. 2초 뒤에 스마트 TV 채널 7번으로 켜도록 예약
        print("\n[4단계] 스마트 TV 2초 뒤 예약 실행 (schedule_device 호출)")
        res_tv = await client.call_tool(
            "schedule_device",
            {"device_id": "tv_main", "action": "set_channel", "delay_seconds": 2, "value": 7},
        )
        tv_text = res_tv.content[0].text
        print(f"  응답: {tv_text}")
        tv_task_id = extract_task_id(tv_text)

        # 5. 백그라운드 워커 처리 완료 대기 후 결과 확인
        print("\n[5단계] 백그라운드 워커 처리 대기 (3.5초)...")
        await asyncio.sleep(3.5)

        res_light_done = await client.call_tool("get_task_result", {"task_id": light_task_id})
        print(f"  전등 작업 결과: {res_light_done.content[0].text}")

        res_tv_done = await client.call_tool("get_task_result", {"task_id": tv_task_id})
        print(f"  TV 예약 결과:   {res_tv_done.content[0].text}")

        # 6. 최종 기기 상태 재확인
        print("\n[6단계] 최종 변경된 기기 전체 상태 확인")
        res_final = await client.call_tool("get_home_devices", {})
        print(f"  응답: {res_final.content[0].text}")

    print("\n=== 시뮬레이션 종료 ===")


if __name__ == "__main__":
    asyncio.run(run_agent_simulation())
