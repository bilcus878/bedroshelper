import asyncio
import random
import math
from typing import Optional
from config import BEHAVIOR_PROFILES, BEHAVIOR_PROFILE


class HumanBehavior:
    """
    Simulates human-like timing, mouse movement, and behavioral patterns.
    All randomness is drawn from this class — nothing else uses random directly.

    Design principle: real humans are not random — they are VARIED but CONSISTENT
    within a session. A fast human stays fast. A cautious human stays cautious.
    We simulate this with per-session drift.
    """

    def __init__(self, profile: str = BEHAVIOR_PROFILE):
        self.profile = BEHAVIOR_PROFILES[profile]
        # Session drift: slightly shift all timings ±15% for this session
        self._session_drift = random.uniform(0.85, 1.15)
        self._action_count = 0

    def _p(self, key: str):
        """Get profile value"""
        return self.profile[key]

    async def reaction_delay(self) -> None:
        """
        Delay between seeing something and acting on it.
        Humans don't react instantly. Sometimes they hesitate.
        """
        lo, hi = self._p("reaction_delay")
        delay = random.uniform(lo, hi) * self._session_drift

        # Occasional extra hesitation (simulates distraction)
        if random.random() < self._p("occasional_pause_chance"):
            extra_lo, extra_hi = self._p("occasional_pause_duration")
            delay += random.uniform(extra_lo, extra_hi)

        await asyncio.sleep(delay)

    async def between_actions(self) -> None:
        """Short pause between sequential actions (e.g. between click and next click)"""
        lo, hi = self._p("between_actions")
        await asyncio.sleep(random.uniform(lo, hi) * self._session_drift)

    async def poll_wait(self, base_seconds: float) -> None:
        """
        Wait before next poll. Never perfectly constant.
        Adds drift so the bot doesn't poll at exactly :00, :30, :00, :30
        """
        lo, hi = self._p("poll_jitter")
        jitter = random.uniform(lo, hi)
        await asyncio.sleep(base_seconds * jitter * self._session_drift)

    def jitter_position(self, x: int, y: int) -> tuple[int, int]:
        """
        Add realistic randomness to a click position.
        Real humans don't click pixel-perfect.
        Uses Gaussian distribution — clustered near center, occasional outlier.
        """
        jitter_px = self._p("click_jitter_px")
        dx = int(random.gauss(0, jitter_px / 2))
        dy = int(random.gauss(0, jitter_px / 2))
        dx = max(-jitter_px, min(jitter_px, dx))
        dy = max(-jitter_px, min(jitter_px, dy))
        return x + dx, y + dy

    def mouse_path(self, x1: int, y1: int, x2: int, y2: int, steps: int = 20) -> list[tuple[int, int]]:
        """
        Generate a curved mouse path from (x1,y1) to (x2,y2).
        Real mouse movement is NOT a straight line — it curves slightly.
        Uses a quadratic bezier with a random control point offset.
        """
        mid_x = (x1 + x2) / 2 + random.uniform(-60, 60)
        mid_y = (y1 + y2) / 2 + random.uniform(-40, 40)

        path = []
        for i in range(steps + 1):
            t = i / steps
            bx = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * mid_x + t ** 2 * x2
            by = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * mid_y + t ** 2 * y2
            path.append((int(bx), int(by)))
        return path

    async def move_and_click(self, page, x: int, y: int) -> None:
        """
        Full human-like click:
        1. Move along curved bezier path
        2. Slight pause before clicking (human lines up the cursor)
        3. Click with randomized position
        4. Brief pause after click
        """
        jx, jy = self.jitter_position(x, y)

        lo_speed, hi_speed = self._p("mouse_speed")
        move_duration = random.uniform(lo_speed, hi_speed)

        path = self.mouse_path(340, 400, jx, jy)
        step_delay = move_duration / len(path)

        for px, py in path[:-1]:
            await page.mouse.move(px, py)
            await asyncio.sleep(step_delay)

        # Final hover pause — human aligns cursor before clicking
        await asyncio.sleep(random.uniform(0.05, 0.2))

        await page.mouse.click(jx, jy)

        await asyncio.sleep(random.uniform(0.1, 0.4))

        self._action_count += 1

    async def maybe_take_break(self) -> None:
        """
        After many actions, humans sometimes stop and do nothing.
        Call this after every ~50 actions.
        """
        if self._action_count > 0 and self._action_count % random.randint(40, 70) == 0:
            pause = random.uniform(30, 120)
            from infra.logger import logger
            logger.info(f"Taking human-like break for {pause:.0f}s")
            await asyncio.sleep(pause)
