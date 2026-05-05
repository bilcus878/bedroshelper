import asyncio
import heapq
from core.task import BaseTask, TaskStatus, TaskResult
from core.event_bus import EventBus, Event, EventType
from core.human import HumanBehavior
from config import ACTION_TIMEOUT, CONSECUTIVE_ERROR_LIMIT, LONG_SLEEP_AFTER_ERRORS
from infra.logger import logger


class Scheduler:
    def __init__(self, event_bus: EventBus, game_state, browser, navigator, human: HumanBehavior):
        self._queue: list[BaseTask] = []
        self._event_bus = event_bus
        self._game_state = game_state
        self._browser = browser
        self._navigator = navigator
        self._human = human
        self._consecutive_errors = 0
        self._running = False

    async def enqueue(self, task: BaseTask) -> None:
        heapq.heappush(self._queue, task)
        logger.debug(f"Task enqueued: {task.__class__.__name__} [{task.task_id}] priority={task.priority}")

    async def run(self) -> None:
        self._running = True
        logger.info("Scheduler started")
        while self._running:
            if not self._queue:
                await asyncio.sleep(5)
                continue

            if self._consecutive_errors >= CONSECUTIVE_ERROR_LIMIT:
                logger.error(
                    f"Too many errors ({self._consecutive_errors}), "
                    f"sleeping {LONG_SLEEP_AFTER_ERRORS}s"
                )
                await asyncio.sleep(LONG_SLEEP_AFTER_ERRORS)
                self._consecutive_errors = 0

            task = heapq.heappop(self._queue)
            await self._execute(task)

    async def _execute(self, task: BaseTask) -> None:
        task.status = TaskStatus.RUNNING
        logger.info(f"Executing {task.__class__.__name__} [{task.task_id}]")
        await self._event_bus.publish(Event(EventType.TASK_STARTED, {"task_id": task.task_id}))

        try:
            result = await asyncio.wait_for(
                task.execute(self._browser, self._game_state, self._navigator, self._human),
                timeout=ACTION_TIMEOUT,
            )
        except asyncio.TimeoutError:
            result = TaskResult(success=False, message="Task timed out")
        except Exception as e:
            result = TaskResult(success=False, message=str(e))

        if result.success:
            task.status = TaskStatus.COMPLETED
            self._consecutive_errors = 0
            await self._event_bus.publish(
                Event(EventType.TASK_COMPLETED, {"task_id": task.task_id, **result.data})
            )
        else:
            await self._handle_failure(task, result)

    async def _handle_failure(self, task: BaseTask, result: TaskResult) -> None:
        task.retry_count += 1
        self._consecutive_errors += 1
        logger.warning(
            f"Task failed [{task.task_id}]: {result.message} "
            f"(retry {task.retry_count}/{task.max_retries})"
        )
        await task.on_failure(result)

        if task.can_retry():
            task.status = TaskStatus.PENDING
            heapq.heappush(self._queue, task)
        else:
            task.status = TaskStatus.FAILED
            await self._event_bus.publish(
                Event(EventType.TASK_FAILED, {"task_id": task.task_id, "reason": result.message})
            )
