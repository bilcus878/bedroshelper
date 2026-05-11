import re
import io
import numpy as np
import cv2
from PIL import Image
from dataclasses import dataclass


@dataclass
class OPDot:
    """An Abandoned Planet (OP) dot found on the sector map."""
    sector_id: int
    sector_href: str      # "?page=0&id_sektor=28"
    sector_title: str     # "Sektor 28"
    dot_x: int            # pixel position relative to map image
    dot_y: int
    abs_x: int            # absolute page pixel position (for clicking)
    abs_y: int


def _find_gold_dots(bgr_img: np.ndarray) -> list[tuple[int, int, int]]:
    """
    Detect gold/yellow OP dots via HSV color thresholding.
    Returns list of (center_x, center_y, radius).
    """
    hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)

    # Gold/yellow range in OpenCV HSV (H: 0-179, S/V: 0-255)
    lower = np.array([15, 100, 150])
    upper = np.array([40, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)

    # Small morphological cleanup
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    dots = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 4 or area > 800:
            continue
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        circularity = 4 * np.pi * area / (perimeter ** 2)
        if circularity < 0.3:
            continue
        (cx, cy), radius = cv2.minEnclosingCircle(cnt)
        dots.append((int(cx), int(cy), max(1, int(radius))))

    return dots


def _point_in_polygon(x: int, y: int, coords: list[int]) -> bool:
    """Ray casting point-in-polygon test."""
    points = [(coords[i], coords[i + 1]) for i in range(0, len(coords) - 1, 2)]
    n = len(points)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = points[i]
        xj, yj = points[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def _load_sector_polygons(areas_raw: list[dict]) -> list[dict]:
    """Parse area dicts into sector polygon dicts (numbered sectors only)."""
    sectors = []
    for area in areas_raw:
        m = re.match(r'^Sektor\s+(\d+)$', area['alt'].strip())
        if not m:
            continue
        raw = [int(x.strip()) for x in area['coords'].split(',')
               if x.strip().lstrip('-').isdigit()]
        if len(raw) < 4:
            continue
        sectors.append({
            'id': int(m.group(1)),
            'href': area['href'],
            'title': area['alt'].strip(),
            'coords': raw,
        })
    return sectors


async def detect_op_dots(page) -> list[OPDot]:
    """
    Main detection on the sector map page:
    1. Screenshot the #galaxie image element
    2. HSV-threshold for gold dots
    3. For each dot, ray-cast into sector polygons from the <area> map
    Returns OPDot list — each has the sector to navigate to + click coords.
    """
    img_box = await page.locator('#galaxie').bounding_box()
    if not img_box:
        return []

    left = int(img_box['x'])
    top  = int(img_box['y'])
    w    = int(img_box['width'])
    h    = int(img_box['height'])

    raw_screenshot = await page.screenshot()
    arr = np.array(Image.open(io.BytesIO(raw_screenshot)))
    cropped = arr[top:top + h, left:left + w]
    bgr = cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR)

    raw_dots = _find_gold_dots(bgr)
    if not raw_dots:
        return []

    areas_raw = await page.evaluate("""() => {
        const map = document.querySelector('map[name="mapa_vesmiru"]');
        if (!map) return [];
        return Array.from(map.querySelectorAll('area')).map(a => ({
            href:   a.getAttribute('href')   || '',
            alt:    a.getAttribute('alt')    || '',
            coords: a.getAttribute('coords') || '',
        }));
    }""")

    # Scale factor: area coords are in image's natural pixel space
    # If the displayed image is scaled, we need to adjust
    natural = await page.evaluate("""() => {
        const img = document.getElementById('galaxie');
        return img ? { w: img.naturalWidth, h: img.naturalHeight } : { w: 0, h: 0 };
    }""")
    scale_x = natural['w'] / w if natural['w'] and w else 1.0
    scale_y = natural['h'] / h if natural['h'] and h else 1.0

    sectors = _load_sector_polygons(areas_raw)

    results = []
    for dot_x, dot_y, _radius in raw_dots:
        # Scale dot coords to natural image space for polygon test
        nat_x = int(dot_x * scale_x)
        nat_y = int(dot_y * scale_y)

        for sec in sectors:
            if _point_in_polygon(nat_x, nat_y, sec['coords']):
                results.append(OPDot(
                    sector_id=sec['id'],
                    sector_href=sec['href'],
                    sector_title=sec['title'],
                    dot_x=dot_x,
                    dot_y=dot_y,
                    abs_x=left + dot_x,
                    abs_y=top  + dot_y,
                ))
                break

    return results


async def find_gold_dot_on_detail(page) -> tuple[int, int] | None:
    """
    On the sector detail page, find the gold dot and return its absolute page coords.
    Used after clicking a sector to find the dot to click before colonizing.
    """
    img_box = await page.locator('#galaxie').bounding_box()
    if not img_box:
        return None

    left = int(img_box['x'])
    top  = int(img_box['y'])
    w    = int(img_box['width'])
    h    = int(img_box['height'])

    raw_screenshot = await page.screenshot()
    arr = np.array(Image.open(io.BytesIO(raw_screenshot)))
    cropped = arr[top:top + h, left:left + w]
    bgr = cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR)

    dots = _find_gold_dots(bgr)
    if not dots:
        return None

    # Take the brightest / largest dot
    dots.sort(key=lambda d: d[2], reverse=True)
    cx, cy, _ = dots[0]
    return left + cx, top + cy


def draw_debug_dots(screenshot_bytes: bytes, dots: list[OPDot]) -> bytes:
    """Annotate a screenshot with detected OP dots for debugging."""
    arr = np.array(Image.open(io.BytesIO(screenshot_bytes)))
    out = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    for dot in dots:
        cv2.circle(out, (dot.abs_x, dot.abs_y), 12, (0, 255, 0), 2)
        cv2.putText(out, f"S{dot.sector_id}", (dot.abs_x + 14, dot.abs_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    buf = io.BytesIO()
    Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB)).save(buf, format="PNG")
    return buf.getvalue()
