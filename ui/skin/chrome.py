"""High-level chrome drawing — fully procedural RPG skin.

Sliced-PNG assets are used as an optional enhancement when available;
all functions render a complete, polished result without any external files.
"""

from __future__ import annotations

import pygame

from ui.skin import assets, colors
from ui.skin.typography import body_font, title_font

PanelStyle = str  # stone | wood | parchment

# ── Padding constants used by chrome drawing ──────────────────────────────────
PANEL_PAD_X = 12
PANEL_PAD_Y = 8

# ── Background vignette cache ─────────────────────────────────────────────────
_vignette_cache: dict[tuple[int, int], pygame.Surface] = {}


def _build_vignette(width: int, height: int) -> pygame.Surface:
    """Radial warm reddish-brown vignette on a transparent surface."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    cx, cy = width // 2, height // 2
    # Draw 12 concentric ellipses from outside in, decreasing alpha
    steps = 14
    for i in range(steps):
        t = i / steps  # 0 = outermost, 1 = center
        alpha = int(180 * (1.0 - t) ** 2)
        r, g, b = colors.VIGNETTE_WARM
        ellipse_w = int(width * (1.0 - t * 0.3))
        ellipse_h = int(height * (1.0 - t * 0.3))
        ex = cx - ellipse_w // 2
        ey = cy - ellipse_h // 2
        if ellipse_w > 0 and ellipse_h > 0:
            layer = pygame.Surface((ellipse_w, ellipse_h), pygame.SRCALPHA)
            layer.fill((r, g, b, alpha))
            surf.blit(layer, (ex, ey))
    return surf


# ── Core primitive helpers ────────────────────────────────────────────────────

def _draw_border_layers(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    outer_color: tuple[int, int, int],
    outer_width: int,
    highlight_color: tuple[int, int, int],
    shadow_color: tuple[int, int, int],
    radius: int,
) -> None:
    """Draw thick outer border, then inner bevel highlight/shadow."""
    # Outer border
    pygame.draw.rect(surface, outer_color, rect, outer_width, border_radius=radius)
    # Inner highlight (top + left edges only, 1px inside the outer border)
    inner = rect.inflate(-(outer_width * 2), -(outer_width * 2))
    if inner.width > 4 and inner.height > 4:
        # top highlight
        pygame.draw.line(
            surface, highlight_color,
            (inner.left + radius // 2, inner.top),
            (inner.right - radius // 2, inner.top),
        )
        # left highlight
        pygame.draw.line(
            surface, highlight_color,
            (inner.left, inner.top + radius // 2),
            (inner.left, inner.bottom - radius // 2),
        )
        # bottom shadow
        pygame.draw.line(
            surface, shadow_color,
            (inner.left + radius // 2, inner.bottom),
            (inner.right - radius // 2, inner.bottom),
        )
        # right shadow
        pygame.draw.line(
            surface, shadow_color,
            (inner.right, inner.top + radius // 2),
            (inner.right, inner.bottom - radius // 2),
        )


def _draw_rivets(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    size: int = 5,
    inset: int = 6,
) -> None:
    """Small metallic rivet squares at each corner."""
    positions = [
        (rect.left + inset, rect.top + inset),
        (rect.right - inset - size, rect.top + inset),
        (rect.left + inset, rect.bottom - inset - size),
        (rect.right - inset - size, rect.bottom - inset - size),
    ]
    for x, y in positions:
        r = pygame.Rect(x, y, size, size)
        pygame.draw.rect(surface, colors.RIVET, r, border_radius=2)
        # Shadow on bottom-right
        pygame.draw.line(surface, colors.RIVET_SHADOW, (x, y + size - 1), (x + size - 1, y + size - 1))
        pygame.draw.line(surface, colors.RIVET_SHADOW, (x + size - 1, y), (x + size - 1, y + size - 1))


def _draw_wood_grain(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    count: int = 4,
    inset: int = 8,
) -> None:
    """Subtle horizontal grain lines inside a wood panel."""
    if rect.height < inset * 2 + count * 4:
        return
    spacing = (rect.height - inset * 2) // (count + 1)
    for i in range(1, count + 1):
        y = rect.top + inset + i * spacing
        x0 = rect.left + inset + 4
        x1 = rect.right - inset - 4
        if x1 > x0:
            grain_surf = pygame.Surface((x1 - x0, 1), pygame.SRCALPHA)
            grain_surf.fill((*colors.WOOD_GRAIN, 90))
            surface.blit(grain_surf, (x0, y))


def _draw_parchment_age(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Semi-transparent darker edges on a parchment panel for an aged look."""
    depth = min(14, rect.width // 6, rect.height // 6)
    if depth < 2:
        return
    r, g, b = colors.PARCHMENT_EDGE
    for d in range(depth):
        alpha = int(60 * (1.0 - d / depth))
        edge = pygame.Surface((rect.width - d * 2, rect.height - d * 2), pygame.SRCALPHA)
        edge.fill((r, g, b, 0))
        # Only draw the border ring of the edge surface
        pygame.draw.rect(edge, (r, g, b, alpha), edge.get_rect(), 1, border_radius=max(0, 8 - d))
        surface.blit(edge, (rect.left + d, rect.top + d))


# ── Public drawing API ─────────────────────────────────────────────────────────

def draw_background(surface: pygame.Surface) -> None:
    """Dark RPG background with warm radial vignette."""
    surf = assets.get_surface("bg_main")
    if surf is not None:
        scaled = pygame.transform.smoothscale(surf, surface.get_size())
        surface.blit(scaled, (0, 0))
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((20, 24, 32, 140))
        surface.blit(overlay, (0, 0))
        return

    surface.fill(colors.SLATE_DARK)
    w, h = surface.get_size()
    key = (w, h)
    if key not in _vignette_cache:
        _vignette_cache[key] = _build_vignette(w, h)
    surface.blit(_vignette_cache[key], (0, 0))


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    style: PanelStyle = "stone",
) -> None:
    """Draw a RPG-styled panel (stone / wood / parchment) procedurally."""
    if rect.width <= 0 or rect.height <= 0:
        return

    # Try sliced asset first
    asset_map = {"stone": "panel_stone", "wood": "panel_wood", "parchment": "panel_parchment"}
    name = asset_map.get(style, "panel_stone")
    src = assets.get_surface(name)
    if src is not None:
        from ui.skin import nine_patch
        nine_patch.draw_nine_patch(surface, src, rect, border=assets.nine_slice_for(name))
        return

    radius = 6

    if style == "stone":
        # Fill
        pygame.draw.rect(surface, colors.SLATE_PANEL, rect, border_radius=radius)
        # Border layers
        _draw_border_layers(
            surface, rect,
            outer_color=colors.STONE_BORDER,
            outer_width=3,
            highlight_color=colors.STONE_HIGHLIGHT,
            shadow_color=colors.STONE_SHADOW,
            radius=radius,
        )
        # Corner rivets
        if rect.width >= 28 and rect.height >= 28:
            _draw_rivets(surface, rect, size=5, inset=6)

    elif style == "wood":
        pygame.draw.rect(surface, colors.WOOD_FILL, rect, border_radius=radius)
        _draw_wood_grain(surface, rect, count=4, inset=8)
        _draw_border_layers(
            surface, rect,
            outer_color=colors.WOOD_BORDER,
            outer_width=3,
            highlight_color=colors.WOOD_LIGHT,
            shadow_color=(60, 40, 24),
            radius=radius,
        )
        # Small corner pin circles
        if rect.width >= 28 and rect.height >= 28:
            for cx, cy in [
                (rect.left + 8, rect.top + 8),
                (rect.right - 9, rect.top + 8),
                (rect.left + 8, rect.bottom - 9),
                (rect.right - 9, rect.bottom - 9),
            ]:
                pygame.draw.circle(surface, colors.RIVET, (cx, cy), 4)
                pygame.draw.circle(surface, colors.RIVET_SHADOW, (cx, cy), 4, 1)

    else:  # parchment
        radius = 8
        pygame.draw.rect(surface, colors.PARCHMENT, rect, border_radius=radius)
        _draw_parchment_age(surface, rect)
        pygame.draw.rect(surface, colors.PARCHMENT_EDGE, rect, 2, border_radius=radius)


