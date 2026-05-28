"""Cached entity icon surfaces and procedural menu icons."""

from __future__ import annotations

from pathlib import Path

import pygame

_ICON_CACHE: dict[str, pygame.Surface | None] = {}
_MENU_ICON_CACHE: dict[tuple[str, int, tuple[int, int, int]], pygame.Surface] = {}


def load_icon(path: str | None, *, size: int = 24) -> pygame.Surface | None:
    if not path:
        return None
    key = f"{path}:{size}"
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    file_path = Path(path)
    if not file_path.is_file():
        _ICON_CACHE[key] = None
        return None

    try:
        image = pygame.image.load(str(file_path)).convert_alpha()
        image = pygame.transform.smoothscale(image, (size, size))
        _ICON_CACHE[key] = image
        return image
    except pygame.error:
        _ICON_CACHE[key] = None
        return None


def draw_portrait_frame(
    surface: pygame.Surface,
    center: tuple[int, int],
    *,
    size: int = 32,
    color: tuple[int, int, int] = (100, 72, 48),
) -> None:
    """Decorative portrait border tinted to the entity's color."""
    half = size // 2 + 3
    rect = pygame.Rect(center[0] - half, center[1] - half, half * 2, half * 2)

    # Semi-transparent tinted backdrop
    r, g, b = color
    bg = pygame.Surface(rect.size, pygame.SRCALPHA)
    bg.fill((max(0, r - 55), max(0, g - 55), max(0, b - 55), 150))
    surface.blit(bg, rect.topleft)

    # Outer border in entity color
    pygame.draw.rect(surface, color, rect, 2, border_radius=4)
    # Thin inner highlight ring
    inner = rect.inflate(-4, -4)
    if inner.width > 4:
        lighter = (min(255, r + 60), min(255, g + 60), min(255, b + 60))
        pygame.draw.rect(surface, lighter, inner, 1, border_radius=3)
    # Dark outer halo for contrast against any tile colour
    pygame.draw.rect(surface, (16, 20, 28), rect.inflate(2, 2), 1, border_radius=5)


def clear_icon_cache() -> None:
    _ICON_CACHE.clear()
    _MENU_ICON_CACHE.clear()


def draw_menu_icon(
    surface: pygame.Surface,
    name: str,
    rect: pygame.Rect,
    color: tuple[int, int, int] = (240, 200, 80),
) -> None:
    """Draw a small procedural RPG-style icon into *rect* on *surface*.

    Supported names: ``swords``, ``scroll``, ``folder``, ``shield``,
    ``classroom``, ``door``, ``random``, ``flag_en``, ``flag_uk``.
    """
    key: tuple[str, int, tuple[int, int, int]] = (name, rect.width, color)
    if key not in _MENU_ICON_CACHE:
        _MENU_ICON_CACHE[key] = _render_menu_icon(name, rect.width, color)
    icon_surf = _MENU_ICON_CACHE[key]
    cy = rect.y + (rect.height - icon_surf.get_height()) // 2
    surface.blit(icon_surf, (rect.x, cy))


