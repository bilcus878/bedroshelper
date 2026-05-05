import math
from core.detector import RawDot
from config import POSITION_MATCH_TOLERANCE


class Mapper:
    @staticmethod
    def find_matching_dot(sector_dot: RawDot, detail_dots: list[RawDot]) -> RawDot | None:
        """
        The sector map and detail map show the same spatial area.
        A dot at relative position (0.3, 0.7) on sector map
        should be near (0.3, 0.7) on the detail map.

        Find the detail dot closest to the expected position.
        Return None if no dot within POSITION_MATCH_TOLERANCE.
        """
        best = None
        best_dist = float("inf")

        for d in detail_dots:
            dist = math.sqrt(
                (d.rel_x - sector_dot.rel_x) ** 2 + (d.rel_y - sector_dot.rel_y) ** 2
            )
            if dist < best_dist:
                best_dist = dist
                best = d

        if best_dist <= POSITION_MATCH_TOLERANCE:
            return best
        return None

    @staticmethod
    def rel_to_pixel(
        rel_x: float, rel_y: float, region: tuple[int, int, int, int]
    ) -> tuple[int, int]:
        """Convert relative coords to absolute pixel coords within a region"""
        left, top, right, bottom = region
        w, h = right - left, bottom - top
        return int(left + rel_x * w), int(top + rel_y * h)
