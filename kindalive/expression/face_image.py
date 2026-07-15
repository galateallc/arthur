"""face_image — render a FaceState snapshot as a PNG, dependency-free.

A static freeze-frame of the live LED face: the same 36×30 dot grid and
eye/brow/mouth geometry as ``web_assets/face3d.js`` (minus the
autonomous life — no blink, no saccade, no breathing glow), rasterized
in pure Python and encoded with stdlib ``zlib``. This lets the web UI
serve ``GET /face.png`` so chat integrations that can only show images
— a custom GPT action embedding the robot's current expression in its
reply, a Slack webhook, a README badge — get the real face computed
from the real chemical state.

Keep the shape constants in sync with ``drawMask`` in ``face3d.js``.
"""

from __future__ import annotations

import math
import struct
import zlib
from typing import Callable

from kindalive.expression.face import FaceState

# Dot grid — identical to face3d.js.
COLS = 36
ROWS = 30

_BACKGROUND = (5, 7, 13)  # #05070d, the dashboard's panel color

_Shape = Callable[[float, float], bool]


def _hex_rgb(color: str) -> tuple[int, int, int]:
    n = int(color.lstrip("#"), 16)
    return ((n >> 16) & 255, (n >> 8) & 255, n & 255)


# ── Shape predicates (grid space, y down — mirrors canvas) ─────────


def _ellipse(
    cx: float, cy: float, rx: float, ry: float, rot: float = 0.0,
) -> _Shape:
    cos_r, sin_r = math.cos(-rot), math.sin(-rot)

    def inside(x: float, y: float) -> bool:
        px, py = x - cx, y - cy
        lx = px * cos_r - py * sin_r
        ly = px * sin_r + py * cos_r
        return (lx / rx) ** 2 + (ly / ry) ** 2 <= 1.0

    return inside


def _segment(
    x1: float, y1: float, x2: float, y2: float, width: float,
) -> _Shape:
    half_sq = (width / 2) ** 2
    dx, dy = x2 - x1, y2 - y1
    len_sq = dx * dx + dy * dy

    def inside(x: float, y: float) -> bool:
        t = 0.0
        if len_sq > 0:
            t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / len_sq))
        qx, qy = x1 + t * dx, y1 + t * dy
        return (x - qx) ** 2 + (y - qy) ** 2 <= half_sq

    return inside


def _arc_stroke(
    cx: float, cy: float, r: float, a0: float, a1: float, width: float,
) -> _Shape:
    """Stroked circular arc (angles in radians, canvas convention)."""
    half = width / 2

    def inside(x: float, y: float) -> bool:
        px, py = x - cx, y - cy
        ang = math.atan2(py, px) % (2 * math.pi)
        if a0 <= ang <= a1:
            return abs(math.hypot(px, py) - r) <= half
        for a in (a0, a1):  # round caps
            ex, ey = cx + r * math.cos(a), cy + r * math.sin(a)
            if (x - ex) ** 2 + (y - ey) ** 2 <= half * half:
                return True
        return False

    return inside


def _quad_stroke(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    width: float,
    samples: int = 24,
) -> _Shape:
    """Stroked quadratic Bézier, approximated as a polyline."""
    pts = []
    for i in range(samples + 1):
        t = i / samples
        u = 1 - t
        pts.append((
            u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1],
        ))
    segs = [
        _segment(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], width)
        for i in range(samples)
    ]

    def inside(x: float, y: float) -> bool:
        return any(s(x, y) for s in segs)

    return inside


# ── FaceState → shapes → dot coverage grid ─────────────────────────


def _shapes(face: FaceState) -> list[_Shape]:
    """The eye/brow/mouth shapes for one expression — a static-snapshot
    port of ``drawMask`` in face3d.js (blink=0, saccade=0)."""
    m = face
    shapes: list[_Shape] = []
    cx = COLS / 2
    smile = m.lip_corner_pull - m.lip_corner_depress  # [-1, 1]
    eye_y, dx = 10.5, 7.6

    open_k = max(0.10, min(
        1.2,
        0.52 + 0.55 * m.eyelid_upper_raise - 0.55 * m.eyelid_lower_tighten,
    ))
    show_brow = (
        m.brow_lower > 0.18
        or m.brow_inner_raise > 0.28
        or m.brow_outer_raise > 0.4
    )

    for sx in (-1.0, 1.0):
        ex = cx + sx * dx
        if smile > 0.34:
            # Happy: upward arc (^)
            shapes.append(_arc_stroke(
                ex, eye_y + 1.8, 4.0,
                math.pi * 1.18, math.pi * 1.82, 2.2,
            ))
        else:
            hh = max(0.7, 1.0 + 3.6 * open_k)
            shapes.append(_ellipse(
                ex, eye_y, 3.3, hh, rot=sx * m.brow_lower * 0.45,
            ))
        if show_brow:
            iy = eye_y - 5.2 + 2.6 * m.brow_lower - 1.6 * m.brow_inner_raise
            oy = eye_y - 5.2 - 1.3 * m.brow_outer_raise
            shapes.append(_segment(ex - sx * 4, oy, ex + sx * 3, iy, 1.7))

    mouth_y = 21.5
    half_w = 7.0 * (1 - 0.3 * m.lip_pucker)
    if m.jaw_open > 0.10:
        shapes.append(_ellipse(
            cx, mouth_y + 1.6 * smile, half_w, 1.4 + 5.6 * m.jaw_open,
        ))
    else:
        shapes.append(_quad_stroke(
            (cx - half_w, mouth_y - 1.6 * smile),
            (cx, mouth_y + 5.2 * smile),
            (cx + half_w, mouth_y - 1.6 * smile),
            2.1,
        ))
    return shapes


