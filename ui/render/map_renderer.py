"""2D tile grid rendering."""

from __future__ import annotations

import pygame

from ui.render.icons import draw_portrait_frame, load_icon
from ui.theme import (
    COLOR_ENTITY_ALT,
    COLOR_ENTITY_OPPONENT,
    COLOR_ENTITY_STUDENT,
    LABEL_FONT_PT,
    MAP_PADDING,
    TILE_COLORS,
    TILE_SIZE,
)

# Name-plate colours
_NAMEPLATE_BG = (18, 22, 30, 180)
_NAMEPLATE_TEXT = (220, 225, 240)


def _tile_color(tile_type: str) -> tuple[int, int, int]:
    return TILE_COLORS.get(tile_type, TILE_COLORS["empty"])


def _lighter(color: tuple[int, int, int], amount: int = 30) -> tuple[int, int, int]:
    return tuple(min(255, c + amount) for c in color)  # type: ignore[return-value]


def _darker(color: tuple[int, int, int], amount: int = 24) -> tuple[int, int, int]:
    return tuple(max(0, c - amount) for c in color)  # type: ignore[return-value]


def _draw_tile(surface: pygame.Surface, rect: pygame.Rect, tile_type: str) -> None:
    """Draw a single tile with bevel edges and a type-specific symbol."""
    color = _tile_color(tile_type)
    pygame.draw.rect(surface, color, rect)

    # Inner bevel (1 px inset from edges so the grid outline stays clean)
    light = _lighter(color, 32)
    dark = _darker(color, 22)
    l, t, r, b = rect.left + 1, rect.top + 1, rect.right - 2, rect.bottom - 2
    pygame.draw.line(surface, light, (l, t), (r, t))        # top
    pygame.draw.line(surface, light, (l, t), (l, b))        # left
    pygame.draw.line(surface, dark,  (l, b), (r, b))        # bottom
    pygame.draw.line(surface, dark,  (r, t), (r, b))        # right

    # Grid outline
    pygame.draw.rect(surface, (42, 48, 60), rect, 1)

    # Type-specific central symbol
    cx, cy = rect.centerx, rect.centery
    if tile_type == "resource":
        # Small diamond gem
        d = max(4, TILE_SIZE // 6)
        pts = [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)]
        gem_fill = _lighter(color, 55)
        gem_edge = _lighter(color, 80)
        pygame.draw.polygon(surface, gem_fill, pts)
        pygame.draw.polygon(surface, gem_edge, pts, 1)
    elif tile_type == "obstacle":
        # Subtle crossed crack lines
        m = max(3, TILE_SIZE // 7)
        crack = _darker(color, 30)
        pygame.draw.line(surface, crack, (cx - m, cy - m), (cx + m, cy + m), 1)
        pygame.draw.line(surface, crack, (cx + m, cy - m), (cx - m, cy + m), 1)
    elif tile_type in ("pool", "station"):
        # Mana flask — bulb + narrow neck
        lw = max(4, TILE_SIZE // 5)
        nh = max(3, TILE_SIZE // 8)
        bh = max(6, TILE_SIZE // 3)
        liquid = (140, 100, 255)
        glass = _lighter(color, 60)
        neck = pygame.Rect(cx - lw // 3, cy - bh // 2 - nh, max(2, lw // 2), nh)
        bulb = pygame.Rect(cx - lw // 2, cy - bh // 2, lw, bh)
        pygame.draw.rect(surface, glass, neck, border_radius=1)
        pygame.draw.ellipse(surface, glass, bulb)
        liquid_rect = bulb.inflate(-max(2, lw // 4), -max(2, bh // 4))
        liquid_rect.top = bulb.centery - liquid_rect.height // 3
        pygame.draw.ellipse(surface, liquid, liquid_rect)
        pygame.draw.ellipse(surface, _lighter(liquid, 40), bulb, 1)


def _entity_palette_index(render_state: dict, player_id: str) -> int:
    order = [str(e["id"]) for e in render_state.get("entities", ())]
    try:
        return order.index(player_id)
    except ValueError:
        return 0


def _entity_color(render_state: dict, player_id: str) -> tuple[int, int, int]:
    if player_id == "student":
        return COLOR_ENTITY_STUDENT
    if player_id == "opponent":
        return COLOR_ENTITY_OPPONENT
    idx = _entity_palette_index(render_state, player_id)
    if idx <= 1:
        return COLOR_ENTITY_STUDENT if idx == 0 else COLOR_ENTITY_OPPONENT
    return COLOR_ENTITY_ALT[(idx - 2) % len(COLOR_ENTITY_ALT)]


def _draw_nameplate(
    surface: pygame.Surface,
    font: pygame.font.Font,
    label: str,
    center_x: int,
    top_y: int,
) -> None:
    """Render a name label with a semi-transparent dark backing pill."""
    text_surf = font.render(label, True, _NAMEPLATE_TEXT)
    tw, th = text_surf.get_size()
    pad_x, pad_y = 4, 2
    plate_rect = pygame.Rect(
        center_x - tw // 2 - pad_x,
        top_y,
        tw + pad_x * 2,
        th + pad_y * 2,
    )
    plate_surf = pygame.Surface(plate_rect.size, pygame.SRCALPHA)
    plate_surf.fill(_NAMEPLATE_BG)
    surface.blit(plate_surf, plate_rect.topleft)
    surface.blit(text_surf, (plate_rect.x + pad_x, plate_rect.y + pad_y))


def _draw_single_hp_bar(
    surface: pygame.Surface,
    x: int,
    y: int,
    bar_w: int,
    bar_h: int,
    info: dict,
    *,
    fg_color: tuple[int, int, int] | None = None,
    bg_color: tuple[int, int, int] | None = None,
) -> None:
    alive = bool(info.get("alive", int(info.get("hp", 0)) > 0))
    hp = int(info.get("hp", 0))
    max_hp = int(info.get("max_hp", 1))
    bar_bg = bg_color if bg_color is not None else _HP_BAR_BG
    bg_rect = pygame.Rect(x, y, bar_w, bar_h)
    pygame.draw.rect(surface, bar_bg, bg_rect, border_radius=2)
    if max_hp > 0:
        filled_w = max(0, round(bar_w * hp / max_hp))
        if fg_color is None:
            fg_color = _HP_BAR_PLAYER_FG if alive else _HP_BAR_DEAD
        if filled_w > 0:
            fg_rect = pygame.Rect(x, y, filled_w, bar_h)
            pygame.draw.rect(surface, fg_color, fg_rect, border_radius=2)
    pygame.draw.rect(surface, (80, 90, 110), bg_rect, 1, border_radius=2)


def draw_map(
    surface: pygame.Surface,
    render_state: dict,
    *,
    origin_y: int = 0,
    lang: str = "en",
) -> pygame.Rect:
    """Draw grid and entities; return the map bounding rect."""
    map_w = int(render_state["map_width"])
    map_h = int(render_state["map_height"])
    pixel_w = map_w * TILE_SIZE
    pixel_h = map_h * TILE_SIZE
    origin_x = (surface.get_width() - pixel_w) // 2
    origin_y = origin_y or MAP_PADDING
    map_rect = pygame.Rect(origin_x, origin_y, pixel_w, pixel_h)

    for tile in render_state["tiles"]:
        tx = int(tile["x"])
        ty = int(tile["y"])
        rect = pygame.Rect(
            origin_x + tx * TILE_SIZE,
            origin_y + ty * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        _draw_tile(surface, rect, str(tile["type"]))

    name_font = pygame.font.SysFont("consolas,courier,monospace", LABEL_FONT_PT)
    icon_size = max(18, TILE_SIZE - 6)

    for entity in render_state["entities"]:
        player_id = str(entity["id"])
        px, py = entity["position"]
        center_x = origin_x + int(px) * TILE_SIZE + TILE_SIZE // 2
        center_y = origin_y + int(py) * TILE_SIZE + TILE_SIZE // 2
        color = _entity_color(render_state, player_id)
        display_name = str(entity.get("display_name", player_id))
        icon_path = entity.get("icon")
        sprite = load_icon(str(icon_path) if icon_path else None, size=icon_size)

        # Portrait frame drawn for both sprite and fallback modes
        draw_portrait_frame(surface, (center_x, center_y), size=icon_size, color=color)

        if sprite is not None:
            surface.blit(sprite, sprite.get_rect(center=(center_x, center_y)))
        else:
            # Filled circle with initial letter
            radius = max(TILE_SIZE // 4, 7)
            pygame.draw.circle(surface, color, (center_x, center_y), radius)
            r, g, b = color
            inner_color = (min(255, r + 40), min(255, g + 40), min(255, b + 40))
            pygame.draw.circle(surface, inner_color, (center_x, center_y), radius, 2)
            initial = display_name[:1].upper() if display_name else "?"
            letter = name_font.render(initial, True, (20, 24, 30))
            surface.blit(letter, letter.get_rect(center=(center_x, center_y)))

        label = display_name if len(display_name) <= 12 else display_name[:11] + "…"
        name_top = center_y + TILE_SIZE // 2 + 3
        _draw_nameplate(surface, name_font, label, center_x, name_top)

    # Draw boss entity (boss_fight scenario)
    boss_entity = render_state.get("boss_entity")
    if boss_entity:
        _draw_boss(surface, boss_entity, origin_x, origin_y, name_font, lang=lang)

    # Draw HP bars (boss_fight scenario)
    hp_bars = render_state.get("hp_bars", {})
    if hp_bars:
        _draw_hp_bars(surface, render_state, hp_bars, origin_x, origin_y)

    # Draw pool capacity overlays (mana_pools scenario)
    pool_caps = render_state.get("pool_capacities") or render_state.get("station_capacities", {})
    if pool_caps:
        _draw_pool_overlays(surface, render_state, pool_caps, origin_x, origin_y)

    # Draw mana bars (mana_pools / mana_pools scenario)
    energy_bars = render_state.get("energy_bars", {})
    if energy_bars:
        _draw_energy_bars(surface, render_state, energy_bars, origin_x, origin_y)

    return map_rect


# ── Boss Fight extras ──────────────────────────────────────────────────────────

_BOSS_COLOR = (200, 40, 40)
_BOSS_INNER = (240, 80, 80)
_HP_BAR_BG = (18, 32, 22)
_HP_BAR_FG = (200, 60, 60)
_HP_BAR_BOSS_BG = (50, 20, 20)
_HP_BAR_BOSS_FG = (220, 50, 50)
_HP_BAR_PLAYER_FG = (60, 200, 80)
_HP_BAR_DEAD = (80, 80, 80)


def _draw_boss(
    surface: pygame.Surface,
    boss: dict,
    origin_x: int,
    origin_y: int,
    font: pygame.font.Font,
    *,
    lang: str = "en",
) -> None:
    px, py = boss["position"]
    cx = origin_x + int(px) * TILE_SIZE + TILE_SIZE // 2
    cy = origin_y + int(py) * TILE_SIZE + TILE_SIZE // 2
    radius = max(TILE_SIZE // 2 - 2, 10)
    icon_size = max(18, TILE_SIZE - 4)

    # Shadow / glow
    glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (200, 40, 40, 60), (radius * 2, radius * 2), radius + 5)
    surface.blit(glow_surf, (cx - radius * 2, cy - radius * 2))

    icon_path = boss.get("icon")
    sprite = load_icon(str(icon_path) if icon_path else None, size=icon_size)
    if sprite is not None:
        draw_portrait_frame(surface, (cx, cy), size=icon_size, color=_BOSS_COLOR)
        surface.blit(sprite, sprite.get_rect(center=(cx, cy)))
    else:
        pygame.draw.circle(surface, _BOSS_COLOR, (cx, cy), radius)
        pygame.draw.circle(surface, _BOSS_INNER, (cx, cy), radius, 3)
        ltr = font.render("B", True, (255, 230, 180))
        surface.blit(ltr, ltr.get_rect(center=(cx, cy)))

    # Nameplate (no HP numbers — shown on the bar above)
    from engine.i18n import translate

    default_boss = translate("render.boss", lang=lang)
    display_name = str(boss.get("display_name", default_boss))
    if display_name == "Boss" and lang != "en":
        display_name = default_boss
    label = display_name if len(display_name) <= 12 else display_name[:11] + "…"
    name_top = cy + radius + 3
    _draw_nameplate(surface, font, label, cx, name_top)

    # Red HP bar above the boss tile (matches student bar placement)
    bar_w = TILE_SIZE - 6
    bar_h = 4
    bx = origin_x + int(px) * TILE_SIZE + 3
    by = origin_y + int(py) * TILE_SIZE + 2
    hp = int(boss.get("hp", 0))
    boss_fg = _HP_BAR_BOSS_FG if hp > 0 else _HP_BAR_DEAD
    _draw_single_hp_bar(
        surface,
        bx,
        by,
        bar_w,
        bar_h,
        boss,
        fg_color=boss_fg,
        bg_color=_HP_BAR_BOSS_BG,
    )


def _draw_hp_bars(
    surface: pygame.Surface,
    render_state: dict,
    hp_bars: dict,
    origin_x: int,
    origin_y: int,
) -> None:
    """Draw small HP bars above each entity that has HP data."""
    bar_w = TILE_SIZE - 6
    bar_h = 4
    for entity in render_state.get("entities", ()):
        pid = str(entity["id"])
        if pid not in hp_bars:
            continue
        info = hp_bars[pid]
        px, py_e = entity["position"]
        ex = origin_x + int(px) * TILE_SIZE + 3
        ey = origin_y + int(py_e) * TILE_SIZE + 2
        _draw_single_hp_bar(
            surface, ex, ey, bar_w, bar_h, info, bg_color=_HP_BAR_BG,
        )


# ── Mana Pools extras ─────────────────────────────────────────────────────────

_MANA_BAR_BG = (20, 16, 40)
_MANA_BAR_FG = (90, 120, 255)    # bright mana blue — distinct from HP green
_POOL_BAR_BG = (24, 16, 36)
_POOL_BAR_FG = (180, 120, 255)   # lavender — remaining pool capacity


def _draw_pool_overlays(
    surface: pygame.Surface,
    render_state: dict,
    pool_caps: dict,
    origin_x: int,
    origin_y: int,
) -> None:
    """Draw lavender capacity bars on mana pool tiles (same placement as HP bars)."""
    max_cap = int(
        render_state.get("pool_max_capacity")
        or render_state.get("station_max_capacity", 0)
    )
    bar_w = TILE_SIZE - 6
    bar_h = 4
    for key, cap in pool_caps.items():
        try:
            sx, sy = (int(v) for v in str(key).split(","))
        except ValueError:
            continue
        capacity = int(cap)
        bar_max = max_cap if max_cap > 0 else max(capacity, 1)
        bx = origin_x + sx * TILE_SIZE + 3
        by = origin_y + sy * TILE_SIZE + 2
        _draw_single_hp_bar(
            surface,
            bx,
            by,
            bar_w,
            bar_h,
            {"hp": capacity, "max_hp": bar_max, "alive": capacity > 0},
            fg_color=_POOL_BAR_FG,
            bg_color=_POOL_BAR_BG,
        )


def _draw_energy_bars(
    surface: pygame.Surface,
    render_state: dict,
    energy_bars: dict,
    origin_x: int,
    origin_y: int,
) -> None:
    """Draw mana bars above each entity — positioned below HP bar if both present."""
    bar_w = TILE_SIZE - 6
    bar_h = 4
    hp_bars = render_state.get("hp_bars", {})
    for entity in render_state.get("entities", ()):
        pid = str(entity["id"])
        if pid not in energy_bars:
            continue
        info = energy_bars[pid]
        energy = int(info.get("energy", 0))
        max_energy = int(info.get("max_energy", 1)) or 1
        px, py_e = entity["position"]
        ex = origin_x + int(px) * TILE_SIZE + 3
        # Stack below HP bar if present, otherwise use top row
        base_ey = origin_y + int(py_e) * TILE_SIZE + 2
        ey = base_ey + bar_h + 2 if pid in hp_bars else base_ey

        bg_rect = pygame.Rect(ex, ey, bar_w, bar_h)
        pygame.draw.rect(surface, _MANA_BAR_BG, bg_rect, border_radius=2)
        filled_w = max(0, round(bar_w * energy / max_energy))
        if filled_w > 0:
            fg_rect = pygame.Rect(ex, ey, filled_w, bar_h)
            pygame.draw.rect(surface, _MANA_BAR_FG, fg_rect, border_radius=2)
        pygame.draw.rect(surface, (50, 40, 90), bg_rect, 1, border_radius=2)
