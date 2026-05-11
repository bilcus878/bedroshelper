from modules.base_module import BaseModule
from core.event_bus import EventType, Event
from modules.colonize.tasks import ColonizeTask
from core.task import TaskPriority
from infra.logger import logger


class ColonizeModule(BaseModule):
    async def setup(self) -> None:
        self.event_bus.subscribe(EventType.DOT_FOUND, self._on_dots_found)
        self.event_bus.subscribe(EventType.COLONIZATION_SUCCESS, self._on_success)
        self.event_bus.subscribe(EventType.COLONIZATION_FAILED, self._on_failed)
        logger.info("ColonizeModule ready")

    async def teardown(self) -> None:
        pass

    async def _on_dots_found(self, event: Event) -> None:
        dots = event.payload.get("dots", [])
        for dot in dots:
            task = ColonizeTask(dot=dot, priority=TaskPriority.NORMAL)
            await self.scheduler.enqueue(task)
            logger.info(f"ColonizeTask queued: OP in sector {dot.sector_id} ({dot.sector_title})")

    async def _on_success(self, event: Event) -> None:
        logger.success(f"Colonization succeeded: {event.payload}")

    async def _on_failed(self, event: Event) -> None:
        logger.warning(f"Colonization failed: {event.payload}")
