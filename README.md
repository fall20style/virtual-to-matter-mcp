# virtual-to-matter-mcp

AI 에이전트(Discord, Meta Muse, Claude 등)가 **MCP(Model Context Protocol v2)**를 통해 음성 또는 텍스트로 스마트홈 기기(전등, TV, 센서)를 제어하고 스케줄링할 수 있도록 설계된 **비동기 홈 컨트롤러 서버**입니다.

포트와 어댑터(Hexagonal) 아키텍처를 적용하여, **가상 시뮬레이션(`FakeHomeService` / Virtual 모드)** 환경에서 완벽하게 테스트한 뒤 코드 수정 없이 **실제 하드웨어 프로토콜(`Matter` / `IoTivity`)** 구현체로 즉시 전환할 수 있습니다.

---

## 주요 기능

- **MCP v2 (`MCPServer`) 표준 인터페이스 제공**: LLM 에이전트가 즉시 호출할 수 있는 4종의 표준 도구(`get_home_devices`, `control_device`, `schedule_device`, `get_task_result`)를 `/mcp` 경로로 제공합니다.
- **이벤트 드리븐 비동기 워커 풀 (`services/worker_pool.py`)**: 폴링(Polling) 없이 `asyncio.Queue`에서 대기하는 3개의 백그라운드 워커가 동시 요청을 안전하게 분산 처리합니다.
- **프로토콜 라우팅 (`RealHomeService`)**: 기기별로 지정된 프로토콜(`Matter` 또는 `IoTivity`)에 따라 제어 명령을 자동 분기하며, `RUN_MODE` 환경 변수(`virtual` / `actual`)로 실행 모드를 전환합니다.
- **의존성 주입(DI) 기반 자동화 테스트 (`tests/`)**: `FakeHomeService` 단위 검증(6개)과 `RealHomeService` 워커 풀·프로토콜 검증(3개) 등 총 9개의 통합 테스트 스위트를 지원합니다.

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

### 3. 통합 서버 실행 (`main.py`)
```powershell
# Virtual(시뮬레이션) 모드로 실행 (기본값)
python main.py

# Actual(실제 Matter/IoTivity 제어) 모드로 실행
$env:RUN_MODE="actual"; python main.py
```
서버가 시작되면 `http://127.0.0`에서 상태를 확인할 수 있으며, AI 에이전트는 `http://127.0.0`로 MCP 연결을 맺을 수 있습니다.

### 4. 자동화 테스트 실행 (`pytest`)
```powershell
pytest -v
```

---

## 제공되는 MCP Tools (`interfaces/mcp_tools.py`)

| Tool 이름 | 설명 | 주요 파라미터 |
| :--- | :--- | :--- |
| **`get_home_devices`** | 등록된 모든 기기(전등, TV, 센서)의 목록과 현재 상태 조회 | 없음 |
| **`control_device`** | 지정된 기기에 즉시 제어 및 측정 명령 실행 | `device_id`, `action`, `value` |
| **`schedule_device`** | 지정된 초(`delay_seconds`) 이후에 기기가 동작하도록 예약 | `device_id`, `action`, `delay_seconds`, `value` |
| **`get_task_result`** | 백그라운드 작업의 진행 상태 및 최종 결과 조회 | `task_id` |

---

## 프로젝트 패키지 구조

```text
virtual-to-matter-mcp/
├── .venv/                       # Python 3.12 가상환경 (Git 제외)
├── .gitignore                   # Git 추적 제외 설정
├── pytest.ini                   # pytest 비동기 설정 및 pythonpath 지정
├── main.py                      # [Entrypoint] FastAPI + MCPServer 통합 실행 진입점
│
├── core/                        # [1. 핵심 도메인 & 추상 포트]
│   ├── __init__.py
│   └── ports.py                 # HomeControllerPort 추상 인터페이스 (ABC)
│
├── services/                    # [2. 비즈니스 로직 & 어댑터 구현체]
│   ├── __init__.py
│   ├── worker_pool.py           # 이벤트 기반 비동기 큐(asyncio.Queue) & 워커 풀 엔진
│   ├── fake_service.py          # 단위 테스트용 가짜 시뮬레이션 구현체
│   ├── real_service.py          # 워커 풀 + Matter/IoTivity 프로토콜 라우터 구현체
│   └── protocols/               # 실제 하드웨어 프로토콜별 어댑터 확장 영역
│       └── __init__.py
│
├── interfaces/                  # [3. 외부 통신 접점 (Driving Adapters)]
│   ├── __init__.py
│   └── mcp_tools.py             # MCP v2(MCPServer) 기반 LLM 에이전트 연동 인터페이스
│
├── templates/                   # 웹 GUI 템플릿 확장 영역
├── tests/                       # [4. 자동화 테스트 스위트]
│   ├── __init__.py
│   ├── test_mcp_fake.py         # FakeHomeService 기반 MCP 단위 테스트 (6개)
│   └── test_real_worker.py      # RealHomeService + 워커 풀 동시성·프로토콜 테스트 (3개)
│
├── README.md                    # 프로젝트 개요 및 설치·실행 가이드
├── ARCHITECTURE.md              # 포트와 어댑터 아키텍처 및 Mermaid 다이어그램
└── TEST_CASE.md                 # 통합 테스트 케이스 명세서
```
