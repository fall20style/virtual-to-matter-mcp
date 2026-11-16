# Test Cases — virtual-to-matter-mcp

본 문서는 **`virtual-to-matter-mcp`**의 MCP Tool 인터페이스(`mcp_tools.py`)와 가상 홈 제어 서비스(`FakeHomeService`)의 정상 동작을 검증하기 위한 통합 테스트 케이스 명세서입니다.

---

## 1. 테스트 환경 및 사전 조건

- **실행 환경**: Python 3.12 / `mcp` v2 (`MCPServer`) / `pytest` / `pytest-asyncio`
- **테스트 격리 방식**: `pytest`의 `@pytest.fixture(autouse=True)`를 통해 매 테스트 함수 실행 직전 초기화된 새 `FakeHomeService` 인스턴스를 `mcp_tools.home_service`에 주입
- **실행 명령어**: `pytest test_mcp_home.py -v`

---

## 2. 테스트 케이스 목록

| TC ID | 테스트 항목 | 호출 MCP Tool | 입력 파라미터 | 기대 결과 (Expected Result) | 매핑 테스트 함수 (`test_mcp_home.py`) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-MCP-01** | 가상 기기 목록 및 초기 상태 조회 | `get_home_devices()` | 없음 | `[SIMULATION MODE]` 문구와 함께 `light_living`, `tv_main`, `sensor_env`의 초기 상태 반환 | `test_tc01_get_home_devices` |
| **TC-MCP-02** | 거실 전등 즉시 제어 및 밝기 조절 | `control_device()`<br>`get_task_result()` | `device_id="light_living"`<br>`action="set_brightness"`<br>`value=80` | 8자리 `task_id` 즉시 발급, 1초 후 작업 상태 `COMPLETED` 및 전등 상태 `power="ON"`, `brightness=80` 반영 | `test_tc02_control_light_immediately` |
| **TC-MCP-03** | 스마트 TV 채널 변경 제어 | `control_device()`<br>`get_task_result()` | `device_id="tv_main"`<br>`action="set_channel"`<br>`value=7` | 1초 후 작업 상태 `COMPLETED` 및 TV 상태 `power="ON"`, `channel=7` 반영 | `test_tc03_control_tv_channel` |
| **TC-MCP-04** | 온습도 센서 값 측정 실행 | `control_device()`<br>`get_task_result()` | `device_id="sensor_env"`<br>`action="read"` | 1초 후 작업 상태 `COMPLETED` 및 센서 온도 값이 `24.0`으로 갱신됨 | `test_tc04_read_sensor_data` |
| **TC-MCP-05** | 지연 스케줄링(예약 실행) 및 상태 전이 | `schedule_device()`<br>`get_task_result()` | `device_id="light_living"`<br>`action="turn_off"`<br>`delay_seconds=2` | - 0.5초 시점: 상태 `SCHEDULED`, 전등 `ON` 유지<br>- 3.5초 시점: 상태 `COMPLETED`, 전등 `OFF` 전환 | `test_tc05_schedule_device_later` |
| **TC-MCP-06** | 존재하지 않는 작업 ID 조회 예외 처리 | `get_task_result()` | `task_id="00000000"` | 서버 오류 없이 `NOT_FOUND` 상태 및 `"존재하지 않는 작업 ID입니다."` 메시지 반환 | `test_tc06_invalid_task_id` |

---

## 3. 테스트 검증 포인트

1. **인터페이스-구현체 분리 검증**: `mcp_tools.py`가 `HomeControllerPort` 추상 규격만을 통해 `FakeHomeService`의 비동기 메서드를 정상 호출하는지 검증합니다.
2. **비동기 스케줄링 정합성**: `schedule_device` 호출 시 이벤트 루프를 블로킹하지 않고 즉시 `task_id`를 반환한 뒤, 지정된 지연 시간(`delay_seconds`) 경과 후에만 기기 상태가 변경되는지 시간대별로 확인합니다.
3. **상태 격리**: 각 테스트가 독립적인 `FakeHomeService` 객체를 사용하므로 이전 테스트의 전등/TV 상태가 다음 테스트에 영향을 주지 않습니다.
