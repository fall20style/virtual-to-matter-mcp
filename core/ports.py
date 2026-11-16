from abc import ABC, abstractmethod
from typing import Optional


class HomeControllerPort(ABC):
    """MCP Tool이 호출하는 스마트홈 제어 서비스의 표준 인터페이스"""

    @abstractmethod
    async def get_devices_summary(self) -> str:
        """등록된 모든 기기의 목록과 현재 상태 요약 문자열을 반환합니다."""
        pass

    @abstractmethod
    async def execute_now(self, device_id: str, action: str, value: Optional[int] = None) -> str:
        """기기를 즉시 제어하도록 백그라운드 큐에 등록하고 task_id를 반환합니다."""
        pass

    @abstractmethod
    async def schedule_later(
        self, device_id: str, action: str, delay_seconds: int, value: Optional[int] = None
    ) -> str:
        """지정된 초(delay_seconds) 후에 실행되도록 예약하고 task_id를 반환합니다."""
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> dict:
        """작업 ID에 해당하는 진행 상태 및 결과를 조회합니다."""
        pass