def draw_banner_title(
    surface: pygame.Surface,
    text: str,
    *,
    center_x: int,
    y: int,
    max_width: int | None = None,
) -> pygame.Rect:
    """Draw a stone banner with gold text, clipped to max_width."""
    font = title_font(28)
    label = font.render(text.upper(), True, colors.GOLD_TEXT)
    pad_x, pad_y = 28, 10

    bw = label.get_width() + pad_x * 2
    bh = label.get_height() + pad_y * 2
    if max_width:
        bw = min(bw, max_width)
    rect = pygame.Rect(center_x - bw // 2, y, bw, bh)

    banner = assets.get_surface("banner_title")
    if banner is not None:
        from ui.skin import nine_patch
        nine_patch.draw_nine_patch(surface, banner, rect, border=assets.nine_slice_for("banner_title"))
    else:
        # Procedural banner: stone panel with notch accents on left/right
        draw_panel(surface, rect, style="stone")
        # Small decorative notches (triangular indent illusion) at left and right center
        notch = 6
        mid_y = rect.centery
        for nx, direction in [(rect.left, 1), (rect.right - 1, -1)]:
            pts = [
                (nx, mid_y - notch),
                (nx + direction * notch, mid_y),
                (nx, mid_y + notch),
            ]
            pygame.draw.polygon(surface, colors.STONE_SHADOW, pts)

    # Clip text to banner interior
    inner_w = rect.width - pad_x * 2
    if label.get_width() > inner_w and inner_w > 0:
        # Truncate text to fit
        while len(text) > 1 and font.render(text.upper() + "…", True, colors.GOLD_TEXT).get_width() > inner_w:
            text = text[:-1]
        label = font.render(text.upper() + "…", True, colors.GOLD_TEXT)

    tx = rect.x + (rect.width - label.get_width()) // 2
    ty = rect.y + (rect.height - label.get_height()) // 2
    old_clip = surface.get_clip()
    surface.set_clip(rect.inflate(-4, -2))
    surface.blit(label, (tx, ty))
    surface.set_clip(old_clip)
    return rect


def draw_primary_button(
    surface: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    *,
    hovered: bool = False,
    pressed: bool = False,
    enabled: bool = True,
) -> None:
    """Draw a primary (stone + gold border) button, fully procedural."""
    src = assets.get_surface("button_primary")
    if src is not None:
        from ui.skin import nine_patch
        nine_patch.draw_nine_patch(surface, src, rect, border=assets.nine_slice_for("button_primary"))
        tint = pygame.Surface(rect.size, pygame.SRCALPHA)
        if not enabled:
            tint.fill((60, 60, 60, 110))
        elif pressed:
            tint.fill((0, 0, 0, 80))
        elif hovered:
            tint.fill((255, 220, 120, 40))
        if tint.get_at((0, 0))[3]:
            surface.blit(tint, rect.topleft)
    else:
        radius = 5
        # Choose fill
        if not enabled:
            fill = (42, 46, 56)
        elif pressed:
            fill = colors.BUTTON_PRESSED
        elif hovered:
            fill = colors.BUTTON_HOVER
        else:
            fill = colors.SLATE_PANEL

        pygame.draw.rect(surface, fill, rect, border_radius=radius)
        # Gold border (2px outer)
        border_color = (140, 110, 40) if not enabled else colors.GOLD_TEXT
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=radius)
        # Inner bevel
        inner = rect.inflate(-4, -4)
        if inner.width > 4 and inner.height > 4:
            pygame.draw.line(surface, colors.STONE_HIGHLIGHT,
                             (inner.left + 2, inner.top), (inner.right - 2, inner.top))
            pygame.draw.line(surface, colors.STONE_SHADOW,
                             (inner.left + 2, inner.bottom), (inner.right - 2, inner.bottom))
        # Hover glow: thin gold inner ring
        if hovered and enabled:
            glow = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (*colors.GOLD_TEXT, 35), glow.get_rect(), border_radius=radius)
            surface.blit(glow, rect.topleft)

    # Text — centered, clipped
    shift_y = 1 if pressed else 0
    font = body_font(18)
    text_color = (140, 120, 50) if not enabled else colors.GOLD_TEXT
    text_surf = font.render(label, True, text_color)
    pad_x = 10
    available_w = rect.width - pad_x * 2
    # Truncate if necessary
    display = label
    while display and text_surf.get_width() > available_w:
        display = display[:-1]
        text_surf = font.render(display + "…", True, text_color)

    old_clip = surface.get_clip()
    surface.set_clip(rect.inflate(-2, -2))
    surface.blit(
        text_surf,
        (
            rect.x + (rect.width - text_surf.get_width()) // 2,
            rect.y + (rect.height - text_surf.get_height()) // 2 + shift_y,
        ),
    )
    surface.set_clip(old_clip)


