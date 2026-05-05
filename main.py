import asyncio
from config import SECTOR_MAP_URL, POLL_INTERVAL_BASE, BEHAVIOR_PROFILE
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
        # WarModule(...) — uncomment when WarModule is implemented
    ]
    for module in modules:
        await module.setup()

    # --- Launch browser ---
    await browser.launch(headless=False)
    await browser.navigate(SECTOR_MAP_URL)

    # --- Start scheduler in background ---
    asyncio.create_task(scheduler.run())

    logger.info(f"Bot started. Profile: {BEHAVIOR_PROFILE}")

    # --- Main polling loop ---
    try:
        while True:
            try:
                screenshot = await browser.take_screenshot()
                dots = await detect_dots(screenshot, SECTOR_MAP_REGION)

                if dots:
                    logger.info(f"Found {len(dots)} dot(s)")
                    await event_bus.publish(Event(
                        type=EventType.DOT_FOUND,
                        payload={"dots": dots},
                        source="main_loop",
                    ))
                else:
                    await event_bus.publish(
                        Event(type=EventType.NO_DOTS_FOUND, source="main_loop")
                    )

                # Human-like poll interval — never perfectly constant
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
