from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from config import CDP_URL, GAME_HOST
from infra.logger import logger


class BrowserSession:
    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self.page: Page | None = None

    async def attach(self, cdp_url: str = CDP_URL) -> bool:
        """
        Attach to an existing Chrome instance launched with:
            chrome.exe --remote-debugging-port=9222
        Finds whichever tab is on the game and uses that.
        """
        self._playwright = await async_playwright().start()
        try:
            self._browser = await self._playwright.chromium.connect_over_cdp(cdp_url)
        except Exception as e:
            logger.error(
                f"Cannot connect to Chrome on {cdp_url}. "
                f"Make sure Chrome is running with --remote-debugging-port=9222\n  {e}"
            )
            return False

        for context in self._browser.contexts:
            for page in context.pages:
                if GAME_HOST in page.url:
                    self.page = page
                    self._context = context
                    logger.info(f"Attached to game tab: {page.url}")
                    return True

        contexts = self._browser.contexts
        if contexts and contexts[0].pages:
            self.page = contexts[0].pages[0]
            self._context = contexts[0]
            logger.warning(
                f"No {GAME_HOST} tab found. Active tab: {self.page.url}\n"
                "Navigate to the game and restart the bot."
            )
            return False

        logger.error("No open tabs found in Chrome.")
        return False

    def current_url(self) -> str:
        return self.page.url if self.page else ""

    def is_on_sector_map(self) -> bool:
        """Main galaxy map — no id_sektor param."""
        url = self.current_url()
        return "mapa.php" in url and "id_sektor" not in url

    def is_on_sector_detail(self) -> bool:
        """Single-sector detail page after clicking a sector."""
        url = self.current_url()
        return "mapa.php" in url and "id_sektor" in url

    def is_on_war_page(self) -> bool:
        url = self.current_url()
        return "valka.php" in url or "utok.php" in url

    async def take_screenshot(self) -> bytes:
        return await self.page.screenshot()

    async def close(self) -> None:
        """Disconnect without closing the user's browser session."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    # --- Standalone mode for testing without a logged-in browser ---
    async def launch(self, headless: bool = False) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        self.page = await self._context.new_page()
        await self.page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        logger.info("Browser launched (standalone mode)")

    async def navigate(self, url: str) -> bool:
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