def draw_toolbar_strip(surface: pygame.Surface, *, y: int, height: int) -> None:
    """A full-width stone toolbar strip."""
    rect = pygame.Rect(0, y, surface.get_width(), height)
    draw_panel(surface, rect, style="stone")


def draw_category_ribbon(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    category: str,
) -> None:
    """Colored category ribbon (teal / purple) with centered label."""
    is_teal = category in ("efficiency", "runtime", "praise")
    name = "ribbon_teal" if is_teal else "ribbon_purple"
    src = assets.get_surface(name)
    if src is not None:
        scaled = pygame.transform.smoothscale(src, (rect.width, rect.height))
        surface.blit(scaled, rect.topleft)
        return

    base_color = colors.TEAL_ACCENT if is_teal else colors.PURPLE_ACCENT
    r, g, b = base_color
    darker = (max(0, r - 30), max(0, g - 30), max(0, b - 30))
    pygame.draw.rect(surface, base_color, rect, border_radius=4)
    pygame.draw.rect(surface, darker, rect, 1, border_radius=4)
    # Inner highlight line at top
    if rect.height >= 6:
        lighter = (min(255, r + 40), min(255, g + 40), min(255, b + 40))
        pygame.draw.line(
            surface, lighter,
            (rect.left + 6, rect.top + 1),
            (rect.right - 6, rect.top + 1),
        )