def dot_grid(face: FaceState) -> list[list[float]]:
    """Per-dot coverage in [0, 1] for the 36×30 LED panel (3×3
    supersampling stands in for the canvas anti-aliasing)."""
    shapes = _shapes(face)
    offsets = [(i + 0.5) / 3 for i in range(3)]
    grid: list[list[float]] = []
    for y in range(ROWS):
        row: list[float] = []
        for x in range(COLS):
            hits = sum(
                1
                for oy in offsets
                for ox in offsets
                if any(s(x + ox, y + oy) for s in shapes)
            )
            row.append(hits / 9)
        grid.append(row)
    return grid


# ── Rasterize + PNG encode (stdlib only) ───────────────────────────


def _draw_dot(
    buf: bytearray,
    img_w: int,
    img_h: int,
    cx: float,
    cy: float,
    radius: float,
    color: tuple[int, int, int],
    alpha: float,
) -> None:
    """Alpha-blend one soft-edged dot into the RGB buffer."""
    x0 = max(0, int(cx - radius - 1))
    x1 = min(img_w - 1, int(cx + radius + 1))
    y0 = max(0, int(cy - radius - 1))
    y1 = min(img_h - 1, int(cy + radius + 1))
    r, g, b = color
    for py in range(y0, y1 + 1):
        for px in range(x0, x1 + 1):
            d = math.hypot(px + 0.5 - cx, py + 0.5 - cy)
            cover = max(0.0, min(1.0, radius + 0.7 - d))  # 1px feather
            a = alpha * cover
            if a <= 0.003:
                continue
            i = (py * img_w + px) * 3
            buf[i] = int(buf[i] * (1 - a) + r * a)
            buf[i + 1] = int(buf[i + 1] * (1 - a) + g * a)
            buf[i + 2] = int(buf[i + 2] * (1 - a) + b * a)


def _png_encode(width: int, height: int, rgb: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    stride = width * 3
    raw = b"".join(
        b"\x00" + rgb[y * stride:(y + 1) * stride] for y in range(height)
    )
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b"")
    )


def render_face_png(
    face: FaceState,
    mood_color: str = "#4FB7A6",
    mood_intensity: float = 0.3,
    scale: int = 12,
) -> bytes:
    """Render the face as a PNG — one frame of the LED panel.

    Args:
        face: The 12-muscle expression to draw.
        mood_color: Hex accent for the lit dots (the dominant emotion's
            color in the web UI palette).
        mood_intensity: Dominant-emotion strength in [0, 1] — brightens
            the lit dots, like the live renderer's glow.
        scale: Pixels per grid cell (image is 36×scale by 30×scale).
    """
    img_w, img_h = COLS * scale, ROWS * scale
    buf = bytearray(bytes(_BACKGROUND) * (img_w * img_h))
    color = _hex_rgb(mood_color)
    glow = 0.55 + 0.6 * max(0.0, min(1.0, mood_intensity))
    base_r = scale * 0.42

    grid = dot_grid(face)
    for y in range(ROWS):
        for x in range(COLS):
            lit = grid[y][x]
            px, py = (x + 0.5) * scale, (y + 0.5) * scale
            if lit > 0.06:
                alpha = min(1.0, 0.22 + 0.78 * min(1.0, lit) * glow)
                radius = base_r * (0.72 + 0.42 * lit)
                # Soft halo first, then the dot core on top.
                _draw_dot(buf, img_w, img_h, px, py, radius * 1.9,
                          color, 0.16 * lit * glow)
                _draw_dot(buf, img_w, img_h, px, py, radius, color, alpha)
            else:
                # Unlit dot — faint, so the panel reads as a grid.
                _draw_dot(buf, img_w, img_h, px, py, base_r * 0.5,
                          (255, 255, 255), 0.035)
    return _png_encode(img_w, img_h, bytes(buf))
