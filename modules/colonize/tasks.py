from core.task import BaseTask, TaskPriority, TaskResult
from core.detector import Sector
from core.human import HumanBehavior
from config import DEBUG_MODE
from infra.logger import logger
from infra.debug import save_debug_screenshot


class ColonizeTask(BaseTask):
    def __init__(self, sector: Sector, priority: TaskPriority = TaskPriority.NORMAL):
        super().__init__(priority=priority)
        self.sector = sector

    async def execute(self, browser, game_state, navigator, human: HumanBehavior) -> TaskResult:
        page = browser.page

        try:
            await human.reaction_delay()

            # Find the map image position on screen
            img_box = await page.locator('#galaxie').bounding_box()
            if not img_box:
                return TaskResult(success=False, message="Map image #galaxie not found on page")

            # Translate image-relative centroid → absolute page coords
            abs_x = int(img_box['x'] + self.sector.centroid[0])
            abs_y = int(img_box['y'] + self.sector.centroid[1])

            logger.info(f"Clicking sector {self.sector.sector_id} at page ({abs_x}, {abs_y})")
            await navigator.click_at(page, abs_x, abs_y)
            await human.between_actions()

            if not await navigator.wait_for_page_change(page):
                return TaskResult(success=False, message="Sector detail page did not load")

            # Human pause — simulate reading the sector detail
            await human.between_actions()

            if DEBUG_MODE:
                logger.info(
                    f"[DEBUG] WOULD COLONIZE sector {self.sector.sector_id} "
                    f"({self.sector.title}) — skipping real click (DEBUG_MODE=True)"
                )
                # Navigate back to sector map
                await page.go_back()
                await navigator.wait_for_page_change(page)
                return TaskResult(
                    success=True,
                    message=f"[DEBUG] Dry-run sector {self.sector.sector_id}",
                )

            success = await navigator.click_colonize_button(page)
            if not success:
                await page.go_back()
                await navigator.wait_for_page_change(page)
                return TaskResult(
                    success=False,
                    message=f"Colonize button not found for sector {self.sector.sector_id}",
                )

            await human.between_actions()

            # Navigate back to sector map for next poll
            await page.go_back()
            await navigator.wait_for_page_change(page)

            return TaskResult(
                success=True,
                message=f"Colonized sector {self.sector.sector_id}",
            )

        except Exception as e:
            return TaskResult(success=False, message=str(e))

    async def on_failure(self, result: TaskResult) -> None:
        await save_debug_screenshot(f"colonize_fail_{self.task_id}")