def draw_divider(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    horizontal: bool = True,
) -> None:
    """A thin divider bar with bevel highlight."""
    pygame.draw.rect(surface, colors.STONE_SHADOW, rect)
    if horizontal:
        pygame.draw.line(surface, colors.STONE_HIGHLIGHT,
                         (rect.left, rect.top), (rect.right, rect.top))
    else:
        pygame.draw.line(surface, colors.STONE_HIGHLIGHT,
                         (rect.left, rect.top), (rect.left, rect.bottom))


def draw_panel_titled(
    surface: pygame.Surface,
    rect: pygame.Rect,
    title: str,
    *,
    style: PanelStyle = "stone",
    title_pt: int = 15,
) -> pygame.Rect:
    """Draw a named panel with a decorative title header bar.

    The header bar is inset at the top of the panel interior with gold text
    and flanking diamond ornaments.  Returns the inner content rect below
    the header — usable area for widgets or sub-content.

    Content rect geometry (for pre-computing widget positions):
      content_y = rect.y + 3 + (title_pt + 14) + 1 + 4 + PANEL_PAD_Y
                = rect.y + 3 + 29 + 13  (title_pt=15, PANEL_PAD_Y=8)
                = rect.y + 45
      content_x = rect.x + PANEL_PAD_X  (= rect.x + 12)
    """
    if rect.width <= 0 or rect.height <= 0:
        return rect

    draw_panel(surface, rect, style=style)

    inset = 3
    header_h = title_pt + 14
    hdr = pygame.Rect(rect.x + inset, rect.y + inset,
                      rect.width - inset * 2, header_h)

    if style == "stone":
        hdr_fill = (44, 50, 62)
    elif style == "wood":
        hdr_fill = colors.WOOD_BORDER
    else:
        hdr_fill = colors.PARCHMENT_EDGE

    pygame.draw.rect(surface, hdr_fill, hdr, border_radius=3)
    pygame.draw.line(surface, colors.STONE_HIGHLIGHT,
                     (hdr.left + 4, hdr.top), (hdr.right - 4, hdr.top))

    # Small diamond ornaments flanking the title
    mid_y = hdr.centery
    for dot_x in [hdr.left + 14, hdr.right - 14]:
        pts = [
            (dot_x, mid_y - 4),
            (dot_x + 4, mid_y),
            (dot_x, mid_y + 4),
            (dot_x - 4, mid_y),
        ]
        pygame.draw.polygon(surface, colors.GOLD_TEXT, pts)

    font = body_font(title_pt)
    draw_text_clipped(surface, title.upper(), hdr, font, colors.GOLD_TEXT,
                      align="center", pad_x=30)

    div_y = hdr.bottom + 1
    pygame.draw.line(surface, colors.GOLD_TEXT,
                     (rect.left + 6, div_y), (rect.right - 6, div_y))
    pygame.draw.line(surface, colors.STONE_SHADOW,
                     (rect.left + 6, div_y + 1), (rect.right - 6, div_y + 1))

    content_top = div_y + 4 + PANEL_PAD_Y
    return pygame.Rect(
        rect.x + PANEL_PAD_X,
        content_top,
        rect.width - PANEL_PAD_X * 2,
        rect.bottom - content_top - PANEL_PAD_Y,
    )


