import asyncio
import sys
from config import POLL_INTERVAL_BASE, BEHAVIOR_PROFILE, CDP_URL
from core.event_bus import EventBus, Event, EventType
from core.game_state import GameState
from core.browser import BrowserSession
from core.human import HumanBehavior
from core.detector import detect_colonizable_sectors
from core.navigator import Navigator
from core.scheduler import Scheduler
from modules.colonize.module import ColonizeModule
from infra.logger import logger


async def main():
    event_bus = EventBus()
    game_state = GameState()
    human = HumanBehavior(profile=BEHAVIOR_PROFILE)
    browser = BrowserSession()
    navigator = Navigator(human)
    scheduler = Scheduler(event_bus, game_state, browser, navigator, human)

    modules = [
        ColonizeModule(event_bus, game_state, scheduler, human),
    ]
    for module in modules:
        await module.setup()

    logger.info(f"Connecting to Chrome on {CDP_URL} ...")
    if not await browser.attach():
        logger.error(
            "Bot cannot start.\n"
            "  1. Run start_chrome.bat to open Chrome with debug port\n"
            "  2. Log into stargate-game.cz\n"
            "  3. Navigate to the sector map (mapa.php)\n"
            "  4. Run start.bat again"
        )
        sys.exit(1)

    asyncio.create_task(scheduler.run())
    logger.info(f"Bot attached. Profile: {BEHAVIOR_PROFILE}. Watching: {browser.current_url()}")

    try:
        while True:
            try:
                url = browser.current_url()

                if browser.is_on_sector_map():
                    sectors = await detect_colonizable_sectors(browser.page)

                    if sectors:
                        logger.info(f"Found {len(sectors)} colonizable sector(s): "
                                    f"{[s.sector_id for s in sectors]}")
                        await event_bus.publish(Event(
                            type=EventType.DOT_FOUND,
                            payload={"dots": sectors},
                            source="main_loop",
                        ))
                    else:
                        logger.debug("No colonizable sectors found this poll")
                        await event_bus.publish(
                            Event(type=EventType.NO_DOTS_FOUND, source="main_loop")
                        )

                elif browser.is_on_war_page():
                    logger.debug("On war page — WarModule not yet active")

                else:
                    logger.debug(f"Waiting on: {url}")

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
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
