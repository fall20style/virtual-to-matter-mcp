import asyncio
from datetime import datetime
from typing import Awaitable, Callable

task_queue: asyncio.Queue | None = None
task_db: dict = {}
task_events: dict[str, asyncio.Event] = {}
WORKER_POOL_SIZE = 3

CommandExecutor = Callable[[str, str, int | None], Awaitable[str]]


async def worker(worker_name: str, executor: CommandExecutor):
    print(f"[{datetime.now()}] [{worker_name}] 준비 완료 (스마트홈 이벤트 대기 중...)")
    while True:
        task_id, payload = await task_queue.get()
        try:
            task_db[task_id]["status"] = "RUNNING"
            task_db[task_id]["worker"] = worker_name
            device_id = payload["device_id"]
            action = payload["action"]
            value = payload.get("value")

            output = await executor(device_id, action, value)

            task_db[task_id]["status"] = "COMPLETED"
            task_db[task_id]["result"] = output
            if task_id in task_events:
                task_events[task_id].set()
        except Exception as e:
            task_db[task_id]["status"] = "FAILED"
            task_db[task_id]["result"] = f"오류 발생: {str(e)}"
            if task_id in task_events:
                task_events[task_id].set()
        finally:
            task_queue.task_done()


def start_worker_pool(executor: CommandExecutor, pool_size: int = WORKER_POOL_SIZE) -> list[asyncio.Task]:
    global task_queue
    task_queue = asyncio.Queue()
    task_db.clear()
    task_events.clear()
    return [
        asyncio.create_task(worker(f"Worker-{i + 1}", executor))
        for i in range(pool_size)
    ]


def stop_worker_pool(workers: list[asyncio.Task]):
    for w in workers:
        w.cancel()


async def enqueue_device_task(task_id: str, device_id: str, action: str, value: int | None = None):
    task_db[task_id] = {"status": "QUEUED", "worker": None, "result": None}
    task_events[task_id] = asyncio.Event()
    await task_queue.put((task_id, {"device_id": device_id, "action": action, "value": value}))


async def enqueue_device_task_after_delay(
    delay_seconds: int, task_id: str, device_id: str, action: str, value: int | None = None
):
    await asyncio.sleep(delay_seconds)
    task_db[task_id]["status"] = "QUEUED"
    await task_queue.put((task_id, {"device_id": device_id, "action": action, "value": value}))
