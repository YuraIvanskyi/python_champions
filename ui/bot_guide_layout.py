"""Measure and draw scrollable bot-guide content blocks."""

from __future__ import annotations

from pathlib import Path

import pygame

from ui.bot_guide_content import GuideBlock
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font, code_font

_PARA_GAP = 8
_SECTION_GAP = 14
_CODE_PAD = 10
_CODE_LINE_GAP = 4
_BULLET_INDENT = 14
_MENTOR_GAP = 14
_MENTOR_MAX_WIDTH = 175
_MENTOR_FLOAT_START_BLOCK = 0
_MENTOR_FLOAT_END_BLOCK = 3
_MENTOR_BOTTOM_PAD = 6
_MENTOR_PATH = Path(__file__).resolve().parent / "assets" / "icons" / "mentor_3.png"
_MENTOR_CACHE: dict[tuple[int, int | None], pygame.Surface | None] = {}
_MENTOR_ASPECT = 601 / 599


def _mentor_surface(content_width: int, *, max_height: int | None = None) -> pygame.Surface | None:
    cache_key = (content_width, max_height)
    if cache_key in _MENTOR_CACHE:
        return _MENTOR_CACHE[cache_key]
    if not _MENTOR_PATH.is_file():
        _MENTOR_CACHE[cache_key] = None
        return None
    try:
        image = pygame.image.load(str(_MENTOR_PATH))
        if pygame.display.get_surface() is not None:
            image = image.convert_alpha()
        src_w, src_h = image.get_size()
        aspect = src_h / src_w if src_w else _MENTOR_ASPECT
        display_w = min(_MENTOR_MAX_WIDTH, max(110, int(content_width * 0.26)))
        display_h = max(1, int(display_w * aspect))
        if max_height is not None and display_h > max_height:
            display_h = max(1, max_height)
            display_w = max(1, int(display_h / aspect))
        scaled = pygame.transform.smoothscale(image, (display_w, display_h))
        _MENTOR_CACHE[cache_key] = scaled
        return scaled
    except pygame.error:
        _MENTOR_CACHE[cache_key] = None
        return None


def _mentor_layout(
    blocks: list[GuideBlock],
    *,
    content_width: int,
    start_y: int,
    body_font: pygame.font.Font,
    code_font: pygame.font.Font,
    heading_font: pygame.font.Font,
) -> tuple[pygame.Surface | None, pygame.Rect | None]:
    if len(blocks) <= _MENTOR_FLOAT_END_BLOCK:
        return None, None

    float_top = start_y
    provisional = _mentor_surface(content_width)
    if provisional is None:
        return None, None

    provisional_rect = pygame.Rect(
        content_width - provisional.get_width(),
        float_top,
        provisional.get_width(),
        provisional.get_height(),
    )
    intro_bottom = float_top
    for index in range(_MENTOR_FLOAT_START_BLOCK, _MENTOR_FLOAT_END_BLOCK + 1):
        if index > _MENTOR_FLOAT_START_BLOCK:
            intro_bottom += _gap_after(blocks[index - 1])
        intro_bottom += _block_height(
            blocks[index],
            content_width,
            body_font=body_font,
            code_font=code_font,
            heading_font=heading_font,
            block_start_y=intro_bottom - start_y,
            float_rect=provisional_rect,
        )

    max_height = max(80, intro_bottom - float_top - _MENTOR_BOTTOM_PAD)
    mentor = _mentor_surface(content_width, max_height=max_height)
    if mentor is None:
        return None, None

    float_rect = pygame.Rect(
        content_width - mentor.get_width(),
        float_top,
        mentor.get_width(),
        mentor.get_height(),
    )
    return mentor, float_rect


def _mentor_float_rect(
    blocks: list[GuideBlock],
    *,
    content_width: int,
    start_y: int,
    body_pt: int = 15,
    code_pt: int = 14,
    heading_pt: int = 17,
) -> pygame.Rect | None:
    _, float_rect = _mentor_layout(
        blocks,
        content_width=content_width,
        start_y=start_y,
        body_font=body_font(body_pt),
        code_font=code_font(code_pt),
        heading_font=body_font(heading_pt),
    )
    return float_rect


