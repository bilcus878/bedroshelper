from core.task import BaseTask, TaskPriority, TaskResult
from core.detector import RawDot, detect_dots
from core.mapper import Mapper
from core.human import HumanBehavior
from config import DEBUG_MODE
from infra.logger import logger
from infra.debug import save_debug_screenshot


class ColonizeTask(BaseTask):
    def __init__(
        self,
        dot: RawDot,
        sector_map_region: tuple,
        detail_map_region: tuple,
        priority: TaskPriority = TaskPriority.NORMAL,
    ):
        super().__init__(priority=priority)
        self.dot = dot
        self.sector_map_region = sector_map_region
        self.detail_map_region = detail_map_region

    async def execute(self, browser, game_state, navigator, human: HumanBehavior) -> TaskResult:
        page = browser.page

        try:
            # Human reaction delay before doing anything
            await human.reaction_delay()

            # Step 1: Click the sector on the main map
            px, py = Mapper.rel_to_pixel(
                self.dot.rel_x, self.dot.rel_y, self.sector_map_region
            )
            logger.info(f"Clicking sector at pixel ({px}, {py})")
            await navigator.click_at(page, px, py)

            # Human pause — as if reading the detail map
            await human.between_actions()

            if not await navigator.wait_for_page_change(page):
                return TaskResult(success=False, message="Detail map did not load")

            # Human pause — simulate time to visually scan the map
            await human.between_actions()

            # Step 2: Detect dots in detail map
            screenshot = await browser.take_screenshot()
            detail_dots = await detect_dots(screenshot, self.detail_map_region)

            if not detail_dots:
                return TaskResult(success=False, message="No dots found in detail map")

            # Step 3: Match position from sector map → detail map
            matched = Mapper.find_matching_dot(self.dot, detail_dots)
            if not matched:
                return TaskResult(
                    success=False, message="No position match found in detail map"
                )

            logger.info(
                f"Matched dot at relative ({matched.rel_x:.2f}, {matched.rel_y:.2f})"
            )

            # Step 4: Click the matched dot
            dx, dy = Mapper.rel_to_pixel(
                matched.rel_x, matched.rel_y, self.detail_map_region
            )
            await navigator.click_at(page, dx, dy)

            # Human pause — as if reading a popup or tooltip
            await human.between_actions()

            # Step 5: Click colonize button (dry-run when DEBUG_MODE is on)
            if DEBUG_MODE:
                logger.info(
                    f"[DEBUG] WOULD COLONIZE at ({self.dot.rel_x:.2f}, {self.dot.rel_y:.2f}) — "
                    f"skipping real click (DEBUG_MODE=True)"
                )
                await human.between_actions()
                return TaskResult(
                    success=True,
                    message=f"[DEBUG] Dry-run colonize at ({self.dot.rel_x:.2f}, {self.dot.rel_y:.2f})",
                )

            success = await navigator.click_colonize_button(page)
            if not success:
                return TaskResult(success=False, message="Colonize button not found")

            # Human pause after completing an action
            await human.between_actions()

            return TaskResult(
                success=True,
                message=f"Colonized at ({self.dot.rel_x:.2f}, {self.dot.rel_y:.2f})",
            )

        except Exception as e:
            return TaskResult(success=False, message=str(e))

    async def on_failure(self, result: TaskResult) -> None:
        screenshot = None
        try:
            screenshot = await self.browser.take_screenshot()  # type: ignore
        except Exception:
            pass
        await save_debug_screenshot(f"colonize_fail_{self.task_id}", screenshot)
