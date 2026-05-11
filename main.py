import asyncio
import sys
from config import POLL_INTERVAL_BASE, BEHAVIOR_PROFILE, CDP_URL
from core.event_bus import EventBus, Event, EventType
from core.game_state import GameState
from core.browser import BrowserSession
from core.human import HumanBehavior
from core.detector import detect_op_dots
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

    modules = [ColonizeModule(event_bus, game_state, scheduler, human)]
    for module in modules:
        await module.setup()

    logger.info(f"Connecting to Chrome on {CDP_URL} ...")
    if not await browser.attach():
        logger.error(
            "Bot cannot start.\n"
            "  1. Run start_chrome.bat\n"
            "  2. Log into the game and go to the sector map\n"
            "  3. Run start.bat again"
        )
        sys.exit(1)

    asyncio.create_task(scheduler.run())
    logger.info(
        f"Bot running. Profile: {BEHAVIOR_PROFILE}. "
        f"Polling every ~{POLL_INTERVAL_BASE}s for gold OP dots."
    )

    try:
        while True:
            try:
                if browser.is_on_sector_map():
                    dots = await detect_op_dots(browser.page)

                    if dots:
                        ids = [d.sector_id for d in dots]
                        logger.info(f"Found {len(dots)} OP dot(s) in sectors: {ids}")
                        await event_bus.publish(Event(
                            type=EventType.DOT_FOUND,
                            payload={"dots": dots},
                            source="main_loop",
                        ))
                    else:
                        logger.debug("No OP dots found this poll")

                elif browser.is_on_war_page():
                    logger.debug("On war page — WarModule not yet active")

                else:
                    logger.debug(f"Waiting on: {browser.current_url()}")

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
