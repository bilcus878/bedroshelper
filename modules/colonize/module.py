from modules.base_module import BaseModule
from core.event_bus import EventType, Event
from modules.colonize.tasks import ColonizeTask
from core.task import TaskPriority
from infra.logger import logger


class ColonizeModule(BaseModule):

    def __init__(self, event_bus, game_state, scheduler, human):
        super().__init__(event_bus, game_state, scheduler, human)
        # task_id → sector_id: tracks which sectors are already queued/running
        self._active: dict[str, int] = {}

    async def setup(self) -> None:
        self.event_bus.subscribe(EventType.DOT_FOUND,       self._on_dots_found)
        self.event_bus.subscribe(EventType.TASK_COMPLETED,  self._on_task_done)
        self.event_bus.subscribe(EventType.TASK_FAILED,     self._on_task_done)
        logger.info("ColonizeModule ready")

    async def teardown(self) -> None:
        pass

    async def _on_dots_found(self, event: Event) -> None:
        dots = event.payload.get("dots", [])
        active_sectors = set(self._active.values())

        for dot in dots:
            if dot.sector_id in active_sectors:
                logger.debug(f"Sector {dot.sector_id} already queued — skipping duplicate")
                continue

            task = ColonizeTask(dot=dot, priority=TaskPriority.NORMAL)
            self._active[task.task_id] = dot.sector_id
            await self.scheduler.enqueue(task)
            logger.info(f"ColonizeTask queued: OP sector {dot.sector_id} [{task.task_id}]")

    async def _on_task_done(self, event: Event) -> None:
        task_id = event.payload.get("task_id", "")
        sector_id = self._active.pop(task_id, None)
        if sector_id is not None:
            logger.debug(f"Sector {sector_id} released from active set [{task_id}]")

    async def _on_success(self, event: Event) -> None:
        logger.success(f"Colonization succeeded: {event.payload}")

    async def _on_failed(self, event: Event) -> None:
        logger.warning(f"Colonization failed: {event.payload}")
