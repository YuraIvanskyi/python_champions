"""vLLM setup component — embedded in the Coach screen's AI Summary tab.

Shown when enable_ai = true but the vLLM health probe returns False.
Provides Retry and Use-Templates-Only buttons.
"""

from __future__ import annotations

from typing import Callable

import pygame

from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font, code_font
from ui.widgets import Button, WidgetGroup

_SETUP_COMMANDS = [
    "# Install Ollama from https://ollama.com",
    "ollama pull qwen2.5:1.5b",
    "ollama serve",
]


class VllmSetupPanel:
    """Embedded panel drawn inside the Coach screen's AI Summary region.

    *on_retry* is called when the user presses "Retry Connection".
    *on_use_templates* is called when the user presses "Use Templates Only".
    """

    def __init__(
        self,
        *,
        on_retry: Callable[[], None],
        on_use_templates: Callable[[], None],
    ) -> None:
        self._retry_btn = Button(
            pygame.Rect(0, 0, 180, 38),
            "Retry Connection",
            on_click=on_retry,
        )
        self._templates_btn = Button(
            pygame.Rect(0, 0, 200, 38),
            "Use Templates Only",
            on_click=on_use_templates,
        )
        self._widgets = WidgetGroup([self._retry_btn, self._templates_btn])

    # ── Event / draw ──────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        return bool(self._widgets.handle_event(event))

    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        skin.draw_panel(surface, rect, style="stone")

        x = rect.x + 24
        y = rect.y + 20

        title_font = body_font(20)
        label_font = body_font(15)
        cmd_font = code_font(14)

        # Title
        title_surf = title_font.render("⚗ AI Summary", True, colors.GOLD_TEXT)
        surface.blit(title_surf, (x, y))
        y += title_surf.get_height() + 12

        # Status message
        _blit_text(surface, label_font, "vLLM is not running.", x, y, colors.TEXT_BODY)
        y += label_font.get_height() + 4
        _blit_text(
            surface,
            label_font,
            "Enable AI feedback by starting the server:",
            x,
            y,
            colors.TEXT_MUTED,
        )
        y += label_font.get_height() + 12

        # Command box
        cmd_lines = _SETUP_COMMANDS
        cmd_box_h = len(cmd_lines) * (cmd_font.get_height() + 4) + 16
        cmd_box_w = rect.width - 48
        cmd_box = pygame.Rect(x, y, cmd_box_w, cmd_box_h)
        pygame.draw.rect(surface, colors.SLATE_DARK, cmd_box, border_radius=4)
        pygame.draw.rect(surface, colors.STONE_BORDER, cmd_box, 1, border_radius=4)
        cy = y + 8
        for line in cmd_lines:
            cmd_surf = cmd_font.render(line, True, colors.GREEN_OK)
            surface.blit(cmd_surf, (x + 8, cy))
            cy += cmd_font.get_height() + 4
        y += cmd_box_h + 16

        # Hint
        _blit_text(
            surface,
            label_font,
            "Then set  enable_ai = true  in configs/default.toml",
            x,
            y,
            colors.TEXT_MUTED,
        )
        y += label_font.get_height() + 4
        _blit_text(
            surface,
            label_font,
            "and rerun the simulation.  (vLLM is Linux-only; use Ollama on Windows)",
            x,
            y,
            colors.TEXT_MUTED,
        )
        y += label_font.get_height() + 24

        # Buttons
        self._retry_btn.rect = pygame.Rect(x, y, 180, 38)
        self._templates_btn.rect = pygame.Rect(x + 196, y, 200, 38)
        self._widgets.draw(surface)


# ── Template-feedback panel ───────────────────────────────────────────────────


class TemplateFeedbackPanel:
    """Shows template feedback strings directly when AI is offline."""

    def draw(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        feedback: list[str],
    ) -> None:
        skin.draw_panel(surface, rect, style="parchment")

        x = rect.x + 20
        y = rect.y + 16

        label_font = body_font(15)
        item_font = body_font(14)

        header = label_font.render("Template feedback (AI offline)", True, colors.PARCHMENT_TEXT)
        surface.blit(header, (x, y))
        y += header.get_height() + 12

        old_clip = surface.get_clip()
        surface.set_clip(rect.inflate(-8, -8))

        if not feedback:
            none_surf = item_font.render("No feedback items.", True, colors.PARCHMENT_TEXT)
            surface.blit(none_surf, (x, y))
        else:
            max_w = rect.width - 40
            for item in feedback:
                lines = _wrap(item_font, f"• {item}", max_w)
                for line in lines:
                    if y + item_font.get_height() > rect.bottom - 8:
                        break
                    surf = item_font.render(line, True, colors.PARCHMENT_TEXT)
                    surface.blit(surf, (x, y))
                    y += item_font.get_height() + 3

        surface.set_clip(old_clip)


