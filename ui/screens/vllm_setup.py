"""vLLM setup component — embedded in the Coach screen's AI Summary tab.

Shown when enable_ai = true but the vLLM health probe returns False.
Provides Retry and Use-Templates-Only buttons.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pygame

from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font, code_font
from ui.theme import MARGIN_X, content_width
from ui.widgets import Button, WidgetGroup

if TYPE_CHECKING:
    from engine.core.config import AppConfig

_SETUP_COMMANDS = [
    "pip install vllm",
    "vllm serve Qwen/Qwen2.5-1.5B-Instruct \\",
    "    --max-model-len 4096",
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
        cmd_font   = code_font(14)

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
            x, y, colors.TEXT_MUTED,
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
            x, y, colors.TEXT_MUTED,
        )
        y += label_font.get_height() + 4
        _blit_text(
            surface,
            label_font,
            "and rerun the simulation.",
            x, y, colors.TEXT_MUTED,
        )
        y += label_font.get_height() + 24

        # Buttons
        self._retry_btn.rect     = pygame.Rect(x, y, 180, 38)
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
        item_font  = body_font(14)

        header = label_font.render(
            "Template feedback (AI offline)", True, colors.PARCHMENT_TEXT
        )
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


class AiReportPanel:
    """Renders the contents of ai_report.md inside the AI Summary tab."""

    def __init__(self) -> None:
        self._scroll_offset = 0

    def reset(self) -> None:
        self._scroll_offset = 0

    def handle_wheel(self, event: pygame.event.Event, rect: pygame.Rect) -> bool:
        if event.type == pygame.MOUSEWHEEL and rect.collidepoint(pygame.mouse.get_pos()):
            self._scroll_offset = max(0, self._scroll_offset - event.y * 20)
            return True
        return False

    def draw(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        report_text: str,
    ) -> None:
        skin.draw_panel(surface, rect, style="parchment")

        item_font = body_font(14)
        max_w = rect.width - 32
        lines: list[str] = []
        for raw_line in report_text.splitlines():
            lines.extend(_wrap(item_font, raw_line or " ", max_w))

        lh = item_font.get_height() + 3
        old_clip = surface.get_clip()
        surface.set_clip(rect.inflate(-4, -4))

        y = rect.y + 12 - self._scroll_offset
        for line in lines:
            if y + lh >= rect.top and y <= rect.bottom:
                color = colors.GOLD_TEXT if line.startswith("#") else colors.PARCHMENT_TEXT
                surf = item_font.render(line.lstrip("#").strip(), True, color)
                surface.blit(surf, (rect.x + 16, y))
            y += lh

        surface.set_clip(old_clip)


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
