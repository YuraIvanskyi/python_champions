"""Code Coach — gamified analysis review screen."""

from __future__ import annotations

import json
import math
import threading
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
from ui.render.icons import load_icon
from ui.render.loading_overlay import draw_loading_overlay
from ui.render.quest_card import draw_quest_card, draw_score_card, quest_card_height
from ui.screens.vllm_setup import AiReportPanel, TemplateFeedbackPanel, VllmSetupPanel
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font
from ui.theme import MARGIN_X, coach_config, content_width, footer_top
from ui.widgets import Button, WidgetGroup
from ui.widgets.scroll import ScrollState

_CARD_GAP     = 8
_SCORE_CARD_H = 116   # score summary card is taller to give columns room
_LABEL_PT     = 14
_TAB_H        = 32
_TAB_FONT_PT  = 15

# AI tab states
_AI_TAB_CHECKING  = "checking"
_AI_TAB_OFFLINE   = "offline"
_AI_TAB_TEMPLATES = "templates"
_AI_TAB_LOADING   = "loading"
_AI_TAB_REPORT    = "report"


class CoachScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.session_dir: Path | None = None
        self.metrics: dict[str, Any] | None = None
        self.replay: dict[str, Any] | None = None
        self.player_ids: list[str] = []
        self.selected_player = 0
        self.selected_quest  = 0
        self._code_scroll  = ScrollState()
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

        # AI Summary tab state
        self._show_ai_tab = False         # True when enable_ai = true
        self._ai_tab_active = False       # user clicked the AI tab
        self._ai_state = _AI_TAB_CHECKING
        self._ai_report_text: str | None = None
        self._spinner_angle = 0.0
        self._vllm_panel = VllmSetupPanel(
            on_retry=self._retry_ai,
            on_use_templates=self._use_templates,
        )
        self._template_panel = TemplateFeedbackPanel()
        self._report_panel   = AiReportPanel()
        self._ai_tab_btn: Button | None = None

    # ── Session loading ───────────────────────────────────────────────────────

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

        # AI tab: enabled only when enable_ai = true in config
        try:
            config = self.app.config  # type: ignore[attr-defined]
        except AttributeError:
            config = None
        self._show_ai_tab = bool(config and config.analysis.enable_ai)
        self._ai_tab_active = False
        self._ai_state = _AI_TAB_CHECKING
        self._ai_report_text = None
        self._spinner_angle = 0.0
        self._report_panel.reset()

        # Pre-load report if it already exists in the session folder
        report_path = session_dir / "ai_report.md"
        if report_path.is_file():
            self._ai_report_text = report_path.read_text(encoding="utf-8")
            self._ai_state = _AI_TAB_REPORT

        self._build_player_tabs()

    # ── AI tab helpers ────────────────────────────────────────────────────────

    def _retry_ai(self) -> None:
        """Re-probe vLLM health and generate report if reachable."""
        from ai.health import reset_cache
        reset_cache()
        self._ai_state = _AI_TAB_LOADING
        self._spinner_angle = 0.0
        self._generate_ai_report_async()

    def _use_templates(self) -> None:
        self._ai_state = _AI_TAB_TEMPLATES

    def _open_ai_tab(self) -> None:
        self._ai_tab_active = True
        if self._ai_state == _AI_TAB_CHECKING:
            self._check_ai_and_load()

    def _check_ai_and_load(self) -> None:
        """Check vLLM health (blocking, fast probe) then decide state."""
        if self._ai_report_text is not None:
            self._ai_state = _AI_TAB_REPORT
            return
        try:
            config = self.app.config  # type: ignore[attr-defined]
        except AttributeError:
            self._ai_state = _AI_TAB_OFFLINE
            return
        from ai.health import is_vllm_reachable
        if is_vllm_reachable(config.ai.health_check_url, use_cache=False):
            self._ai_state = _AI_TAB_LOADING
            self._spinner_angle = 0.0
            self._generate_ai_report_async()
        else:
            self._ai_state = _AI_TAB_OFFLINE

    def _generate_ai_report_async(self) -> None:
        """Spawn a background thread to generate the AI report."""
        session_dir = self.session_dir
        if session_dir is None:
            self._ai_state = _AI_TAB_OFFLINE
            return
        try:
            config = self.app.config  # type: ignore[attr-defined]
        except AttributeError:
            self._ai_state = _AI_TAB_OFFLINE
            return

        def _worker() -> None:
            from engine.analysis.ai_report import generate_report
            path = generate_report(session_dir, config)
            if path is not None and path.is_file():
                self._ai_report_text = path.read_text(encoding="utf-8")
                self._ai_state = _AI_TAB_REPORT
            else:
                self._ai_state = _AI_TAB_OFFLINE

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def update(self, dt_ms: int) -> None:
        if self._ai_tab_active and self._ai_state == _AI_TAB_LOADING:
            self._spinner_angle = (self._spinner_angle + dt_ms * 0.004) % math.tau

    def _build_player_tabs(self) -> None:
        self._player_tabs = []
        self._ai_tab_btn = None
        self._widgets = WidgetGroup([self._back_btn, self._menu_btn])

        tab_font = body_font(_TAB_FONT_PT)
        x = MARGIN_X
        y = 72

        if len(self.player_ids) > 1:
            for index, pid in enumerate(self.player_ids):
                display = self._display_name(pid)
                text_w = tab_font.size(display)[0]
                # 22 px extra left room for the 18 px portrait icon + gap
                btn_w  = text_w + 50
                btn    = Button(
                    pygame.Rect(x, y, btn_w, _TAB_H),
                    display,
                    on_click=lambda i=index: self._select_player(i),
                    font_size=_TAB_FONT_PT,
                )
                self._player_tabs.append(btn)
                self._widgets.add(btn)
                x += btn_w + 8

        if self._show_ai_tab:
            ai_label = "⚗ AI Summary"
            ai_w = tab_font.size(ai_label)[0] + 28
            self._ai_tab_btn = Button(
                pygame.Rect(x, y, ai_w, _TAB_H),
                ai_label,
                on_click=self._open_ai_tab,
                font_size=_TAB_FONT_PT,
            )
            self._widgets.add(self._ai_tab_btn)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _display_name(self, pid: str) -> str:
        """Return the human-readable display name for a player id."""
        if self.replay and "players" in self.replay:
            meta = self.replay["players"].get(pid, {})
            return str(meta.get("display_name", pid))
        return pid

    def _player_icon(self, pid: str, size: int = 32) -> pygame.Surface | None:
        """Return the portrait surface for a player, or None."""
        if not self.replay:
            return None
        info = self.replay.get("players", {}).get(pid, {})
        icon_path = info.get("icon")
        if not icon_path:
            return None
        return load_icon(str(icon_path), size=size)

    def _select_player(self, index: int) -> None:
        self.selected_player = index
        self.selected_quest  = 0
        self._ai_tab_active  = False

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
        idx   = min(self.selected_quest, len(quests) - 1)
        lines = quests[idx].get("lines", [])
        return {int(ln) for ln in lines if isinstance(ln, int)}

    def _score_summary_item(self, block: dict, bot_name: str) -> dict[str, Any]:
        """Synthesise a score-summary quest card from the metrics block."""
        scores = block.get("scores", {})
        gp = scores.get("gameplay",     "—")
        cq = scores.get("code_quality", "—")
        fn = scores.get("final",        "—")
        return {
            "category": "praise",
            "title":    f"Final  {fn}",
            "message":  f"{bot_name}   ·   Gameplay {gp}   ·   Code {cq}",
            "fix_hint": "",
            "panel":    "parchment",
            "lines":    [],
        }

    # ── Layout ────────────────────────────────────────────────────────────────

    def _layout_rects(self, surface: pygame.Surface | None) -> dict[str, pygame.Rect] | None:
        if surface is None:
            return None
        w      = surface.get_width()
        has_tabs = len(self.player_ids) > 1 or self._show_ai_tab
        top    = 112 if has_tabs else 88
        bottom = footer_top() - 52
        split  = int(w * 0.58)
        quests_x = split + 8
        quests_w = w - split - MARGIN_X - 8
        full_w   = w - 2 * MARGIN_X
        return {
            "code": pygame.Rect(MARGIN_X, top, split - MARGIN_X - 8, bottom - top),
            "score_card": pygame.Rect(quests_x, top, quests_w, _SCORE_CARD_H),
            "quests": pygame.Rect(
                quests_x,
                top + _SCORE_CARD_H + 8,
                quests_w,
                bottom - top - _SCORE_CARD_H - 8,
            ),
            # AI tab takes full content width
            "ai_panel": pygame.Rect(MARGIN_X, top, full_w, bottom - top),
        }

    # ── Events ────────────────────────────────────────────────────────────────

    def on_enter(self) -> None:
        self._code_scroll.offset  = 0
        self._quest_scroll.offset = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        layout = self._layout_rects(pygame.display.get_surface())

        # AI tab gets priority for wheel and panel events
        if self._ai_tab_active and layout:
            if self._ai_state == _AI_TAB_OFFLINE:
                if self._vllm_panel.handle_event(event):
                    return
            elif self._ai_state == _AI_TAB_REPORT:
                ai_rect = layout.get("ai_panel")
                if ai_rect and self._report_panel.handle_wheel(event, ai_rect):
                    return

        if not self._ai_tab_active and layout:
            if self._code_scroll.handle_wheel(event, rect=layout["code"]):
                return
            if self._quest_scroll.handle_wheel(event, rect=layout["quests"]):
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos    = event.pos
                quests = self._current_quests()
                inner_q = layout["quests"].inflate(-8, -8)
                card_w  = inner_q.width - 8   # matches draw() card_w approximation
                y       = inner_q.y - self._quest_scroll.offset
                for index, item in enumerate(quests):
                    card_h = quest_card_height(item, card_w)
                    card_rect = pygame.Rect(inner_q.x, y, card_w, card_h)
                    if card_rect.collidepoint(pos):
                        self.selected_quest = index
                        lines = quests[index].get("lines", [])
                        if lines and isinstance(lines[0], int):
                            self._code_scroll.offset = max(0, (lines[0] - 2) * 18)
                        return
                    y += card_h + _CARD_GAP

        if self._widgets.handle_event(event):
            return

        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            if self._ai_tab_active:
                self._ai_tab_active = False
            else:
                self._back_to_scores()
        elif not self._ai_tab_active:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_quest = max(0, self.selected_quest - 1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                quests = self._current_quests()
                if quests:
                    self.selected_quest = min(len(quests) - 1, self.selected_quest + 1)

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        skin.draw_background(surface)
        sw = surface.get_width()
        cw = content_width()

        skin.draw_banner_title(
            surface, "Code Coach",
            center_x=sw // 2, y=14, max_width=cw,
        )

        self._back_btn.rect = pygame.Rect(MARGIN_X,           footer_top() - 44, 120, 40)
        self._menu_btn.rect = pygame.Rect(MARGIN_X + 130,     footer_top() - 44, 100, 40)

        if self.metrics is None:
            panel = pygame.Rect(MARGIN_X, 200, cw, 120)
            skin.draw_panel(surface, panel, style="parchment")
            skin.draw_text_clipped(
                surface,
                "No analysis for this session. Run a match without --no-analysis.",
                panel.inflate(-16, -16),
                body_font(15),
                colors.PARCHMENT_TEXT,
                align="center",
            )
            self._widgets.draw(surface)
            return

        pid      = self.player_ids[self.selected_player]
        block    = self._current_block()
        bot_path = bot_path_for_player(self.replay, pid) if self.replay else None
        source_lines = read_bot_source(bot_path)

        # Display name (used for label and score card)
        name = self._display_name(pid)

        # "Bot: <name>" header with portrait icon
        label_font = body_font(_LABEL_PT)
        _HEADER_ICON = 28
        icon_surf = self._player_icon(pid, size=_HEADER_ICON)
        if icon_surf is not None:
            surface.blit(icon_surf, (MARGIN_X, 50))
            label_x = MARGIN_X + _HEADER_ICON + 6
        else:
            label_x = MARGIN_X
        skin.draw_text_clipped(
            surface,
            f"Bot:  {name}",
            pygame.Rect(label_x, 54, cw - (label_x - MARGIN_X), _LABEL_PT + 8),
            label_font,
            colors.GOLD_TEXT,
            align="left",
        )

        # Active tab highlight
        for i, btn in enumerate(self._player_tabs):
            if i == self.selected_player and not self._ai_tab_active:
                pygame.draw.rect(surface, colors.TEAL_ACCENT, btn.rect, 2, border_radius=5)
        if self._ai_tab_active and self._ai_tab_btn:
            pygame.draw.rect(surface, colors.TEAL_ACCENT, self._ai_tab_btn.rect, 2, border_radius=5)

        layout = self._layout_rects(surface)
        if not layout:
            return

        # ── AI tab view ───────────────────────────────────────────────────────
        if self._ai_tab_active:
            ai_rect = layout["ai_panel"]
            self._draw_ai_panel(surface, ai_rect, block)
            self._widgets.draw(surface)
            self._draw_ai_loading_overlay_if_needed(surface)
            return

        # ── Normal coach view ─────────────────────────────────────────────────

        # Code panel
        draw_code_panel(
            surface,
            layout["code"],
            lines=source_lines,
            highlight_lines=self._highlight_lines(),
            scroll=self._code_scroll,
            font_pt=coach_config()[1],
        )

        # Score summary card (fixed, always visible at top of right column)
        scores = block.get("scores", {})
        draw_score_card(
            surface, layout["score_card"],
            bot_name=name,
            gameplay_score=scores.get("gameplay", "—"),
            code_score=scores.get("code_quality", "—"),
            final_score=scores.get("final", "—"),
        )

        # Scrollable quest list
        quests = self._current_quests()
        skin.draw_panel(surface, layout["quests"], style="wood")
        inner    = layout["quests"].inflate(-8, -8)

        _SCROLLBAR_W = 6
        card_w = inner.width - _SCROLLBAR_W - 2   # leave room for scrollbar

        card_heights = [quest_card_height(item, card_w) for item in quests]
        total_h = sum(card_heights) + max(0, len(card_heights) - 1) * _CARD_GAP
        self._quest_scroll.set_content(total_h, inner.height)
        y = inner.y - self._quest_scroll.offset

        old_clip = surface.get_clip()
        surface.set_clip(inner)
        for index, (item, card_h) in enumerate(zip(quests, card_heights)):
            card_rect = pygame.Rect(inner.x, y, card_w, card_h)
            if card_rect.bottom >= inner.top and card_rect.top <= inner.bottom:
                draw_quest_card(
                    surface, card_rect, item,
                    selected=index == self.selected_quest,
                )
            y += card_h + _CARD_GAP
        surface.set_clip(old_clip)

        # Scrollbar on the right edge of the quest panel
        track = pygame.Rect(inner.right - _SCROLLBAR_W, inner.y, _SCROLLBAR_W, inner.height)
        skin.draw_scrollbar(
            surface, track,
            content_height=self._quest_scroll.content_height,
            viewport_height=self._quest_scroll.viewport_height,
            offset=self._quest_scroll.offset,
        )

        self._widgets.draw(surface)

        # Portrait icons overlaid on multi-player tabs (drawn after widget backgrounds)
        if len(self.player_ids) > 1:
            _TAB_ICON = 18
            for i, (tab_pid, tab_btn) in enumerate(zip(self.player_ids, self._player_tabs)):
                tab_icon = self._player_icon(tab_pid, size=_TAB_ICON)
                if tab_icon is not None:
                    ix = tab_btn.rect.x + 4
                    iy = tab_btn.rect.y + (tab_btn.rect.height - _TAB_ICON) // 2
                    surface.blit(tab_icon, (ix, iy))

    def _player_info_for_report(self) -> dict[str, dict[str, object]]:
        info: dict[str, dict[str, object]] = {}
        if not self.replay:
            return info
        for pid in self.player_ids:
            meta = self.replay.get("players", {}).get(pid, {})
            bot_path = bot_path_for_player(self.replay, pid)
            info[pid] = {
                "display_name": meta.get("display_name", pid),
                "icon": meta.get("icon"),
                "bot_file": bot_path.name if bot_path else pid,
            }
        return info

    def _draw_ai_panel(
        self, surface: pygame.Surface, rect: pygame.Rect, block: dict[str, Any]
    ) -> None:
        state = self._ai_state
        if state == _AI_TAB_CHECKING:
            _draw_status(surface, rect, "Checking vLLM connection…", colors.TEXT_MUTED)
        elif state == _AI_TAB_LOADING:
            skin.draw_panel(surface, rect, style="stone")
        elif state == _AI_TAB_OFFLINE:
            self._vllm_panel.draw(surface, rect)
        elif state == _AI_TAB_TEMPLATES:
            feedback = block.get("feedback", [])
            self._template_panel.draw(surface, rect, feedback)
        elif state == _AI_TAB_REPORT:
            text = self._ai_report_text or ""
            self._report_panel.draw(surface, rect, text, players=self._player_info_for_report())

    def _draw_ai_loading_overlay_if_needed(self, surface: pygame.Surface) -> None:
        if not self._ai_tab_active or self._ai_state != _AI_TAB_LOADING:
            return
        draw_loading_overlay(
            surface,
            message="Generating AI summary…",
            subtitle="Consulting the arcane advisor…",
            spinner_angle=self._spinner_angle,
        )


def _draw_status(
    surface: pygame.Surface,
    rect: pygame.Rect,
    message: str,
    color: tuple[int, int, int],
) -> None:
    from ui.skin import chrome as _skin
    from ui.skin.typography import body_font as _bf
    _skin.draw_panel(surface, rect, style="stone")
    font = _bf(16)
    surf = font.render(message, True, color)
    cx = rect.x + (rect.width - surf.get_width()) // 2
    cy = rect.y + (rect.height - surf.get_height()) // 2
    surface.blit(surf, (cx, cy))
