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
        Attach to an existing Chrome instance that was launched with:
            chrome.exe --remote-debugging-port=9222

        Finds whichever tab is currently on the game and uses that.
        If multiple game tabs are open, picks the first one.
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

        # Search all contexts and tabs for a game page
        for context in self._browser.contexts:
            for page in context.pages:
                if GAME_HOST in page.url:
                    self.page = page
                    self._context = context
                    logger.info(f"Attached to game tab: {page.url}")
                    return True

        # No game tab found — warn and use whatever tab is active
        contexts = self._browser.contexts
        if contexts and contexts[0].pages:
            self.page = contexts[0].pages[0]
            self._context = contexts[0]
            logger.warning(
                f"No {GAME_HOST} tab found. Using active tab: {self.page.url}\n"
                f"Navigate to the game manually and restart the bot."
            )
            return False

        logger.error("No open tabs found in Chrome.")
        return False

    def current_url(self) -> str:
        if self.page:
            return self.page.url
        return ""

    def is_on_sector_map(self) -> bool:
        return "mapa.php" in self.current_url()

    def is_on_war_page(self) -> bool:
        # CALIBRATE: add the war page URL fragment when known
        return "valka.php" in self.current_url() or "utok.php" in self.current_url()

    async def take_screenshot(self) -> bytes:
        return await self.page.screenshot()

    async def close(self) -> None:
        """Disconnect from the browser without closing it — the user's session stays open."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    # --- Keep launch() for local testing / CI without a real browser ---
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
