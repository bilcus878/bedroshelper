from modules.base_module import BaseModule
from core.event_bus import EventType, Event
from modules.colonize.tasks import ColonizeTask
from core.task import TaskPriority
from infra.logger import logger

# CALIBRATE: measure these from a real screenshot of the game
SECTOR_MAP_REGION = (610, 10, 1270, 790)
DETAIL_MAP_REGION = (530, 130, 1040, 520)


class ColonizeModule(BaseModule):
    async def setup(self) -> None:
        self.event_bus.subscribe(EventType.DOT_FOUND, self._on_dot_found)
        self.event_bus.subscribe(EventType.COLONIZATION_SUCCESS, self._on_success)
        self.event_bus.subscribe(EventType.COLONIZATION_FAILED, self._on_failed)
        logger.info("ColonizeModule ready")

    async def teardown(self) -> None:
        pass

    async def _on_dot_found(self, event: Event) -> None:
        dots = event.payload.get("dots", [])
        for dot in dots:
            task = ColonizeTask(
                dot=dot,
                sector_map_region=SECTOR_MAP_REGION,
                detail_map_region=DETAIL_MAP_REGION,
                priority=TaskPriority.NORMAL,
            )
            await self.scheduler.enqueue(task)
            logger.info(
                f"ColonizeTask queued for dot at ({dot.rel_x:.2f}, {dot.rel_y:.2f})"
            )

    async def _on_success(self, event: Event) -> None:
        logger.success(f"Colonization succeeded: {event.payload}")

    async def _on_failed(self, event: Event) -> None:
        logger.warning(f"Colonization failed: {event.payload}")
