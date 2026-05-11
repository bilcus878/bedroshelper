from core.task import BaseTask, TaskPriority, TaskResult
from core.detector import OPDot, find_gold_dot_on_detail
from core.human import HumanBehavior
from config import DEBUG_MODE
from infra.logger import logger
from infra.debug import save_debug_screenshot


class ColonizeTask(BaseTask):
    def __init__(self, dot: OPDot, priority: TaskPriority = TaskPriority.NORMAL):
        super().__init__(priority=priority)
        self.dot = dot

    async def execute(self, browser, game_state, navigator, human: HumanBehavior) -> TaskResult:
        page = browser.page

        try:
            await human.reaction_delay()

            # Step 1: Click the gold dot on sector map → navigates to sector detail
            logger.info(
                f"Clicking OP dot in sector {self.dot.sector_id} "
                f"at page ({self.dot.abs_x}, {self.dot.abs_y})"
            )
            await navigator.click_at(page, self.dot.abs_x, self.dot.abs_y)
            await human.between_actions()

            if not await navigator.wait_for_page_change(page):
                return TaskResult(success=False, message="Sector detail did not load")

            await human.between_actions()

            if DEBUG_MODE:
                logger.info(
                    f"[DEBUG] WOULD click dot in sector detail and colonize "
                    f"sector {self.dot.sector_id} — DEBUG_MODE=True"
                )
                await page.go_back()
                await navigator.wait_for_page_change(page)
                return TaskResult(
                    success=True,
                    message=f"[DEBUG] Dry-run sector {self.dot.sector_id}",
                )

            # Step 2: Find and click the gold dot on the detail page
            dot_pos = await find_gold_dot_on_detail(page)
            if not dot_pos:
                await page.go_back()
                await navigator.wait_for_page_change(page)
                return TaskResult(
                    success=False,
                    message=f"Gold dot not found on detail page for sector {self.dot.sector_id}",
                )

            logger.info(f"Clicking dot on detail page at {dot_pos}")
            await navigator.click_at(page, dot_pos[0], dot_pos[1])
            await human.between_actions()

            # Step 3: Click "kolonizovat"
            success = await navigator.click_colonize_button(page)
            if not success:
                await page.go_back()
                await navigator.wait_for_page_change(page)
                return TaskResult(
                    success=False,
                    message=f"Kolonizovat button not found for sector {self.dot.sector_id}",
                )

            await human.between_actions()

            # Step 4: Return to sector map
            await page.go_back()
            await navigator.wait_for_page_change(page)

            return TaskResult(
                success=True,
                message=f"Colonized OP in sector {self.dot.sector_id}",
            )

        except Exception as e:
            return TaskResult(success=False, message=str(e))

    async def on_failure(self, result: TaskResult) -> None:
        await save_debug_screenshot(f"colonize_fail_{self.task_id}")
