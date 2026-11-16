# virtual-to-matter-mcp

AI 에이전트(Discord, Meta Muse, Claude 등)가 **MCP(Model Context Protocol v2)**를 통해 음성 또는 텍스트로 스마트홈 기기(전등, TV, 센서)를 제어하고 스케줄링할 수 있도록 설계된 **비동기 홈 컨트롤러 서버**입니다.

포트와 어댑터(Hexagonal) 아키텍처를 적용하여, **가상 시뮬레이션(`FakeHomeService`)** 환경에서 완벽하게 테스트한 뒤 코드 수정 없이 **실제 하드웨어 프로토콜(`Matter` / `IoTivity`)** 구현체로 즉시 전환할 수 있습니다.

---

## 주요 기능

- **MCP v2 (`MCPServer`) 표준 인터페이스 제공**: LLM 에이전트가 즉시 호출할 수 있는 4종의 표준 도구(`get_home_devices`, `control_device`, `schedule_device`, `get_task_result`)를 제공합니다.
- **시뮬레이션과 실기기의 완벽한 분리 (`HomeControllerPort`)**: 추상 인터페이스를 통해 가상 전등·TV·센서 시뮬레이터와 실제 Matter/IoTivity 제어 모듈을 손쉽게 교체할 수 있습니다.
- **비동기 지연 스케줄링**: *"N분 뒤에 거실 불 꺼줘"*와 같은 예약 명령을 이벤트 루프 블로킹 없이 백그라운드에서 정확히 실행합니다.
- **의존성 주입(DI) 기반 자동화 테스트**: 실제 하드웨어 장비 없이도 `pytest`를 통해 모든 기기 제어 및 스케줄링 시나리오를 수 초 내에 자동 검증합니다.

---

## 설치 및 실행 방법

### 1. 가상환경 생성 및 활성화 (Windows PowerShell 기준)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. 필수 패키지 설치
```powershell
pip install mcp fastapi uvicorn pytest pytest-asyncio httpx
```

### 3. 자동화 테스트 실행 (`pytest`)
```powershell
pytest test_mcp_home.py -v
```

---

## 제공되는 MCP Tools (`mcp_tools.py`)

| Tool 이름 | 설명 | 주요 파라미터 |
| :--- | :--- | :--- |
| **`get_home_devices`** | 등록된 모든 기기(전등, TV, 센서)의 목록과 현재 상태 조회 | 없음 |
| **`control_device`** | 지정된 기기에 즉시 제어 및 측정 명령 실행 | `device_id`, `action`, `value` |
| **`schedule_device`** | 지정된 초(`delay_seconds`) 이후에 기기가 동작하도록 예약 | `device_id`, `action`, `delay_seconds`, `value` |
| **`get_task_result`** | 백그라운드 작업의 진행 상태 및 최종 결과 조회 | `task_id` |

---

## 프로젝트 구조

```text
virtual-to-matter-mcp/
├── .venv/                   # Python 3.12 가상환경
├── home_port.py             # 스마트홈 제어 서비스 추상 인터페이스 (Port)
├── fake_home_service.py     # 개발 및 테스트용 가상 기기 시뮬레이션 구현체 (Adapter)
├── mcp_tools.py             # MCP v2(MCPServer) 기반 LLM 에이전트 연동 인터페이스
├── test_mcp_home.py         # pytest 기반 MCP 기능 통합 자동화 테스트
├── pytest.ini               # pytest 비동기 이벤트 루프 설정
├── README.md                # 프로젝트 개요 및 설치·테스트 가이드
├── ARCHITECTURE.md          # 포트와 어댑터 아키텍처 및 Mermaid 다이어그램
└── TEST_CASE.md             # MCP Tool 통합 테스트 케이스 명세서
```
