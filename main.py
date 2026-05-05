import asyncio
import sys
from config import POLL_INTERVAL_BASE, BEHAVIOR_PROFILE, CDP_URL
from core.event_bus import EventBus, Event, EventType
from core.game_state import GameState
from core.browser import BrowserSession
from core.human import HumanBehavior
from core.detector import detect_dots
from core.navigator import Navigator
from core.scheduler import Scheduler
from modules.colonize.module import ColonizeModule, SECTOR_MAP_REGION
from infra.logger import logger


async def main():
    # --- Wire everything together ---
    event_bus = EventBus()
    game_state = GameState()
    human = HumanBehavior(profile=BEHAVIOR_PROFILE)
    browser = BrowserSession()
    navigator = Navigator(human)
    scheduler = Scheduler(event_bus, game_state, browser, navigator, human)

    # --- Register modules ---
    modules = [
        ColonizeModule(event_bus, game_state, scheduler, human),
        # WarModule(...) — add here when implemented
    ]
    for module in modules:
        await module.setup()

    # --- Attach to existing Chrome session ---
    logger.info(f"Connecting to Chrome on {CDP_URL} ...")
    attached = await browser.attach()
    if not attached:
        logger.error(
            "Bot cannot start.\n"
            "  1. Launch Chrome with:  chrome.exe --remote-debugging-port=9222\n"
            "  2. Log into stargate-game.cz manually\n"
            "  3. Navigate to the sector map (mapa.php)\n"
            "  4. Run the bot again"
        )
        sys.exit(1)

    # --- Start scheduler in background ---
    asyncio.create_task(scheduler.run())

    logger.info(f"Bot attached. Profile: {BEHAVIOR_PROFILE}. Watching page: {browser.current_url()}")

    # --- Main polling loop ---
    try:
        while True:
            try:
                url = browser.current_url()

                # --- Sector map: look for colonizable planets ---
                if browser.is_on_sector_map():
                    screenshot = await browser.take_screenshot()
                    dots = await detect_dots(screenshot, SECTOR_MAP_REGION)

                    if dots:
                        logger.info(f"Found {len(dots)} dot(s) on sector map")
                        await event_bus.publish(Event(
                            type=EventType.DOT_FOUND,
                            payload={"dots": dots},
                            source="main_loop",
                        ))
                    else:
                        await event_bus.publish(
                            Event(type=EventType.NO_DOTS_FOUND, source="main_loop")
                        )

                # --- War page: placeholder until WarModule is implemented ---
                elif browser.is_on_war_page():
                    logger.debug("On war page — WarModule not yet active")
                    await event_bus.publish(
                        Event(type=EventType.ATTACK_INCOMING, source="main_loop")
                    )

                else:
                    logger.debug(f"Unrecognised page, waiting: {url}")

                await human.poll_wait(POLL_INTERVAL_BASE)
                await human.maybe_take_break()

            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(10)

    except KeyboardInterrupt:
        logger.info("Shutting down...")

    finally:
        for module in modules:
            await module.teardown()
        # Disconnect without closing the browser — session stays alive
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
