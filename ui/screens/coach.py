"""Code Coach — gamified analysis review screen."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pygame

from ui.coach_data import (
    bot_path_for_player,
    list_player_metrics,
    load_metrics_block,
    load_replay,
    player_ids_from_replay,
    read_bot_source,
)
from ui.render.code_panel import draw_code_panel
from ui.render.quest_card import draw_quest_card, quest_card_height
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font
from ui.theme import FOOTER_PT, MARGIN_X, coach_config, content_width, footer_top
from ui.widgets import Button, WidgetGroup
from ui.widgets.scroll import ScrollState

_CARD_H = 104
_CARD_GAP = 8
_LABEL_PT = 14


class CoachScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.session_dir: Path | None = None
        self.metrics: dict[str, Any] | None = None
        self.replay: dict[str, Any] | None = None
        self.player_ids: list[str] = []
        self.selected_player = 0
        self.selected_quest = 0
        self._code_scroll = ScrollState()
        self._quest_scroll = ScrollState()
        self._back_btn = Button(
            pygame.Rect(MARGIN_X, 0, 120, 40),
            "Back",
            on_click=self._back_to_scores,
        )
        self._menu_btn = Button(
            pygame.Rect(0, 0, 100, 40),
            "Menu",
            on_click=lambda: self.app.goto_menu(),
        )
        self._player_tabs: list[Button] = []
        self._widgets = WidgetGroup([self._back_btn, self._menu_btn])

    def open_session(self, session_dir: Path, *, player_id: str | None = None) -> None:
        self.session_dir = session_dir
        self.metrics = None
        self.replay = load_replay(session_dir)
        metrics_path = session_dir / "metrics.json"
        if metrics_path.is_file():
            self.metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        self.player_ids = player_ids_from_replay(self.replay) if self.replay else []
        if not self.player_ids and self.metrics:
            self.player_ids = [pid for pid, _ in list_player_metrics(self.metrics)]
        if not self.player_ids:
            self.player_ids = ["student"]
        if player_id and player_id in self.player_ids:
            self.selected_player = self.player_ids.index(player_id)
        else:
            self.selected_player = 0
        self.selected_quest = 0
        self._build_player_tabs()

    def _build_player_tabs(self) -> None:
        self._player_tabs = []
        self._widgets = WidgetGroup([self._back_btn, self._menu_btn])
        if len(self.player_ids) <= 1:
            return
        x = MARGIN_X
        y = 72
        for index, pid in enumerate(self.player_ids):
            btn = Button(
                pygame.Rect(x, y, 100, 32),
                pid[:10],
                on_click=lambda i=index: self._select_player(i),
            )
            self._player_tabs.append(btn)
            self._widgets.add(btn)
            x += 108

    def _select_player(self, index: int) -> None:
        self.selected_player = index
        self.selected_quest = 0

    def _back_to_scores(self) -> None:
        if not self.session_dir:
            self.app.goto_menu()
            return
        final: dict[str, int] = {}
        if self.replay:
            raw = self.replay.get("final_scores", {})
            if isinstance(raw, dict):
                players = self.replay.get("players", {})
                for pid, score in raw.items():
                    if isinstance(players, dict) and pid in players:
                        name = players[pid].get("display_name", pid)
                        final[str(name)] = int(score)
                    else:
                        final[str(pid)] = int(score)
        if not final:
            block = self._current_block()
            raw_scores = block.get("gameplay", {}).get("raw_scores", {})
            if isinstance(raw_scores, dict):
                final = {str(k): int(v) for k, v in raw_scores.items()}
        self.app.goto_scores(final_scores=final, session_dir=self.session_dir)

    def _current_block(self) -> dict[str, Any]:
        if self.metrics is None:
            return {}
        pid = self.player_ids[self.selected_player]
        return load_metrics_block(self.metrics, pid)

    def _current_quests(self) -> list[dict[str, Any]]:
        block = self._current_block()
        items = block.get("feedback_items", [])
        max_cards, _ = coach_config()
        return list(items[:max_cards])

    def _highlight_lines(self) -> set[int]:
        quests = self._current_quests()
        if not quests:
            return set()
        idx = min(self.selected_quest, len(quests) - 1)
        lines = quests[idx].get("lines", [])
        return {int(ln) for ln in lines if isinstance(ln, int)}

    def on_enter(self) -> None:
        self._code_scroll.offset = 0
        self._quest_scroll.offset = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        layout = self._layout_rects(pygame.display.get_surface())
        if layout and self._code_scroll.handle_wheel(event, rect=layout["code"]):
            return
        if layout and self._quest_scroll.handle_wheel(event, rect=layout["quests"]):
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and layout:
            pos = event.pos
            quests = self._current_quests()
            y = layout["quests"].y - self._quest_scroll.offset
            for index, _ in enumerate(quests):
                card_rect = pygame.Rect(layout["quests"].x, y, layout["quests"].width, _CARD_H)
                if card_rect.collidepoint(pos):
                    self.selected_quest = index
                    lines = quests[index].get("lines", [])
                    if lines and isinstance(lines[0], int):
                        self._code_scroll.offset = max(0, (lines[0] - 2) * 18)
                    return
                y += _CARD_H + _CARD_GAP

        if self._widgets.handle_event(event):
            return

        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self._back_to_scores()
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.selected_quest = max(0, self.selected_quest - 1)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            quests = self._current_quests()
            if quests:
                self.selected_quest = min(len(quests) - 1, self.selected_quest + 1)

    def _layout_rects(self, surface: pygame.Surface | None) -> dict[str, pygame.Rect] | None:
        if surface is None:
            return None
        w = surface.get_width()
        top = 112 if len(self.player_ids) > 1 else 88
        bottom = footer_top() - 52
        split = int(w * 0.58)
        return {
            "code": pygame.Rect(MARGIN_X, top, split - MARGIN_X - 8, bottom - top),
            "quests": pygame.Rect(split + 8, top, w - split - MARGIN_X - 8, bottom - top),
        }

    def draw(self, surface: pygame.Surface) -> None:
        skin.draw_background(surface)
        sw = surface.get_width()
        cw = content_width()

        skin.draw_banner_title(
            surface,
            "Code Coach",
            center_x=sw // 2,
            y=14,
            max_width=cw,
        )

        self._back_btn.rect = pygame.Rect(MARGIN_X, footer_top() - 44, 120, 40)
        self._menu_btn.rect = pygame.Rect(MARGIN_X + 130, footer_top() - 44, 100, 40)

        if self.metrics is None:
            panel = pygame.Rect(MARGIN_X, 200, cw, 120)
            skin.draw_panel(surface, panel, style="parchment")
            inner = panel.inflate(-16, -16)
            font = body_font(15)
            skin.draw_text_clipped(
                surface,
                "No analysis for this session. Run a match without --no-analysis.",
                inner,
                font,
                colors.PARCHMENT_TEXT,
                align="center",
            )
            self._widgets.draw(surface)
            return

        pid = self.player_ids[self.selected_player]
        block = self._current_block()
        bot_path = bot_path_for_player(self.replay, pid) if self.replay else None
        source_lines = read_bot_source(bot_path)

        name = pid
        if self.replay and "players" in self.replay:
            meta = self.replay["players"].get(pid, {})
            name = meta.get("display_name", pid)

        label_font = body_font(_LABEL_PT)
        bot_label = f"Bot: {name}"
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(MARGIN_X, 54, cw, _LABEL_PT + 8))
        skin.draw_text_clipped(
            surface, bot_label,
            pygame.Rect(MARGIN_X, 54, cw, _LABEL_PT + 8),
            label_font, colors.GOLD_TEXT, align="left",
        )
        surface.set_clip(old_clip)

        layout = self._layout_rects(surface)
        if not layout:
            return

        draw_code_panel(
            surface,
            layout["code"],
            lines=source_lines,
            highlight_lines=self._highlight_lines(),
            scroll=self._code_scroll,
            font_pt=coach_config()[1],
        )

        quests = self._current_quests()
        skin.draw_panel(surface, layout["quests"], style="wood")
        inner = layout["quests"].inflate(-8, -8)
        total_h = len(quests) * (_CARD_H + _CARD_GAP)
        self._quest_scroll.set_content(total_h, inner.height)
        y = inner.y - self._quest_scroll.offset

        old_clip = surface.get_clip()
        surface.set_clip(inner)
        for index, item in enumerate(quests):
            card_rect = pygame.Rect(inner.x, y, inner.width, _CARD_H)
            if card_rect.bottom >= inner.top and card_rect.top <= inner.bottom:
                draw_quest_card(
                    surface,
                    card_rect,
                    item,
                    selected=index == self.selected_quest,
                )
            y += _CARD_H + _CARD_GAP
        surface.set_clip(old_clip)

        # Score summary bar
        scores = block.get("scores", {})
        footer_text = (
            f"Gameplay {scores.get('gameplay', '—')} · "
            f"Code {scores.get('code_quality', '—')} · "
            f"Final {scores.get('final', '—')}"
        )
        score_rect = pygame.Rect(MARGIN_X, footer_top() - 72, cw, _LABEL_PT + 8)
        skin.draw_text_clipped(surface, footer_text, score_rect, label_font, colors.TEXT_MUTED, align="left")

        self._widgets.draw(surface)

        foot = body_font(FOOTER_PT)
        foot_surf = foot.render(
            "Wheel scroll · Click quest · ↑↓ quest · Esc back", True, colors.TEXT_MUTED
        )
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(MARGIN_X, footer_top() + 4, cw, FOOTER_PT + 8))
        surface.blit(foot_surf, (MARGIN_X, footer_top() + 4))
        surface.set_clip(old_clip)
