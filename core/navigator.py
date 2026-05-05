import asyncio
from playwright.async_api import Page
from core.human import HumanBehavior
from infra.logger import logger


class Navigator:
    def __init__(self, human: HumanBehavior):
        self.human = human

    async def click_at(self, page: Page, x: int, y: int) -> None:
        """Click with human-like mouse movement and jitter"""
        await self.human.move_and_click(page, x, y)
        await self.human.between_actions()

    async def click_colonize_button(self, page: Page) -> bool:
        """
        Try multiple strategies to find and click the colonize button.
        1. Czech text: "kolonizovat planetu"
        2. Partial match: "kolonizovat"
        3. Button/link variants
        Returns True if found and clicked.
        """
        selectors = [
            "text=kolonizovat planetu",
            "text=Kolonizovat planetu",
            "button:has-text('kolonizovat')",
            "a:has-text('kolonizovat')",
            "input[value*='kolonizovat' i]",
        ]
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=3000):
                    box = await el.bounding_box()
                    cx = int(box["x"] + box["width"] / 2)
                    cy = int(box["y"] + box["height"] / 2)
                    await self.click_at(page, cx, cy)
                    logger.debug(f"Colonize button found via selector: {sel}")
                    return True
            except Exception:
                continue
        return False

    async def wait_for_page_change(self, page: Page, timeout: int = 10000) -> bool:
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except Exception:
            return False

    async def take_screenshot(self, page: Page) -> bytes:
        return await page.screenshot()