def measure_guide_content(
    blocks: list[GuideBlock],
    *,
    content_width: int,
    body_pt: int = 15,
    code_pt: int = 14,
    heading_pt: int = 17,
) -> int:
    """Return total pixel height of all blocks at the given width."""
    y = 0
    body_font_obj = body_font(body_pt)
    code_font_obj = code_font(code_pt)
    heading_font_obj = body_font(heading_pt)
    float_rect = _mentor_float_rect(
        blocks,
        content_width=content_width,
        start_y=0,
        body_pt=body_pt,
        code_pt=code_pt,
        heading_pt=heading_pt,
    )

    for index, block in enumerate(blocks):
        block_float = float_rect if _MENTOR_FLOAT_START_BLOCK <= index <= _MENTOR_FLOAT_END_BLOCK else None
        y += _block_height(
            block,
            content_width,
            block_start_y=y,
            body_font=body_font_obj,
            code_font=code_font_obj,
            heading_font=heading_font_obj,
            float_rect=block_float,
        )
        y += _gap_after(block)
    return y


def _gap_after(block: GuideBlock) -> int:
    if block.kind == "heading":
        return 4
    if block.kind == "code":
        return _SECTION_GAP
    return _PARA_GAP


def _block_height(
    block: GuideBlock,
    width: int,
    *,
    block_start_y: int,
    body_font: pygame.font.Font,
    code_font: pygame.font.Font,
    heading_font: pygame.font.Font,
    float_rect: pygame.Rect | None = None,
) -> int:
    if block.kind == "heading":
        line_h = heading_font.get_height() + 2
        width_at = _width_at(width, float_rect, line_h)
        lines = _wrap_text(
            block.text,
            heading_font,
            start_y=block_start_y,
            line_h=line_h,
            width_at=width_at,
        )
        return len(lines) * line_h

    if block.kind == "bullet":
        line_h = body_font.get_height() + 2
        width_at = _width_at(width, float_rect, line_h, margin=_BULLET_INDENT)
        lines = _wrap_text(
            f"• {block.text}",
            body_font,
            start_y=block_start_y,
            line_h=line_h,
            width_at=width_at,
        )
        return len(lines) * line_h

    if block.kind == "paragraph":
        line_h = body_font.get_height() + 2
        width_at = _width_at(width, float_rect, line_h)
        lines = _wrap_text(
            block.text,
            body_font,
            start_y=block_start_y,
            line_h=line_h,
            width_at=width_at,
        )
        return len(lines) * line_h

    if block.kind == "code":
        line_h = code_font.get_height() + _CODE_LINE_GAP
        inner_h = len(block.lines) * line_h
        return inner_h + _CODE_PAD * 2

    return 0


def draw_guide_content(
    surface: pygame.Surface,
    rect: pygame.Rect,
    blocks: list[GuideBlock],
    scroll_offset: int,
    *,
    body_pt: int = 15,
    code_pt: int = 14,
    heading_pt: int = 17,
) -> None:
    body_font_obj = body_font(body_pt)
    code_font_obj = code_font(code_pt)
    heading_font_obj = body_font(heading_pt)

    clip = surface.get_clip()
    surface.set_clip(rect)
    x = rect.x
    screen_y = rect.y - scroll_offset
    content_y = 0
    inner_w = rect.width
    mentor, float_rect = _mentor_layout(
        blocks,
        content_width=inner_w,
        start_y=0,
        body_font=body_font_obj,
        code_font=code_font_obj,
        heading_font=heading_font_obj,
    )
    if mentor is not None and float_rect is not None:
        draw_rect = pygame.Rect(
            x + float_rect.x,
            screen_y + float_rect.y,
            float_rect.width,
            float_rect.height,
        )
        if draw_rect.colliderect(rect):
            surface.blit(mentor, draw_rect.topleft)

    for index, block in enumerate(blocks):
        block_float = float_rect if _MENTOR_FLOAT_START_BLOCK <= index <= _MENTOR_FLOAT_END_BLOCK else None
        block_h = _block_height(
            block,
            inner_w,
            block_start_y=content_y,
            body_font=body_font_obj,
            code_font=code_font_obj,
            heading_font=heading_font_obj,
            float_rect=block_float,
        )
        block_rect = pygame.Rect(x, screen_y + content_y, inner_w, block_h)

        if block_rect.bottom >= rect.top and block_rect.top <= rect.bottom:
            _draw_block(
                surface,
                block,
                x,
                screen_y + content_y,
                inner_w,
                block_start_y=content_y,
                body_font=body_font_obj,
                code_font=code_font_obj,
                heading_font=heading_font_obj,
                float_rect=block_float,
            )

        content_y += block_h + _gap_after(block)

    surface.set_clip(clip)


