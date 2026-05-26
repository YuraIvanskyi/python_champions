"""Measure and draw scrollable bot-guide content blocks."""

from __future__ import annotations

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

    for block in blocks:
        y += _block_height(
            block,
            content_width,
            body_font=body_font_obj,
            code_font=code_font_obj,
            heading_font=heading_font_obj,
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
    body_font: pygame.font.Font,
    code_font: pygame.font.Font,
    heading_font: pygame.font.Font,
) -> int:
    if block.kind == "heading":
        return heading_font.get_height() + 2

    if block.kind == "bullet":
        lines = _wrap_text(f"• {block.text}", body_font, width - _BULLET_INDENT)
        return len(lines) * (body_font.get_height() + 2)

    if block.kind == "paragraph":
        lines = _wrap_text(block.text, body_font, width)
        return len(lines) * (body_font.get_height() + 2)

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
    y = rect.y - scroll_offset
    inner_w = rect.width

    for block in blocks:
        block_h = _block_height(
            block,
            inner_w,
            body_font=body_font_obj,
            code_font=code_font_obj,
            heading_font=heading_font_obj,
        )
        block_rect = pygame.Rect(x, y, inner_w, block_h)

        if block_rect.bottom >= rect.top and block_rect.top <= rect.bottom:
            _draw_block(
                surface,
                block,
                x,
                y,
                inner_w,
                body_font=body_font_obj,
                code_font=code_font_obj,
                heading_font=heading_font_obj,
            )

        y += block_h + _gap_after(block)

    surface.set_clip(clip)


def _draw_block(
    surface: pygame.Surface,
    block: GuideBlock,
    x: int,
    y: int,
    width: int,
    *,
    body_font: pygame.font.Font,
    code_font: pygame.font.Font,
    heading_font: pygame.font.Font,
) -> None:
    if block.kind == "heading":
        surf = heading_font.render(block.text, True, colors.GOLD_TEXT)
        surface.blit(surf, (x, y))
        return

    if block.kind == "bullet":
        lines = _wrap_text(f"• {block.text}", body_font, width - _BULLET_INDENT)
        cy = y
        for line in lines:
            ls = body_font.render(line, True, colors.TEXT_BODY)
            surface.blit(ls, (x + _BULLET_INDENT, cy))
            cy += body_font.get_height() + 2
        return

    if block.kind == "paragraph":
        lines = _wrap_text(block.text, body_font, width)
        cy = y
        for line in lines:
            ls = body_font.render(line, True, colors.TEXT_BODY)
            surface.blit(ls, (x, cy))
            cy += body_font.get_height() + 2
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


def _wrap_text(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip() if current else word
        if font.size(trial)[0] <= max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]