# ── AI report display panel ───────────────────────────────────────────────────

import re as _re

# Line style tokens
_STYLE_ADVISORY = "advisory"   # > blockquote
_STYLE_PLAYER   = "player"     # ## Player: …  (multi-bot separator)
_STYLE_HEADING  = "heading"    # ### / ## / # / **Section:**
_STYLE_NUMBERED = "numbered"   # 1. 2. 3.
_STYLE_BULLET   = "bullet"     # - / • / · item
_STYLE_MUTED    = "muted"      # _italic_ unavailable message
_STYLE_BODY     = "body"       # normal paragraph
_STYLE_SPACER   = "spacer"     # blank line
_STYLE_CODE     = "code"       # line inside a fenced ``` block


def _strip_inline(text: str) -> str:
    """Remove **bold**, *italic*, and `code` markers from inline text."""
    text = _re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = _re.sub(r"\*(.+?)\*",     r"\1", text)
    text = _re.sub(r"`([^`]+)`",     r"\1", text)
    return text.strip()


def _preprocess(report_text: str) -> list[tuple[str, str]]:
    """Split report into (raw_kind, text) pairs, expanding fenced code blocks.

    Lines inside ``` … ``` fences get kind="code"; everything else stays as the
    raw line so _classify can handle it normally.
    """
    result: list[tuple[str, str]] = []
    in_fence = False
    for line in report_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            if in_fence:
                # fence-open — emit a small spacer before the block
                result.append(("spacer_pre_code", ""))
            else:
                # fence-close — emit a small spacer after the block
                result.append(("spacer_post_code", ""))
            continue
        if in_fence:
            result.append(("code", line))   # preserve indentation inside block
        else:
            result.append(("normal", line))
    return result


def _classify(raw: str) -> tuple[str, str]:
    """Return (style, display_text) for one raw non-code markdown line."""
    s = raw.strip()

    if not s:
        return _STYLE_SPACER, ""

    # Blockquote  > ⚠️ …
    if s.startswith("> "):
        return _STYLE_ADVISORY, _strip_inline(s[2:])
    if s == ">":
        return _STYLE_SPACER, ""

    # Any number of leading # → heading
    m = _re.match(r"^(#{1,6})\s+(.*)", s)
    if m:
        hashes = m.group(1)
        text   = _strip_inline(m.group(2))
        if len(hashes) == 2 and text.lower().startswith("player"):
            return _STYLE_PLAYER, text
        return _STYLE_HEADING, text

    # Italic-wrapped unavailable notice  _…_
    if s.startswith("_") and s.endswith("_") and len(s) > 2:
        return _STYLE_MUTED, s[1:-1]

    # Bold-only line → heading
    if s.startswith("**") and s.count("**") >= 2:
        rest = _re.sub(r"\*\*", "", s).strip().rstrip(":")
        if len(rest.split()) <= 6:
            return _STYLE_HEADING, rest

    # Numbered list  1. …  or  1) …
    if _re.match(r"^\d+[.)]\s", s):
        num_end = s.index(" ")
        rest = _strip_inline(s[num_end:].strip())
        num  = s[:num_end].rstrip(".)") + "."
        return _STYLE_NUMBERED, f"{num} {rest}"

    # Bullet  - / • / · / * (possibly indented)
    if _re.match(r"^[-•·*]\s", s):
        return _STYLE_BULLET, _strip_inline(s[2:])

    return _STYLE_BODY, _strip_inline(s)


# ── Row type for the render list ──────────────────────────────────────────────

_Row = tuple[str, str, "pygame.font.Font", tuple, int, int]
# (style, text, font, color, x_indent, gap_after_px)

_SCROLLBAR_W   = 8
_SCROLLBAR_PAD = 4

# Code block visual constants
_CODE_BG    = (30, 32, 42)   # dark slate
_CODE_FG    = (140, 220, 140)  # soft green — readable on dark bg
_CODE_PAD_X = 10
_CODE_PAD_Y = 5


