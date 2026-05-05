import cv2
import numpy as np
from PIL import Image
import io
from dataclasses import dataclass
from config import DOT_MIN_RADIUS, DOT_MAX_RADIUS, DOT_COLOR_SATURATION_MIN


@dataclass
class RawDot:
    rel_x: float
    rel_y: float
    radius: float
    color_bgr: tuple


async def detect_dots(screenshot_bytes: bytes, map_region: tuple[int, int, int, int]) -> list[RawDot]:
    """
    map_region = (left, top, right, bottom) absolute pixels
    Returns dots with RELATIVE (0.0-1.0) coords within that region.

    Strategy:
    1. Crop to region only — ignore game sidebar/header
    2. SimpleBlobDetector (primary — good for round colored dots)
    3. HoughCircles (fallback)
    4. Filter by radius range
    5. Filter by color saturation — large real dots are vivid, fake/background dots are dull
    """
    img = Image.open(io.BytesIO(screenshot_bytes))
    arr = np.array(img)
    left, top, right, bottom = map_region
    crop = arr[top:bottom, left:right]
    bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    h, w = crop.shape[:2]

    dots = []

    # --- Method 1: SimpleBlobDetector ---
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = int(np.pi * DOT_MIN_RADIUS ** 2 * 0.5)
    params.maxArea = int(np.pi * DOT_MAX_RADIUS ** 2 * 1.5)
    params.filterByCircularity = True
    params.minCircularity = 0.6
    params.filterByConvexity = True
    params.minConvexity = 0.7
    params.filterByColor = False

    detector = cv2.SimpleBlobDetector_create(params)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    inv = cv2.bitwise_not(gray)   # blobs are bright on dark background
    keypoints = detector.detect(inv)

    for kp in keypoints:
        radius = kp.size / 2
        if DOT_MIN_RADIUS <= radius <= DOT_MAX_RADIUS:
            cx, cy = int(kp.pt[0]), int(kp.pt[1])
            if _is_colorful(bgr, cx, cy, int(radius)):
                dots.append(RawDot(
                    rel_x=cx / w,
                    rel_y=cy / h,
                    radius=radius,
                    color_bgr=tuple(bgr[cy, cx].tolist()),
                ))

    # --- Method 2: HoughCircles fallback ---
    if not dots:
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=DOT_MIN_RADIUS * 2,
            param1=50,
            param2=25,
            minRadius=DOT_MIN_RADIUS,
            maxRadius=DOT_MAX_RADIUS,
        )
        if circles is not None:
            for cx, cy, r in np.round(circles[0]).astype(int):
                if _is_colorful(bgr, cx, cy, r):
                    dots.append(RawDot(
                        rel_x=cx / w,
                        rel_y=cy / h,
                        radius=float(r),
                        color_bgr=tuple(bgr[cy, cx].tolist()),
                    ))

    return dots


def _is_colorful(bgr_img, cx: int, cy: int, radius: int) -> bool:
    """
    Real large dots are saturated (vivid color).
    Fake dots or UI noise tend to be gray/dark.
    Sample pixels in a small circle around the center and check HSV saturation.
    """
    h, w = bgr_img.shape[:2]
    sample_r = max(2, radius // 2)
    ys = np.clip([cy - sample_r, cy, cy + sample_r], 0, h - 1)
    xs = np.clip([cx - sample_r, cx, cx + sample_r], 0, w - 1)

    pixels = [bgr_img[y, x] for y in ys for x in xs]
    avg_bgr = np.mean(pixels, axis=0).reshape(1, 1, 3).astype(np.uint8)
    hsv = cv2.cvtColor(avg_bgr, cv2.COLOR_BGR2HSV)
    saturation = int(hsv[0, 0, 1])
    return saturation >= DOT_COLOR_SATURATION_MIN


def draw_debug_dots(
    screenshot_bytes: bytes,
    dots: list[RawDot],
    map_region: tuple[int, int, int, int],
) -> bytes:
    """Draw detected dots as annotated circles on screenshot for debugging"""
    img = Image.open(io.BytesIO(screenshot_bytes))
    arr = np.array(img)
    left, top, right, bottom = map_region
    w, h = right - left, bottom - top

    for dot in dots:
        cx = int(dot.rel_x * w) + left
        cy = int(dot.rel_y * h) + top
        r = int(dot.radius)
        cv2.circle(arr, (cx, cy), r, (0, 255, 0), 2)
        cv2.putText(
            arr,
            f"({dot.rel_x:.2f},{dot.rel_y:.2f})",
            (cx + r + 4, cy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 255, 0),
            1,
        )

    out = io.BytesIO()
    Image.fromarray(arr).save(out, format="PNG")
    return out.getvalue()