def _draw_block(
    surface: pygame.Surface,
    block: GuideBlock,
    x: int,
    y: int,
    width: int,
    *,
    block_start_y: int,
    body_font: pygame.font.Font,
    code_font: pygame.font.Font,
    heading_font: pygame.font.Font,
    float_rect: pygame.Rect | None = None,
) -> None:
    if block.kind == "heading":
        line_h = heading_font.get_height() + 2
        width_at = _width_at(width, float_rect, line_h)
        lines = _wrap_text(
            block.text,
            heading_font,
            start_y=block_start_y,
            line_h=line_h,
            width_at=width_at,
        )
        cy = y
        for line in lines:
            ls = heading_font.render(line, True, colors.GOLD_TEXT)
            surface.blit(ls, (x, cy))
            cy += line_h
        return

    if block.kind == "bullet":
        line_h = body_font.get_height() + 2
        width_at = _width_at(width, float_rect, line_h, margin=_BULLET_INDENT)
        lines = _wrap_text(
            f"• {block.text}",
            body_font,
            start_y=block_start_y,
            line_h=line_h,
            width_at=width_at,
        )
        cy = y
        for line in lines:
            ls = body_font.render(line, True, colors.TEXT_BODY)
            surface.blit(ls, (x + _BULLET_INDENT, cy))
            cy += line_h
        return

    if block.kind == "paragraph":
        line_h = body_font.get_height() + 2
        width_at = _width_at(width, float_rect, line_h)
        lines = _wrap_text(
            block.text,
            body_font,
            start_y=block_start_y,
            line_h=line_h,
            width_at=width_at,
        )
        cy = y
        for line in lines:
            ls = body_font.render(line, True, colors.TEXT_BODY)
            surface.blit(ls, (x, cy))
            cy += line_h
        return

    if block.kind == "code":
        line_h = code_font.get_height() + _CODE_LINE_GAP
        box_h = len(block.lines) * line_h + _CODE_PAD * 2
        box = pygame.Rect(x, y, width, box_h)
        pygame.draw.rect(surface, colors.SLATE_DARK, box, border_radius=4)
        pygame.draw.rect(surface, colors.STONE_BORDER, box, 1, border_radius=4)
        cy = y + _CODE_PAD
        for line in block.lines:
            if line:
                ls = code_font.render(line, True, colors.GREEN_OK)
            else:
                ls = code_font.render(" ", True, colors.GREEN_OK)
            surface.blit(ls, (x + _CODE_PAD, cy))
            cy += line_h
        return


def draw_guide_scrollbar(
    surface: pygame.Surface,
    track: pygame.Rect,
    *,
    content_height: int,
    viewport_height: int,
    offset: int,
) -> None:
    skin.draw_scrollbar(
        surface,
        track,
        content_height=content_height,
        viewport_height=viewport_height,
        offset=offset,
    )


def _width_at(
    content_width: int,
    float_rect: pygame.Rect | None,
    line_h: int,
    *,
    margin: int = 0,
):
    def width_for_line(y_pos: int) -> int:
        available = content_width - margin
        if float_rect is None:
            return available
        line_bottom = y_pos + line_h
        if y_pos < float_rect.bottom and line_bottom > float_rect.top:
            return max(40, content_width - float_rect.width - _MENTOR_GAP - margin)
        return available

    return width_for_line


def _wrap_text(
    text: str,
    font: pygame.font.Font,
    *,
    start_y: int,
    line_h: int,
    width_at,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = ""
    line_y = start_y

    for word in words:
        max_w = width_at(line_y)
        trial = f"{current} {word}".strip() if current else word
        if font.size(trial)[0] <= max_w:
            current = trial
            continue
        if current:
            lines.append(current)
            line_y += line_h
            current = word
            continue
        current = word
    if current:
        lines.append(current)
    return lines or [text]