class AiReportPanel:
    """Markdown-aware renderer for ai_report.md with code blocks and scrollbar."""

    def __init__(self) -> None:
        self._scroll_offset = 0
        self._total_h = 0

    def reset(self) -> None:
        self._scroll_offset = 0
        self._total_h = 0

    def handle_wheel(self, event: pygame.event.Event, rect: pygame.Rect) -> bool:
        if event.type == pygame.MOUSEWHEEL and rect.collidepoint(pygame.mouse.get_pos()):
            max_scroll = max(0, self._total_h - rect.height + 28)
            self._scroll_offset = max(0, min(max_scroll, self._scroll_offset - event.y * 22))
            return True
        return False

    def draw(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        report_text: str,
    ) -> None:
        from ui.skin.typography import code_font as _code_font

        skin.draw_panel(surface, rect, style="parchment")

        _C     = colors
        sb_w   = _SCROLLBAR_W + _SCROLLBAR_PAD * 2
        pad_x  = rect.x + 20
        max_w  = rect.width - 40 - sb_w
        inner  = rect.inflate(-4, -4)
        vis_h  = inner.height

        f_head   = body_font(16)
        f_player = body_font(15)
        f_body   = body_font(14)
        f_small  = body_font(13)
        f_code   = _code_font(13)

        style_cfg: dict[str, tuple] = {
            _STYLE_ADVISORY: (f_small, _C.TEXT_MUTED,       0,   6),
            _STYLE_PLAYER:   (f_player, _C.WOOD_BORDER,     0,  10),
            _STYLE_HEADING:  (f_head,  _C.WOOD_FILL,        0,   8),
            _STYLE_NUMBERED: (f_body,  _C.PARCHMENT_TEXT,  18,   5),
            _STYLE_BULLET:   (f_body,  _C.PARCHMENT_TEXT,  22,   4),
            _STYLE_MUTED:    (f_small, _C.TEXT_MUTED,       0,   4),
            _STYLE_BODY:     (f_body,  _C.PARCHMENT_TEXT,   0,   4),
            _STYLE_SPACER:   (f_small, _C.PARCHMENT_TEXT,   0,   8),
            _STYLE_CODE:     (f_code,  _CODE_FG,            _CODE_PAD_X, 0),
        }

        # ── Build flat render rows ────────────────────────────────────────────
        rows: list[_Row] = []
        segments = _preprocess(report_text)

        # Collect consecutive code lines so we can compute the bg box height
        # We emit them together, but render as individual rows tagged _STYLE_CODE
        i = 0
        while i < len(segments):
            kind, text = segments[i]

            if kind == "spacer_pre_code":
                rows.append((_STYLE_SPACER, "", f_small, _C.PARCHMENT_TEXT, 0, 4))
                i += 1
                continue

            if kind == "spacer_post_code":
                rows.append((_STYLE_SPACER, "", f_small, _C.PARCHMENT_TEXT, 0, 8))
                i += 1
                continue

            if kind == "code":
                rows.append((_STYLE_CODE, text, f_code, _CODE_FG, _CODE_PAD_X, 2))
                i += 1
                continue

            # Normal markdown line
            style, display = _classify(text)
            if style == _STYLE_SPACER:
                rows.append((_STYLE_SPACER, "", f_small, _C.PARCHMENT_TEXT, 0, 8))
                i += 1
                continue

            font, color, indent, gap = style_cfg[style]
            prefix  = "• " if style == _STYLE_BULLET else ""
            wrapped = _wrap(font, prefix + display, max_w - indent)
            for j, line in enumerate(wrapped):
                g = gap if j == len(wrapped) - 1 else 2
                rows.append((style, line, font, color, indent, g))
            i += 1

        # ── Measure total content height ──────────────────────────────────────
        # Code rows share one background box per contiguous group; account for
        # top+bottom padding of that box.
        def _total_height(rows: list[_Row]) -> int:
            h = 14  # top padding
            prev_code = False
            for style, _, font, _, _, gap in rows:
                if style == _STYLE_CODE and not prev_code:
                    h += _CODE_PAD_Y        # box top padding (first row of block)
                h += font.get_height() + gap
                if style == _STYLE_CODE:
                    prev_code = True
                else:
                    if prev_code:
                        h += _CODE_PAD_Y    # box bottom padding (end of block)
                    prev_code = False
            if prev_code:
                h += _CODE_PAD_Y
            return h

        total_h = _total_height(rows)
        self._total_h = total_h
        max_scroll = max(0, total_h - vis_h)
        self._scroll_offset = min(self._scroll_offset, max_scroll)

        # ── Draw ─────────────────────────────────────────────────────────────
        old_clip = surface.get_clip()
        surface.set_clip(inner)

        y = rect.y + 14 - self._scroll_offset

        # We need a two-pass approach for code blocks: first compute the box
        # rect, draw bg, then draw text. Instead we do a single pass tracking
        # whether we're inside a code group.
        code_block_lines: list[tuple[int, str]] = []  # (y, text)
        code_block_start_y: int | None = None

        def _flush_code_block() -> None:
            nonlocal code_block_start_y, code_block_lines
            if code_block_start_y is None or not code_block_lines:
                code_block_start_y = None
                code_block_lines = []
                return
            # Draw background box
            last_y, _ = code_block_lines[-1]
            lh = f_code.get_height()
            box = pygame.Rect(
                pad_x - _CODE_PAD_X,
                code_block_start_y - _CODE_PAD_Y,
                max_w + _CODE_PAD_X * 2,
                (last_y + lh + _CODE_PAD_Y) - (code_block_start_y - _CODE_PAD_Y),
            )
            if box.bottom >= inner.top and box.top <= inner.bottom:
                pygame.draw.rect(surface, _CODE_BG, box, border_radius=4)
                pygame.draw.rect(surface, _C.STONE_BORDER, box, 1, border_radius=4)
            # Draw each line of code
            for cy, ctext in code_block_lines:
                if cy + lh >= inner.top and cy <= inner.bottom:
                    csurf = f_code.render(ctext, True, _CODE_FG)
                    surface.blit(csurf, (pad_x, cy))
            code_block_start_y = None
            code_block_lines = []

        for style, text, font, color, indent, gap_after in rows:
            lh = font.get_height()

            if style == _STYLE_CODE:
                # Accumulate for background-box rendering
                if code_block_start_y is None:
                    code_block_start_y = y + _CODE_PAD_Y
                    y += _CODE_PAD_Y
                code_block_lines.append((y, text))
                y += lh + gap_after
                continue

            # Flush any pending code block before drawing a non-code row
            _flush_code_block()

            if style == _STYLE_SPACER:
                y += font.get_height() + gap_after
                continue

            if y + lh >= inner.top and y <= inner.bottom:
                if style == _STYLE_HEADING:
                    pygame.draw.rect(surface, _C.PARCHMENT_EDGE,
                                     pygame.Rect(pad_x, y + lh - 2, max_w, 1))
                if style == _STYLE_PLAYER:
                    pygame.draw.rect(surface, _C.PARCHMENT_EDGE,
                                     pygame.Rect(pad_x, y - 5, max_w, 1))
                surf = font.render(text, True, color)
                surface.blit(surf, (pad_x + indent, y))

            y += lh + gap_after

        _flush_code_block()

        surface.set_clip(old_clip)

        # ── Scrollbar ────────────────────────────────────────────────────────
        if total_h > vis_h:
            track_x = inner.right - _SCROLLBAR_W - _SCROLLBAR_PAD
            track   = pygame.Rect(track_x, inner.top + 4, _SCROLLBAR_W, inner.height - 8)
            pygame.draw.rect(surface, _C.PARCHMENT_EDGE, track, border_radius=4)

            thumb_ratio = min(1.0, vis_h / total_h)
            thumb_h     = max(24, int(track.height * thumb_ratio))
            thumb_top   = track.top + int((track.height - thumb_h) * self._scroll_offset / max(1, max_scroll))
            thumb       = pygame.Rect(track_x, thumb_top, _SCROLLBAR_W, thumb_h)
            pygame.draw.rect(surface, _C.WOOD_FILL, thumb, border_radius=4)


# ── helpers ───────────────────────────────────────────────────────────────────


def _blit_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    x: int,
    y: int,
    color: tuple[int, int, int],
) -> None:
    surf = font.render(text, True, color)
    surface.blit(surf, (x, y))


def _wrap(font: pygame.font.Font, text: str, max_w: int) -> list[str]:
    """Naive word-wrap for a single line of text."""
    if font.size(text)[0] <= max_w:
        return [text]
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if font.size(test)[0] <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]