def _render_menu_icon(
    name: str,
    size: int,
    color: tuple[int, int, int],
) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    s = size
    c = color
    dim = (max(0, c[0] - 60), max(0, c[1] - 60), max(0, c[2] - 60))

    if name == "swords":
        # Two crossed diagonal lines (X) with small crossguards
        w = max(1, s // 8)
        pygame.draw.line(surf, c, (2, 2), (s - 3, s - 3), w)
        pygame.draw.line(surf, c, (s - 3, 2), (2, s - 3), w)
        mid = s // 2
        gw = s // 3
        pygame.draw.line(surf, dim, (mid - gw // 2, mid - 1), (mid + gw // 2, mid - 1), max(1, w - 1))

    elif name == "scroll":
        # Rounded rect with horizontal content lines
        r = max(2, s // 5)
        pygame.draw.rect(surf, c, pygame.Rect(1, 2, s - 2, s - 4), border_radius=r)
        pygame.draw.rect(surf, dim, pygame.Rect(1, 2, s - 2, s - 4), 1, border_radius=r)
        line_color = (max(0, c[0] - 80), max(0, c[1] - 80), max(0, c[2] - 80))
        for i in range(1, 4):
            y = 2 + i * (s - 4) // 4
            pygame.draw.line(surf, line_color, (r, y), (s - r - 1, y), 1)

    elif name == "folder":
        # Open folder: bottom rect + top flap
        tab_h = s // 4
        body_y = tab_h
        pygame.draw.rect(surf, c, pygame.Rect(0, body_y, s, s - body_y - 1), border_radius=2)
        tab_w = s * 2 // 5
        pygame.draw.polygon(surf, c, [
            (1, body_y),
            (tab_w + 1, body_y),
            (tab_w - 1, 2),
            (1, 2),
        ])
        pygame.draw.rect(surf, dim, pygame.Rect(0, body_y, s, s - body_y - 1), 1, border_radius=2)

    elif name == "shield":
        # Pentagon shield
        mid_x = s // 2
        pts = [
            (1, 1),
            (s - 2, 1),
            (s - 2, s * 3 // 5),
            (mid_x, s - 2),
            (1, s * 3 // 5),
        ]
        pygame.draw.polygon(surf, c, pts)
        pygame.draw.polygon(surf, dim, pts, 1)
        # Small cross/emblem in centre
        inner = s // 5
        pygame.draw.line(surf, dim, (mid_x, s // 5), (mid_x, s * 3 // 5), max(1, s // 8))
        pygame.draw.line(surf, dim, (mid_x - inner, s // 3), (mid_x + inner, s // 3), max(1, s // 8))

    elif name == "classroom":
        # Two simplified humanoid figures side by side
        fig_w = max(3, s // 3)
        for i, fx in enumerate([s // 4 - fig_w // 2, s * 3 // 4 - fig_w // 2]):
            head_r = max(2, s // 8)
            head_cx = fx + fig_w // 2
            head_cy = s // 4
            pygame.draw.circle(surf, c, (head_cx, head_cy), head_r)
            body_top = head_cy + head_r
            body_bot = s * 3 // 4
            pygame.draw.line(surf, c, (head_cx, body_top), (head_cx, body_bot), max(1, s // 10))
            # arms
            arm_y = body_top + (body_bot - body_top) // 3
            pygame.draw.line(surf, c, (fx, arm_y), (fx + fig_w, arm_y), max(1, s // 10))
            # legs
            pygame.draw.line(surf, c, (head_cx, body_bot), (fx + 1, s - 2), max(1, s // 10))
            pygame.draw.line(surf, c, (head_cx, body_bot), (fx + fig_w - 1, s - 2), max(1, s // 10))

    elif name == "door":
        # Door rectangle with arch/oval at top
        door_x, door_w = s // 4, s // 2
        door_y = s // 5
        pygame.draw.rect(surf, c, pygame.Rect(door_x, door_y, door_w, s - door_y - 1))
        pygame.draw.rect(surf, dim, pygame.Rect(door_x, door_y, door_w, s - door_y - 1), 1)
        # knob
        knob_x = door_x + door_w * 3 // 4
        knob_y = door_y + (s - door_y) // 2
        pygame.draw.circle(surf, dim, (knob_x, knob_y), max(1, s // 10))

    elif name == "random":
        # Dice face with dots
        r = max(2, s // 6)
        pygame.draw.rect(surf, c, pygame.Rect(1, 1, s - 2, s - 2), border_radius=r)
        pygame.draw.rect(surf, dim, pygame.Rect(1, 1, s - 2, s - 2), 1, border_radius=r)
        dot_r = max(1, s // 8)
        dot_color = (max(0, c[0] - 100), max(0, c[1] - 100), max(0, c[2] - 100))
        for dx, dy in [(1, 1), (-1, -1), (1, -1), (-1, 1), (0, 0)]:
            px = s // 2 + dx * s // 4
            py = s // 2 + dy * s // 4
            pygame.draw.circle(surf, dot_color, (px, py), dot_r)

    elif name == "arrow_up":
        # Filled upward-pointing triangle with a subtle stem
        mid = s // 2
        tip = 2
        base = s - 3
        margin = max(2, s // 5)
        pts = [(mid, tip), (s - margin, base), (margin, base)]
        pygame.draw.polygon(surf, c, pts)
        # thin stem below
        stem_w = max(1, s // 5)
        pygame.draw.rect(surf, dim,
                         pygame.Rect(mid - stem_w // 2, base - 1, stem_w, s - base))

    elif name == "arrow_down":
        # Filled downward-pointing triangle with a subtle stem
        mid = s // 2
        tip = s - 2
        base = 3
        margin = max(2, s // 5)
        pts = [(mid, tip), (s - margin, base), (margin, base)]
        pygame.draw.polygon(surf, c, pts)
        stem_w = max(1, s // 5)
        pygame.draw.rect(surf, dim,
                         pygame.Rect(mid - stem_w // 2, 0, stem_w, base + 1))

    elif name == "flag_en":
        # UK / English — simplified Union Jack in a rounded rect
        r = max(2, s // 8)
        pygame.draw.rect(surf, (20, 40, 120), pygame.Rect(1, 2, s - 2, s - 4), border_radius=r)
        pygame.draw.rect(surf, (180, 30, 40), pygame.Rect(1, 2, s - 2, s - 4), 1, border_radius=r)
        w = max(1, s // 6)
        mid = s // 2
        pygame.draw.line(surf, (240, 240, 245), (2, 2), (s - 2, s - 2), w)
        pygame.draw.line(surf, (240, 240, 245), (s - 2, 2), (2, s - 2), w)
        pygame.draw.line(surf, (180, 30, 40), (mid, 2), (mid, s - 2), max(1, w - 1))
        pygame.draw.line(surf, (180, 30, 40), (2, mid), (s - 2, mid), max(1, w - 1))

    elif name == "flag_uk":
        # Ukrainian flag — blue over yellow
        r = max(2, s // 8)
        half = s // 2
        pygame.draw.rect(surf, (0, 87, 183), pygame.Rect(1, 2, s - 2, half - 1), border_top_left_radius=r, border_top_right_radius=r)
        pygame.draw.rect(surf, (255, 215, 0), pygame.Rect(1, half, s - 2, half - 2), border_bottom_left_radius=r, border_bottom_right_radius=r)
        pygame.draw.rect(surf, (40, 40, 40), pygame.Rect(1, 2, s - 2, s - 4), 1, border_radius=r)

    return surf
