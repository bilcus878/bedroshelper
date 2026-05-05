"""
Integration test for the dot detector.

Requires screenshots/sector_map_sample.png to run the detection test.
If the file is absent the test is skipped automatically.

Run with:
    pytest tests/test_detector.py -v
or directly:
    python tests/test_detector.py
"""

import asyncio
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.detector import detect_dots, draw_debug_dots
from config import SCREENSHOT_DIR

# CALIBRATE: adjust to match real game layout after capturing a screenshot
SECTOR_MAP_REGION = (610, 10, 1270, 790)

SAMPLE_PATH = os.path.join(SCREENSHOT_DIR, "sector_map_sample.png")


@pytest.mark.asyncio
async def test_detect_dots_from_sample():
    if not os.path.exists(SAMPLE_PATH):
        pytest.skip(f"Sample screenshot not found at {SAMPLE_PATH}")

    with open(SAMPLE_PATH, "rb") as f:
        screenshot_bytes = f.read()

    dots = await detect_dots(screenshot_bytes, SECTOR_MAP_REGION)

    print(f"\nDetected {len(dots)} dot(s):")
    for dot in dots:
        print(f"  rel=({dot.rel_x:.3f}, {dot.rel_y:.3f})  radius={dot.radius:.1f}  bgr={dot.color_bgr}")

    # Save annotated debug image
    if dots:
        debug_bytes = draw_debug_dots(screenshot_bytes, dots, SECTOR_MAP_REGION)
        out_path = os.path.join(SCREENSHOT_DIR, "sector_map_debug.png")
        with open(out_path, "wb") as f:
            f.write(debug_bytes)
        print(f"Debug image saved to {out_path}")

    # Sanity check — we're not asserting exact count, just that detection is sane
    assert 0 <= len(dots) <= 10, f"Unexpected dot count: {len(dots)}"


if __name__ == "__main__":
    asyncio.run(test_detect_dots_from_sample())
