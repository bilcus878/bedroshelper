import os
import time
from config import SCREENSHOT_DIR, DEBUG_MODE

os.makedirs(SCREENSHOT_DIR, exist_ok=True)


async def save_debug_screenshot(label: str, screenshot_bytes: bytes = None) -> str | None:
    if not DEBUG_MODE:
        return None
    fname = f"{SCREENSHOT_DIR}/{label}_{int(time.time())}.png"
    if screenshot_bytes:
        with open(fname, "wb") as f:
            f.write(screenshot_bytes)
    return fname
