"""Draw scaled nine-patch panels from a source surface."""

from __future__ import annotations

import pygame


def draw_nine_patch(
    target: pygame.Surface,
    source: pygame.Surface,
    rect: pygame.Rect,
    *,
    border: tuple[int, int, int, int],
) -> None:
    """border = left, top, right, bottom in source pixels."""
    if rect.width <= 0 or rect.height <= 0:
        return
    left, top, right, bottom = border
    sw, sh = source.get_size()
    center_w = max(1, sw - left - right)
    center_h = max(1, sh - top - bottom)

    # Corners
    if left > 0 and top > 0:
        target.blit(source.subsurface((0, 0, left, top)), (rect.x, rect.y))
    if right > 0 and top > 0:
        target.blit(
            source.subsurface((sw - right, 0, right, top)),
            (rect.right - right, rect.y),
        )
    if left > 0 and bottom > 0:
        target.blit(
            source.subsurface((0, sh - bottom, left, bottom)),
            (rect.x, rect.bottom - bottom),
        )
    if right > 0 and bottom > 0:
        target.blit(
            source.subsurface((sw - right, sh - bottom, right, bottom)),
            (rect.right - right, rect.bottom - bottom),
        )

    mid_w = max(1, rect.width - left - right)
    mid_h = max(1, rect.height - top - bottom)
    center_src = source.subsurface((left, top, center_w, center_h))

    # Top / bottom edges
    if mid_w > 0 and top > 0:
        top_edge = source.subsurface((left, 0, center_w, top))
        _tile_horizontal(target, top_edge, pygame.Rect(rect.x + left, rect.y, mid_w, top))
    if mid_w > 0 and bottom > 0:
        bot_edge = source.subsurface((left, sh - bottom, center_w, bottom))
        _tile_horizontal(
            target,
            bot_edge,
            pygame.Rect(rect.x + left, rect.bottom - bottom, mid_w, bottom),
        )
    # Left / right edges
    if mid_h > 0 and left > 0:
        left_edge = source.subsurface((0, top, left, center_h))
        _tile_vertical(target, left_edge, pygame.Rect(rect.x, rect.y + top, left, mid_h))
    if mid_h > 0 and right > 0:
        right_edge = source.subsurface((sw - right, top, right, center_h))
        _tile_vertical(
            target,
            right_edge,
            pygame.Rect(rect.right - right, rect.y + top, right, mid_h),
        )

    # Center
    if mid_w > 0 and mid_h > 0:
        scaled = pygame.transform.smoothscale(center_src, (mid_w, mid_h))
        target.blit(scaled, (rect.x + left, rect.y + top))


def _tile_horizontal(target: pygame.Surface, tile: pygame.Surface, rect: pygame.Rect) -> None:
    tw = tile.get_width()
    if tw <= 0:
        return
    x = rect.x
    while x < rect.right:
        w = min(tw, rect.right - x)
        if w == tw:
            target.blit(tile, (x, rect.y))
        else:
            target.blit(tile.subsurface((0, 0, w, rect.height)), (x, rect.y))
        x += tw


def _tile_vertical(target: pygame.Surface, tile: pygame.Surface, rect: pygame.Rect) -> None:
    th = tile.get_height()
    if th <= 0:
        return
    y = rect.y
    while y < rect.bottom:
        h = min(th, rect.bottom - y)
        if h == th:
            target.blit(tile, (rect.x, y))
        else:
            target.blit(tile.subsurface((0, 0, rect.width, h)), (rect.x, y))
        y += th
