"""Heads-up display for simulation and replay."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygame

from engine.core.turn_result import TurnResult
from engine.i18n import translate
from ui.render.icons import load_icon
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font, title_font
from ui.theme import HUD_BODY_PT, HUD_TEXT_HEIGHT, HUD_TITLE_PT
from ui.widgets.scroll import ScrollState

_HUD_PAD_X = 16
_HUD_PAD_Y = 6
_HUD_HEADER_GAP = 4
_HUD_CARDS_GAP = 4
_HUD_FOOTER_GAP = 2
_HUD_MENTOR_GAP = 12
_HUD_SCROLLBAR_H = 6
_HUD_SCROLLBAR_GAP = 2

_BOT_NAME_MAX = 25
_BOT_ICON_SIZE = 18
_BOT_CARD_GAP = 6
_BOT_CARD_PAD_X = 6
_BOT_CARD_PAD_Y = 5
_BOT_CARD_MIN_W = 72
_BOT_NAME_PT = 13
_BOT_SCORE_PT = 13
_BOT_ACTION_PT = 12
_BOT_LINE_GAP = 2
_BOT_ACTION_COLOR = (58, 44, 26)

_MENTOR_PATH = Path(__file__).resolve().parents[1] / "assets" / "icons" / "mentor_1.png"
_MENTOR_CACHE: dict[int, pygame.Surface | None] = {}


@dataclass(frozen=True)
class HudBotEntry:
    name: str
    icon_path: str | None
    score_line: str
    action_line: str


def build_hud_bot_entries(
    render_state: dict[str, Any],
    last_turn: TurnResult | None,
    *,
    lang: str = "en",
) -> list[HudBotEntry]:
    """Build per-bot HUD cards from render state and the latest turn."""
    entities = render_state.get("entities", ())
    scores = render_state.get("scores", {})
    names = render_state.get("display_names", {})

    actions: dict[str, str] = {}
    if last_turn is not None:
        for pid, action in last_turn.actions.items():
            actions[pid] = action.value

    order = [str(entity["id"]) for entity in entities]
    if not order:
        order = sorted(scores.keys())

    entries: list[HudBotEntry] = []
    for pid in order:
        entity = next((item for item in entities if str(item["id"]) == pid), {})
        name = str(entity.get("display_name") or names.get(pid, pid))
        icon = entity.get("icon")
        score = scores.get(pid, 0)
        action = actions.get(pid, "")
        entries.append(
            HudBotEntry(
                name=name,
                icon_path=str(icon) if icon else None,
                score_line=translate("sim.bot_score", lang=lang, score=score),
                action_line=action or translate("sim.bot_no_action", lang=lang),
            )
        )
    return entries


def hud_header_line(
    *,
    title: str,
    seed: int,
    turn: int | None = None,
    turn_label: str | None = None,
    lang: str = "en",
) -> str:
    seed_text = translate("sim.seed", lang=lang, seed=seed)
    parts = [title, seed_text]
    if turn_label:
        parts.append(turn_label)
    elif turn is not None:
        parts.append(translate("sim.turn_only", lang=lang, turn=turn))
    return "  ·  ".join(parts)


def _mentor_surface(max_height: int) -> pygame.Surface | None:
    if max_height in _MENTOR_CACHE:
        return _MENTOR_CACHE[max_height]
    if not _MENTOR_PATH.is_file():
        _MENTOR_CACHE[max_height] = None
        return None
    try:
        image = pygame.image.load(str(_MENTOR_PATH))
        if pygame.display.get_surface() is not None:
            image = image.convert_alpha()
        src_w, src_h = image.get_size()
        if src_h <= 0:
            _MENTOR_CACHE[max_height] = None
            return None
        display_h = min(max_height, src_h)
        display_w = max(1, int(display_h * src_w / src_h))
        scaled = pygame.transform.smoothscale(image, (display_w, display_h))
        _MENTOR_CACHE[max_height] = scaled
        return scaled
    except pygame.error:
        _MENTOR_CACHE[max_height] = None
        return None


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
            continue
        if current:
            lines.append(current)
            current = word
            continue
        current = word
    if current:
        lines.append(current)
    return lines or [text]


def _hud_text_column(panel: pygame.Rect) -> tuple[int, int, pygame.Surface | None]:
    inner_h = max(1, panel.height - _HUD_PAD_Y * 2)
    mentor = _mentor_surface(inner_h)
    if mentor is None:
        return _HUD_PAD_X, panel.width - _HUD_PAD_X * 2, None
    text_x = _HUD_PAD_X + mentor.get_width() + _HUD_MENTOR_GAP
    text_w = max(80, panel.width - text_x - _HUD_PAD_X)
    return text_x, text_w, mentor


def _truncate_name(name: str, *, max_len: int = _BOT_NAME_MAX) -> str:
    if len(name) <= max_len:
        return name
    if max_len <= 1:
        return name[:max_len]
    return name[: max_len - 1] + "…"


def _bot_card_width(
    entry: HudBotEntry,
    *,
    name_font: pygame.font.Font,
    score_font: pygame.font.Font,
    action_font: pygame.font.Font,
) -> int:
    label = _truncate_name(entry.name)
    name_row_w = _BOT_ICON_SIZE + 4 + name_font.size(label)[0]
    score_w = score_font.size(entry.score_line)[0]
    action_w = action_font.size(entry.action_line)[0]
    inner_w = max(name_row_w, score_w, action_w)
    return max(_BOT_CARD_MIN_W, inner_w + _BOT_CARD_PAD_X * 2)


def _draw_wrapped_in_rect(
    surface: pygame.Surface,
    text: str,
    rect: pygame.Rect,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    *,
    line_h: int,
) -> None:
    y = rect.y
    for line in _wrap_text(text, font, rect.width):
        if y + line_h > rect.bottom:
            break
        skin.draw_text_clipped(
            surface,
            line,
            pygame.Rect(rect.x, y, rect.width, line_h),
            font,
            color,
            align="left",
        )
        y += line_h


def _draw_bot_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    entry: HudBotEntry,
) -> None:
    skin.draw_panel(surface, rect, style="parchment")

    name_font = body_font(_BOT_NAME_PT)
    score_font = body_font(_BOT_SCORE_PT)
    action_font = body_font(_BOT_ACTION_PT)
    name_line_h = _BOT_NAME_PT + 2
    score_line_h = _BOT_SCORE_PT + 2
    action_line_h = _BOT_ACTION_PT + 2

    inner = rect.inflate(-_BOT_CARD_PAD_X * 2, -_BOT_CARD_PAD_Y * 2)
    x = inner.x
    y = inner.y

    icon = load_icon(entry.icon_path, size=_BOT_ICON_SIZE)
    if icon is not None:
        icon_y = y + max(0, (name_line_h - icon.get_height()) // 2)
        surface.blit(icon, (x, icon_y))
        name_x = x + _BOT_ICON_SIZE + 4
        name_w = max(1, inner.right - name_x)
    else:
        name_x = x
        name_w = inner.width

    skin.draw_text_clipped(
        surface,
        _truncate_name(entry.name),
        pygame.Rect(name_x, y, name_w, name_line_h),
        name_font,
        colors.PARCHMENT_TEXT,
        align="left",
    )

    y += max(_BOT_ICON_SIZE, name_line_h) + _BOT_LINE_GAP
    skin.draw_text_clipped(
        surface,
        entry.score_line,
        pygame.Rect(inner.x, y, inner.width, score_line_h),
        score_font,
        colors.PARCHMENT_TEXT,
        align="left",
    )
    y += score_line_h + _BOT_LINE_GAP
    action_rect = pygame.Rect(inner.x, y, inner.width, max(0, inner.bottom - y))
    _draw_wrapped_in_rect(
        surface,
        entry.action_line,
        action_rect,
        action_font,
        _BOT_ACTION_COLOR,
        line_h=action_line_h,
    )


def _draw_horizontal_scrollbar(
    surface: pygame.Surface,
    track_rect: pygame.Rect,
    *,
    content_width: int,
    viewport_width: int,
    offset: int,
) -> None:
    if content_width <= viewport_width or track_rect.width <= 0:
        return

    track_surf = pygame.Surface((track_rect.width, track_rect.height), pygame.SRCALPHA)
    track_surf.fill((*colors.STONE_SHADOW, 160))
    pygame.draw.rect(track_surf, (*colors.STONE_BORDER, 180), track_surf.get_rect(), 1, border_radius=3)
    surface.blit(track_surf, track_rect.topleft)

    ratio = max(0.0, min(1.0, viewport_width / content_width))
    thumb_w = max(18, int(track_rect.width * ratio))
    scroll_ratio = offset / max(1, content_width - viewport_width)
    thumb_x = track_rect.x + int((track_rect.width - thumb_w) * scroll_ratio)
    thumb = pygame.Rect(thumb_x, track_rect.y + 1, thumb_w, track_rect.height - 2)
    pygame.draw.rect(surface, colors.TEXT_MUTED, thumb, border_radius=3)
    pygame.draw.rect(surface, colors.GOLD_TEXT, thumb, 1, border_radius=3)


def _draw_wrapped_entry(
    surface: pygame.Surface,
    *,
    text: str,
    rect_x: int,
    rect_w: int,
    y: int,
    line_h: int,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    panel_bottom: int,
) -> int:
    for line in _wrap_text(text, font, rect_w):
        if y + line_h > panel_bottom - _HUD_PAD_Y:
            return y
        skin.draw_text_clipped(
            surface,
            line,
            pygame.Rect(rect_x, y, rect_w, line_h),
            font,
            color,
            align="left",
        )
        y += line_h
    return y


def draw_hud(
    surface: pygame.Surface,
    *,
    header: str,
    bots: list[HudBotEntry],
    footer_lines: list[str] | None = None,
    scroll: ScrollState | None = None,
    y_offset: int | None = None,
    content_height: int | None = None,
) -> pygame.Rect:
    """Draw the wood HUD panel. Returns the bot-cards viewport for wheel scrolling."""
    height = content_height if content_height is not None else HUD_TEXT_HEIGHT
    panel_top = y_offset if y_offset is not None else surface.get_height() - height
    panel = pygame.Rect(0, panel_top, surface.get_width(), height)
    skin.draw_panel(surface, panel, style="wood")
    pygame.draw.line(
        surface, (180, 148, 72),
        (0, panel_top), (surface.get_width(), panel_top), 2,
    )

    title_font_obj = title_font(HUD_TITLE_PT)
    body_font_obj = body_font(HUD_BODY_PT)
    name_font_obj = body_font(_BOT_NAME_PT)
    score_font_obj = body_font(_BOT_SCORE_PT)
    action_font_obj = body_font(_BOT_ACTION_PT)
    text_x, text_w, mentor = _hud_text_column(panel)

    footer_lines = [line for line in (footer_lines or []) if line]
    footer_line_h = HUD_BODY_PT + 2
    footer_block_h = (
        len(footer_lines) * footer_line_h
        + max(0, len(footer_lines) - 1) * _HUD_FOOTER_GAP
        if footer_lines
        else 0
    )

    header_h = HUD_TITLE_PT + 4
    cards_top = panel_top + _HUD_PAD_Y + header_h + _HUD_HEADER_GAP
    cards_bottom_limit = panel.bottom - _HUD_PAD_Y - footer_block_h
    if footer_block_h:
        cards_bottom_limit -= _HUD_FOOTER_GAP

    total_cards_w = 0
    if bots:
        total_cards_w = sum(
            _bot_card_width(
                bot,
                name_font=name_font_obj,
                score_font=score_font_obj,
                action_font=action_font_obj,
            )
            for bot in bots
        )
        total_cards_w += _BOT_CARD_GAP * max(0, len(bots) - 1)

    scroll_state = scroll if scroll is not None else ScrollState()
    scroll_state.set_content(total_cards_w, text_w)
    scrollbar_space = (
        _HUD_SCROLLBAR_H + _HUD_SCROLLBAR_GAP if scroll_state.max_offset > 0 else 0
    )
    cards_viewport_h = max(1, cards_bottom_limit - cards_top - scrollbar_space)
    cards_viewport = pygame.Rect(text_x, cards_top, text_w, cards_viewport_h)

    old_clip = surface.get_clip()
    surface.set_clip(panel)

    if mentor is not None:
        inner_h = panel.height - _HUD_PAD_Y * 2
        mentor_y = panel_top + _HUD_PAD_Y + (inner_h - mentor.get_height()) // 2
        surface.blit(mentor, (_HUD_PAD_X, mentor_y))

    y = panel_top + _HUD_PAD_Y
    y = _draw_wrapped_entry(
        surface,
        text=header,
        rect_x=text_x,
        rect_w=text_w,
        y=y,
        line_h=header_h,
        font=title_font_obj,
        color=colors.GOLD_TEXT,
        panel_bottom=panel.bottom,
    )
    y += _HUD_HEADER_GAP

    cards_clip = cards_viewport.copy()
    surface.set_clip(cards_clip)
    card_x = cards_viewport.x - scroll_state.offset
    card_y = cards_viewport.y
    card_h = cards_viewport.height
    for entry in bots:
        card_w = _bot_card_width(
            entry,
            name_font=name_font_obj,
            score_font=score_font_obj,
            action_font=action_font_obj,
        )
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        if card_rect.right >= cards_viewport.left and card_rect.left <= cards_viewport.right:
            _draw_bot_card(surface, card_rect, entry)
        card_x += card_w + _BOT_CARD_GAP
    surface.set_clip(panel)

    if scroll_state.max_offset > 0:
        track = pygame.Rect(
            cards_viewport.x,
            cards_viewport.bottom + _HUD_SCROLLBAR_GAP,
            cards_viewport.width,
            _HUD_SCROLLBAR_H,
        )
        _draw_horizontal_scrollbar(
            surface,
            track,
            content_width=scroll_state.content_height,
            viewport_width=scroll_state.viewport_height,
            offset=scroll_state.offset,
        )

    if footer_lines:
        y = panel.bottom - _HUD_PAD_Y - footer_block_h
        for line in footer_lines[:3]:
            y = _draw_wrapped_entry(
                surface,
                text=line,
                rect_x=text_x,
                rect_w=text_w,
                y=y,
                line_h=footer_line_h,
                font=body_font_obj,
                color=colors.TEXT_BODY,
                panel_bottom=panel.bottom,
            )
            y += _HUD_FOOTER_GAP

    surface.set_clip(old_clip)
    return cards_viewport


def draw_toolbar_strip(surface: pygame.Surface, *, y: int, height: int) -> None:
    skin.draw_toolbar_strip(surface, y=y, height=height)


def draw_centered_text(
    surface: pygame.Surface,
    lines: list[str],
    *,
    y_start: int = 80,
    color: tuple[int, int, int] = colors.TEXT_BODY,
    size: int | None = None,
) -> None:
    pt = size if size is not None else HUD_BODY_PT + 4
    font = body_font(pt)
    sw = surface.get_width()
    y = y_start
    for line in lines:
        text = font.render(line, True, color)
        x = (sw - text.get_width()) // 2
        clip = pygame.Rect(16, y, sw - 32, pt + 8)
        old_clip = surface.get_clip()
        surface.set_clip(clip)
        surface.blit(text, (x, y))
        surface.set_clip(old_clip)
        y += pt + 12
