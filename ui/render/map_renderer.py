"""2D tile grid rendering."""

from __future__ import annotations

import pygame

from ui.theme import (
    COLOR_ENTITY_OPPONENT,
    COLOR_ENTITY_STUDENT,
    MAP_PADDING,
    TILE_COLORS,
    TILE_SIZE,
)


def _tile_color(tile_type: str) -> tuple[int, int, int]:
    return TILE_COLORS.get(tile_type, TILE_COLORS["empty"])


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

    for entity in render_state["entities"]:
        player_id = str(entity["id"])
        px, py = entity["position"]
        center_x = origin_x + int(px) * TILE_SIZE + TILE_SIZE // 2
        center_y = origin_y + int(py) * TILE_SIZE + TILE_SIZE // 2
        color = COLOR_ENTITY_STUDENT if player_id == "student" else COLOR_ENTITY_OPPONENT
        pygame.draw.circle(surface, color, (center_x, center_y), TILE_SIZE // 3)
        pygame.draw.circle(surface, (20, 24, 30), (center_x, center_y), TILE_SIZE // 3, 2)

    return map_rect
