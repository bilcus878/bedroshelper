"""
Run from the bedroshelper folder:
    python calibrate.py
"""
import asyncio
import os
import sys

# Make sure we run from the project root regardless of where python is called from
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

print(f"Working dir: {ROOT}")
print("Importing dependencies...")

try:
    import cv2
    print("  cv2 OK")
except Exception as e:
    print(f"  cv2 FAILED: {e}")
    input("Press Enter to exit")
    sys.exit(1)

try:
    import numpy as np
    from PIL import Image
    import io
    print("  numpy/PIL OK")
except Exception as e:
    print(f"  numpy/PIL FAILED: {e}")
    input("Press Enter to exit")
    sys.exit(1)

try:
    from config import CDP_URL, SCREENSHOT_DIR
    from modules.colonize.module import SECTOR_MAP_REGION, DETAIL_MAP_REGION
    from core.browser import BrowserSession
    print("  project imports OK")
except Exception as e:
    print(f"  project import FAILED: {e}")
    input("Press Enter to exit")
    sys.exit(1)

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
print(f"Screenshots folder: {os.path.abspath(SCREENSHOT_DIR)}")


async def main():
    print(f"\nConnecting to Chrome on {CDP_URL} ...")
    browser = BrowserSession()
    ok = await browser.attach(CDP_URL)
    if not ok:
        print("Could not attach. Make sure Chrome is open on the game page.")
        input("Press Enter to exit")
        return

    print(f"Attached to: {browser.current_url()}")
    print("Taking screenshot...")

    raw = await browser.take_screenshot()
    img = Image.open(io.BytesIO(raw))
    print(f"Screenshot size: {img.width} x {img.height} px")

    arr = np.array(img)
    out = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    # Green = sector map region
    l, t, r, b = SECTOR_MAP_REGION
    cv2.rectangle(out, (l, t), (r, b), (0, 200, 0), 3)
    cv2.putText(out, "SECTOR_MAP_REGION", (l + 4, t + 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 0), 2)

    # Blue = detail map region
    l2, t2, r2, b2 = DETAIL_MAP_REGION
    cv2.rectangle(out, (l2, t2), (r2, b2), (200, 100, 0), 3)
    cv2.putText(out, "DETAIL_MAP_REGION", (l2 + 4, t2 + 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200, 100, 0), 2)

    path = os.path.join(SCREENSHOT_DIR, "calibration.png")
    result = cv2.imwrite(path, out)
    if result:
        print(f"\nSaved: {path}")
    else:
        print(f"\nFAILED to write image to {path}")

    print(f"\nSECTOR_MAP_REGION = {SECTOR_MAP_REGION}  (green box)")
    print(f"DETAIL_MAP_REGION = {DETAIL_MAP_REGION}  (blue box)")
    print("\nOpen screenshots/calibration.png and send it to Claude.")

    await browser.close()


asyncio.run(main())
input("\nPress Enter to exit")
