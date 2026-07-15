"""Tests for face_image — the dependency-free PNG snapshot of the face."""

from __future__ import annotations

import struct
import zlib

from kindalive.expression.face import FaceState
from kindalive.expression.face_image import (
    COLS,
    ROWS,
    dot_grid,
    render_face_png,
)


def _face(**overrides: float) -> FaceState:
    values = {
        "brow_inner_raise": 0.0,
        "brow_outer_raise": 0.0,
        "brow_lower": 0.0,
        "eyelid_upper_raise": 0.0,
        "eyelid_lower_tighten": 0.0,
        "cheek_raise": 0.0,
        "nose_wrinkle": 0.0,
        "lip_corner_pull": 0.0,
        "lip_corner_depress": 0.0,
        "jaw_open": 0.0,
        "lip_pucker": 0.0,
        "lip_press": 0.0,
    }
    values.update(overrides)
    return FaceState(**values)


def _decode_png_header(png: bytes) -> tuple[int, int]:
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert png[12:16] == b"IHDR"
    width, height = struct.unpack(">II", png[16:24])
    return width, height


# ---------------------------------------------------------------------------
# dot_grid
# ---------------------------------------------------------------------------


def test_grid_shape_and_range():
    grid = dot_grid(_face())
    assert len(grid) == ROWS
    assert all(len(row) == COLS for row in grid)
    assert all(0.0 <= v <= 1.0 for row in grid for v in row)


def test_neutral_face_lights_eyes_and_mouth():
    grid = dot_grid(_face())
    # Eyes sit in the upper half, mouth in the lower half.
    upper = sum(v for row in grid[:15] for v in row)
    lower = sum(v for row in grid[15:] for v in row)
    assert upper > 0, "expected lit eye dots"
    assert lower > 0, "expected lit mouth dots"


def test_smile_uses_happy_arc_eyes():
    """A strong smile flips the eyes from ellipses to arcs (^) — same
    threshold as the live renderer (smile > 0.34)."""
    neutral = dot_grid(_face())
    smiling = dot_grid(_face(lip_corner_pull=0.8))
    assert smiling != neutral


def test_jaw_open_grows_the_mouth():
    closed = dot_grid(_face())
    open_ = dot_grid(_face(jaw_open=0.9))
    mouth_rows = range(18, ROWS)
    closed_mouth = sum(v for y in mouth_rows for v in closed[y])
    open_mouth = sum(v for y in mouth_rows for v in open_[y])
    assert open_mouth > closed_mouth


def test_brow_bars_appear_when_furrowed():
    calm = dot_grid(_face())
    angry = dot_grid(_face(brow_lower=0.8))
    brow_rows = range(0, 8)
    calm_brow = sum(v for y in brow_rows for v in calm[y])
    angry_brow = sum(v for y in brow_rows for v in angry[y])
    assert angry_brow > calm_brow


# ---------------------------------------------------------------------------
# render_face_png
# ---------------------------------------------------------------------------


def test_png_is_valid_and_sized():
    png = render_face_png(_face(), scale=8)
    width, height = _decode_png_header(png)
    assert (width, height) == (COLS * 8, ROWS * 8)
    assert png.endswith(
        struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND"))
    )


def test_png_pixels_decode_and_show_the_mood_color():
    """The IDAT stream decompresses to the expected size and contains
    mood-colored pixels brighter than the background."""
    png = render_face_png(_face(lip_corner_pull=0.9), mood_color="#E6A23C",
                          mood_intensity=0.8, scale=6)
    width, height = _decode_png_header(png)
    idat_start = png.index(b"IDAT") + 4
    idat_len = struct.unpack(">I", png[idat_start - 8:idat_start - 4])[0]
    raw = zlib.decompress(png[idat_start:idat_start + idat_len])
    assert len(raw) == height * (1 + width * 3)
    # Some pixel should be strongly red-ish (amber dots on #05070d).
    reds = [raw[y * (1 + width * 3) + 1 + x * 3]
            for y in range(height) for x in range(0, width)]
    assert max(reds) > 150


def test_png_is_deterministic_and_expression_sensitive():
    a1 = render_face_png(_face(), scale=6)
    a2 = render_face_png(_face(), scale=6)
    b = render_face_png(_face(jaw_open=0.9), scale=6)
    assert a1 == a2
    assert a1 != b
