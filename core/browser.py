from playwright.async_api import async_playwright, Browser, Page
from infra.logger import logger


class BrowserSession:
    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None
        self.page: Page | None = None

    async def launch(self, headless: bool = False) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        self.page = await context.new_page()
        # Prevent webdriver detection
        await self.page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        logger.info("Browser launched")

    async def navigate(self, url: str) -> bool:
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    async def take_screenshot(self) -> bytes:
        return await self.page.screenshot()

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
