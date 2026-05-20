"""2D tile grid rendering."""

from __future__ import annotations

import pygame

from ui.render.icons import load_icon
from ui.theme import (
    COLOR_ENTITY_ALT,
    COLOR_ENTITY_OPPONENT,
    COLOR_ENTITY_STUDENT,
    COLOR_MUTED,
    COLOR_TEXT,
    LABEL_FONT_PT,
    MAP_PADDING,
    TILE_COLORS,
    TILE_SIZE,
)


def _tile_color(tile_type: str) -> tuple[int, int, int]:
    return TILE_COLORS.get(tile_type, TILE_COLORS["empty"])


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


def draw_map(surface: pygame.Surface, render_state: dict, *, origin_y: int = 0) -> pygame.Rect:
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
        pygame.draw.rect(surface, _tile_color(str(tile["type"])), rect)
        pygame.draw.rect(surface, (30, 34, 42), rect, 1)

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

        if sprite is not None:
            rect = sprite.get_rect(center=(center_x, center_y))
            surface.blit(sprite, rect)
        else:
            radius = max(TILE_SIZE // 4, 6)
            pygame.draw.circle(surface, color, (center_x, center_y), radius)
            pygame.draw.circle(surface, (20, 24, 30), (center_x, center_y), radius, 2)
            initial = display_name[:1].upper() if display_name else "?"
            letter = name_font.render(initial, True, COLOR_TEXT)
            surface.blit(
                letter,
                letter.get_rect(center=(center_x, center_y)),
            )

        label = display_name if len(display_name) <= 12 else display_name[:11] + "…"
        name_surf = name_font.render(label, True, COLOR_MUTED)
        name_rect = name_surf.get_rect(midtop=(center_x, center_y + TILE_SIZE // 2 + 2))
        surface.blit(name_surf, name_rect)

    return map_rect