def draw_ornamental_divider(
    surface: pygame.Surface,
    rect: pygame.Rect,
) -> None:
    """Horizontal ornamental divider with a central diamond and flanking marks."""
    mid_y = rect.centery
    cx = rect.centerx

    pygame.draw.line(surface, colors.STONE_SHADOW,
                     (rect.left, mid_y + 1), (rect.right, mid_y + 1))
    pygame.draw.line(surface, colors.STONE_HIGHLIGHT,
                     (rect.left, mid_y), (rect.right, mid_y))

    d = 5
    pts = [(cx, mid_y - d), (cx + d, mid_y), (cx, mid_y + d), (cx - d, mid_y)]
    pygame.draw.polygon(surface, colors.STONE_BORDER, pts)
    pygame.draw.polygon(surface, colors.GOLD_TEXT, pts, 1)

    for fx in [cx - 22, cx + 22]:
        pygame.draw.line(surface, colors.STONE_SHADOW,
                         (fx, mid_y - 3), (fx, mid_y + 3))


def draw_text_clipped(
    surface: pygame.Surface,
    text: str,
    rect: pygame.Rect,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    *,
    align: str = "left",
    pad_x: int = 0,
    pad_y: int = 0,
) -> pygame.Rect:
    """Render text clipped to rect with optional padding. Returns the blit rect.

    If text overflows the available width, it is truncated with an ellipsis.
    """
    inner = rect.inflate(-pad_x * 2, -pad_y * 2)
    avail_w = max(0, inner.width)

    surf = font.render(text, True, color)
    if surf.get_width() > avail_w and avail_w > 0:
        while len(text) > 1:
            text = text[:-1]
            candidate = font.render(text + "…", True, color)
            if candidate.get_width() <= avail_w:
                surf = candidate
                break
        else:
            surf = font.render("…", True, color)

    if align == "center":
        x = inner.x + (inner.width - surf.get_width()) // 2
    elif align == "right":
        x = inner.right - surf.get_width()
    else:
        x = inner.x

    y = inner.y + (inner.height - surf.get_height()) // 2

    old_clip = surface.get_clip()
    surface.set_clip(inner)
    blit_pos = (x, y)
    surface.blit(surf, blit_pos)
    surface.set_clip(old_clip)
    return pygame.Rect(x, y, surf.get_width(), surf.get_height())
