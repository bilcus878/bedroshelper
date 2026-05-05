"""
Unit tests for Mapper — no browser, no screenshot needed.

Run with:
    pytest tests/test_mapper.py -v
or directly:
    python tests/test_mapper.py
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.mapper import Mapper
from core.detector import RawDot


def make_dot(rel_x: float, rel_y: float, radius: float = 10.0) -> RawDot:
    return RawDot(rel_x=rel_x, rel_y=rel_y, radius=radius, color_bgr=(0, 0, 255))


class TestFindMatchingDot:
    def test_exact_match(self):
        sector_dot = make_dot(0.5, 0.5)
        detail_dots = [make_dot(0.5, 0.5)]
        result = Mapper.find_matching_dot(sector_dot, detail_dots)
        assert result is not None
        assert result.rel_x == pytest.approx(0.5)
        assert result.rel_y == pytest.approx(0.5)

    def test_close_match_within_tolerance(self):
        sector_dot = make_dot(0.3, 0.7)
        # 0.10 distance — within default tolerance of 0.15
        detail_dots = [make_dot(0.35, 0.73)]
        result = Mapper.find_matching_dot(sector_dot, detail_dots)
        assert result is not None

    def test_no_match_outside_tolerance(self):
        sector_dot = make_dot(0.1, 0.1)
        # 0.57 distance — well outside tolerance
        detail_dots = [make_dot(0.5, 0.5)]
        result = Mapper.find_matching_dot(sector_dot, detail_dots)
        assert result is None

    def test_picks_closest_when_multiple_candidates(self):
        sector_dot = make_dot(0.5, 0.5)
        close = make_dot(0.52, 0.52)
        far = make_dot(0.60, 0.60)
        result = Mapper.find_matching_dot(sector_dot, [far, close])
        assert result is close

    def test_empty_detail_dots(self):
        sector_dot = make_dot(0.5, 0.5)
        result = Mapper.find_matching_dot(sector_dot, [])
        assert result is None


class TestRelToPixel:
    def test_top_left_corner(self):
        region = (100, 50, 600, 450)
        px, py = Mapper.rel_to_pixel(0.0, 0.0, region)
        assert px == 100
        assert py == 50

    def test_bottom_right_corner(self):
        region = (100, 50, 600, 450)
        px, py = Mapper.rel_to_pixel(1.0, 1.0, region)
        assert px == 600
        assert py == 450

    def test_center(self):
        region = (0, 0, 1000, 800)
        px, py = Mapper.rel_to_pixel(0.5, 0.5, region)
        assert px == 500
        assert py == 400

    def test_arbitrary_position(self):
        region = (610, 10, 1270, 790)
        w, h = 1270 - 610, 790 - 10
        px, py = Mapper.rel_to_pixel(0.25, 0.75, region)
        assert px == 610 + int(0.25 * w)
        assert py == 10 + int(0.75 * h)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
