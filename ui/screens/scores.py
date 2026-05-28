"""End-of-game score screen — RPG launcher visual redesign."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pygame

from ui.render.icons import load_icon
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font
from ui.theme import MARGIN_X, content_width
from ui.widgets import Button, WidgetGroup
from ui.widgets.scroll import ScrollState

_PANEL_PAD = 16
_SCORE_NAME_PT = 20
_SCORE_NUM_PT = 22
_SCORE_SUB_PT = 13
_BADGE_PT = 11
_SESSION_PT = 13
_ANALYSIS_PT = 13
_ANALYSIS_NAME_PT = 14
_BTN_H = 46
_BTN_W_PRIMARY = 180
_BTN_W_SECONDARY = 148
_BTN_GAP = 12
_SCROLLBAR_W = 8
_SCROLLBAR_PAD = 4

_MAX_TEXT_LEN = 300

_RANK_COLORS = [
    colors.GOLD_TEXT,         # 1st — gold
    (190, 196, 215),          # 2nd — silver
    (185, 126, 65),           # 3rd — bronze
]
_RANK_LABELS = ["1ST", "2ND", "3RD", "4TH", "5TH", "6TH"]

_ROW_H_WITH_SUB = 56
_ROW_H_SIMPLE   = 46
_ICON_SIZE      = 32
_ROW_GAP        = 3

# Vertical layout constants
_BANNER_BOTTOM = 86      # top of scrollable viewport
_BTN_MARGIN_B  = 16      # gap below buttons to screen bottom


def _clip_text(text: str) -> str:
    """Only truncate genuinely over-long strings."""
    if len(text) > _MAX_TEXT_LEN:
        return text[:_MAX_TEXT_LEN - 1] + "…"
    return text


def _best_feedback_hint(pdata: dict) -> str:
    """Return the most relevant feedback string for the analysis panel.

    Prefers logic/movement/runtime items over style/praise so that students
    see actionable issues even when the hint slot shows only one line.
    """
    items = pdata.get("feedback_items", [])
    priority_order = ("runtime", "logic", "efficiency", "style", "praise")
    by_category: dict[str, str] = {}
    for item in items:
        cat = item.get("category", "")
        if cat not in by_category:
            by_category[cat] = item.get("message", "")
    for cat in priority_order:
        if cat in by_category:
            return _clip_text(by_category[cat])
    # Fallback to plain feedback strings
    feedback = pdata.get("feedback", [])
    return _clip_text(str(feedback[0])) if feedback else ""


def _movement_summary(mv: dict, *, lang: str = "en") -> str:
    """Build a compact one-line movement summary for the analysis panel."""
    from engine.i18n import translate

    if not mv.get("analyzed"):
        return ""
    parts: list[str] = []
    blocked_ratio = float(mv.get("blocked_move_ratio", 0.0))
    if blocked_ratio >= 0.15:
        parts.append(
            translate("scores.movement_blocked", lang=lang, pct=int(blocked_ratio * 100))
        )
    stuck = int(mv.get("stuck_episodes", 0))
    if stuck:
        parts.append(f"{translate('scores.movement_stuck', lang=lang)} {stuck}\u00d7")
    osc = int(mv.get("oscillation_episodes", 0))
    if osc:
        parts.append(f"{translate('scores.movement_bounced', lang=lang)} {osc}\u00d7")
    max_run = int(mv.get("max_consecutive_same_action", 0))
    if max_run >= 6:
        parts.append(f"{max_run}-turn repeat")
    if not parts:
        return ""
    return translate("scores.movement_prefix", lang=lang) + " \u00b7 ".join(parts)


class ScoresScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.final_scores: dict[str, int] = {}
        self.session_dir: Path | None = None
        self.metrics: dict | None = None
        self.replay_meta: dict | None = None
        self._scroll = ScrollState()
        self._viewport_rect = pygame.Rect(0, 0, 1, 1)

        self._play_again = Button(
            pygame.Rect(0, 0, _BTN_W_PRIMARY, _BTN_H),
            "Play Again",
            on_click=lambda: self.app.goto_menu(),
            primary=True,
        )
        self._view_replay = Button(
            pygame.Rect(0, 0, _BTN_W_SECONDARY, _BTN_H),
            "View Replay",
            on_click=self._open_replay,
        )
        self._coach_btn = Button(
            pygame.Rect(0, 0, _BTN_W_SECONDARY, _BTN_H),
            "Code Coach",
            on_click=self._open_coach,
        )
        self._open_results = Button(
            pygame.Rect(0, 0, _BTN_W_SECONDARY, _BTN_H),
            "Open Folder",
            on_click=self._reveal_folder,
        )
        self._widgets = WidgetGroup(
            [self._play_again, self._view_replay, self._coach_btn, self._open_results]
        )

    # ── Data loading ──────────────────────────────────────────────────────────

    def set_results(self, final_scores: dict[str, int], session_dir: Path | None) -> None:
        self.final_scores = final_scores
        self.session_dir = session_dir
        self.metrics = None
        self.replay_meta = None
        self._scroll.offset = 0
        self._play_again.label = self.app.t("scores.play_again")
        self._view_replay.label = self.app.t("scores.view_replay")
        self._coach_btn.label = self.app.t("scores.code_coach")
        self._open_results.label = self.app.t("scores.open_folder")
        if session_dir is not None:
            metrics_path = session_dir / "metrics.json"
            if metrics_path.is_file():
                self.metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            replay_path = session_dir / "replay.json"
            if replay_path.is_file():
                try:
                    self.replay_meta = json.loads(replay_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
        has_replay = session_dir is not None and (session_dir / "replay.json").is_file()
        self._view_replay.enabled = has_replay
        self._coach_btn.enabled = self.metrics is not None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _display_name(self, player_id: str) -> str:
        if self.replay_meta:
            players = self.replay_meta.get("players", {})
            if player_id in players:
                name = players[player_id].get("display_name", "")
                if name:
                    return name
        clean = re.sub(r"^p\d+_", "", player_id)
        return clean.replace("_", " ").title()

    def _open_replay(self) -> None:
        if self.session_dir is None:
            return
        replay_path = self.session_dir / "replay.json"
        if replay_path.is_file():
            self.app.open_replay(replay_path)

    def _open_coach(self) -> None:
        if self.session_dir is None:
            return
        self.app.goto_coach(self.session_dir)

    def _reveal_folder(self) -> None:
        if self.session_dir is None or not self.session_dir.is_dir():
            return
        try:
            if sys.platform == "win32":
                os.startfile(self.session_dir)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self.session_dir)], check=False)
            else:
                subprocess.run(["xdg-open", str(self.session_dir)], check=False)
        except OSError:
            pass

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._widgets.handle_event(event):
            return
        if self._scroll.handle_wheel(event, rect=self._viewport_rect):
            return
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.app.goto_menu()
        elif event.key == pygame.K_DOWN:
            self._scroll.scroll(40)
        elif event.key == pygame.K_UP:
            self._scroll.scroll(-40)
        elif event.key == pygame.K_v:
            self._open_replay()
        elif event.key == pygame.K_c:
            self._open_coach()
        elif event.key == pygame.K_ESCAPE:
            self.app.goto_menu()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        skin.draw_background(surface)
        sw, sh = surface.get_size()
        cw = content_width(sw)
        mx = MARGIN_X
        panel_w = cw - _SCROLLBAR_W - _SCROLLBAR_PAD

        # ── Banner (fixed) ────────────────────────────────────────────────────
        skin.draw_banner_title(
            surface, self.app.t("scores.game_over"), center_x=sw // 2, y=22, max_width=cw,
        )

        # ── Buttons (fixed at bottom) ─────────────────────────────────────────
        btn_y = sh - _BTN_H - _BTN_MARGIN_B
        total_btn_w = (
            _BTN_W_PRIMARY  + _BTN_GAP
            + _BTN_W_SECONDARY + _BTN_GAP
            + _BTN_W_SECONDARY + _BTN_GAP
            + _BTN_W_SECONDARY
        )
        bx = sw // 2 - total_btn_w // 2
        self._play_again.rect   = pygame.Rect(bx, btn_y, _BTN_W_PRIMARY,   _BTN_H)
        bx += _BTN_W_PRIMARY + _BTN_GAP
        self._view_replay.rect  = pygame.Rect(bx, btn_y, _BTN_W_SECONDARY, _BTN_H)
        bx += _BTN_W_SECONDARY + _BTN_GAP
        self._coach_btn.rect    = pygame.Rect(bx, btn_y, _BTN_W_SECONDARY, _BTN_H)
        bx += _BTN_W_SECONDARY + _BTN_GAP
        self._open_results.rect = pygame.Rect(bx, btn_y, _BTN_W_SECONDARY, _BTN_H)
        self._widgets.draw(surface)

        # ── Scrollable viewport ───────────────────────────────────────────────
        vp_top    = _BANNER_BOTTOM
        vp_bottom = btn_y - 8
        vp_h      = vp_bottom - vp_top
        if vp_h < 1:
            return
        self._viewport_rect = pygame.Rect(mx, vp_top, panel_w, vp_h)

        # Measure content
        lines = sorted(self.final_scores.items(), key=lambda kv: kv[1], reverse=True)
        if not lines:
            lines = [("—", 0)]
        has_metrics = self.metrics is not None
        row_h = _ROW_H_WITH_SUB if has_metrics else _ROW_H_SIMPLE
        n_rows = len(lines)
        score_panel_h = 45 + 8 + n_rows * row_h + max(0, n_rows - 1) * _ROW_GAP + 10 + _PANEL_PAD

        analysis_sections = self._build_analysis_sections()
        analysis_content_h = sum(s["h"] for s in analysis_sections)
        analysis_panel_h = (45 + analysis_content_h + _PANEL_PAD) if analysis_sections else 0

        session_block_h = _SESSION_PT + 16
        total_content_h = (
            score_panel_h
            + session_block_h
            + (analysis_panel_h + 8 if analysis_panel_h else 0)
            + 8
        )
        self._scroll.set_content(total_content_h, vp_h)

        # Draw content clipped to viewport with scroll offset applied
        old_clip = surface.get_clip()
        surface.set_clip(self._viewport_rect)

        y = vp_top - self._scroll.offset

        # Score panel
        score_panel = pygame.Rect(mx, y, panel_w, score_panel_h)
        skin.draw_panel_titled(
            surface, score_panel, self.app.t("scores.final_scores"), style="wood",
        )
        self._draw_score_rows(surface, lines, score_panel, mx, panel_w, has_metrics, row_h)
        y += score_panel_h

        # Session ID
        y += 8
        session_text = _clip_text(
            self.app.t("scores.session", name=self.session_dir.name)
            if self.session_dir
            else self.app.t("scores.session_not_saved")
        )
        sess_surf = body_font(_SESSION_PT).render(session_text, True, colors.TEXT_MUTED)
        surface.blit(sess_surf, (sw // 2 - sess_surf.get_width() // 2, y))
        y += session_block_h

        # Analysis panel
        if analysis_sections:
            analysis_panel = pygame.Rect(mx, y, panel_w, analysis_panel_h)
            content_rect = skin.draw_panel_titled(
                surface, analysis_panel, self.app.t("scores.analysis"), style="parchment"
            )
            self._draw_analysis_sections(
                surface, analysis_sections,
                content_rect.x, content_rect.y, content_rect.width,
            )

        surface.set_clip(old_clip)

        # Scrollbar
        if self._scroll.max_offset > 0:
            self._draw_scrollbar(surface, mx + panel_w + _SCROLLBAR_PAD, vp_top, vp_h)

    # ── Player icon / metrics helpers ────────────────────────────────────────

    def _player_icon_for_display(self, display_name: str, size: int = 32) -> pygame.Surface | None:
        """Return a portrait surface for the player whose display_name matches."""
        if not self.replay_meta:
            return None
        for info in self.replay_meta.get("players", {}).values():
            if str(info.get("display_name", "")) == display_name:
                icon_path = info.get("icon")
                if icon_path:
                    return load_icon(str(icon_path), size=size)
        return None

    def _player_id_for_score_row(self, row_key: str) -> str | None:
        """Map a final-scores row key (display name or player id) to metrics player id."""
        if self.replay_meta:
            players = self.replay_meta.get("players", {})
            if row_key in players:
                return row_key
            for pid, info in players.items():
                if str(info.get("display_name", "")) == row_key:
                    return pid
        if self.metrics:
            from ui.coach_data import list_player_metrics

            for pid, _ in list_player_metrics(self.metrics):
                if self._display_name(pid) == row_key:
                    return pid
        return None

    def _metrics_for_display(self, display_name: str) -> dict:
        """Return the metrics block for the player matching display_name."""
        if not self.metrics:
            return {}
        from ui.coach_data import load_metrics_block

        pid = self._player_id_for_score_row(display_name)
        if pid is None:
            return {}
        return load_metrics_block(self.metrics, pid)

    # ── Score rows ────────────────────────────────────────────────────────────

    # Layout offsets relative to the left edge of a row_rect
    _ROW_ACCENT_W  = 3
    _ROW_BADGE_W   = 44
    _ROW_ICON_W    = _ICON_SIZE   # 32
    _ROW_NAME_XOFF = _ROW_ACCENT_W + 10 + _ROW_BADGE_W + 8 + _ROW_ICON_W + 8  # 105

    def _draw_score_rows(
        self,
        surface: pygame.Surface,
        lines: list[tuple[str, int]],
        score_panel: pygame.Rect,
        mx: int,
        panel_w: int,
        has_metrics: bool,
        row_h: int,
    ) -> None:
        name_font  = body_font(_SCORE_NAME_PT)
        num_font   = body_font(_SCORE_NUM_PT)
        sub_font   = body_font(_SCORE_SUB_PT)
        badge_font = body_font(_BADGE_PT)

        ranked: list[tuple[int, str, int]] = [
            (i + 1, pid, sc) for i, (pid, sc) in enumerate(lines)
        ]

        row_y = score_panel.y + 45 + 8
        row_w = panel_w - 12

        for rank, pid, sc in ranked:
            rank_color = (
                _RANK_COLORS[rank - 1] if rank <= len(_RANK_COLORS) else colors.TEXT_MUTED
            )
            badge_label = (
                self.app.t(f"scores.rank.{rank}")
                if rank <= 6
                else f"{rank}TH"
            )
            row_rect = pygame.Rect(mx + 6, row_y, row_w, row_h)

            # Row background
            bg = pygame.Surface(row_rect.size, pygame.SRCALPHA)
            if rank == 1:
                bg.fill((60, 50, 18, 110))
            elif rank % 2 == 0:
                bg.fill((44, 52, 68, 100))
            else:
                bg.fill((36, 44, 58, 80))
            surface.blit(bg, row_rect.topleft)
            border_col = (110, 100, 60) if rank == 1 else (68, 78, 100)
            pygame.draw.rect(surface, border_col, row_rect, 1, border_radius=4)

            # Left accent bar
            accent_rect = pygame.Rect(row_rect.x, row_rect.y + 2, self._ROW_ACCENT_W, row_h - 4)
            pygame.draw.rect(surface, rank_color, accent_rect, border_radius=2)

            # Rank badge — vertically centred
            badge_surf = badge_font.render(badge_label, True, rank_color)
            badge_x = row_rect.x + self._ROW_ACCENT_W + 10
            badge_y = row_y + (row_h - badge_surf.get_height()) // 2
            surface.blit(badge_surf, (badge_x, badge_y))

            # Player icon (portrait or coloured initial circle)
            display = _clip_text(self._display_name(pid))
            icon_x = badge_x + self._ROW_BADGE_W
            icon_y = row_y + (row_h - _ICON_SIZE) // 2
            icon_surf = self._player_icon_for_display(display, size=_ICON_SIZE)
            if icon_surf is not None:
                surface.blit(icon_surf, (icon_x, icon_y))
            else:
                ctr = (icon_x + _ICON_SIZE // 2, icon_y + _ICON_SIZE // 2)
                pygame.draw.circle(surface, rank_color, ctr, _ICON_SIZE // 2 - 1)
                initial = display[:1].upper() if display else "?"
                init_s = badge_font.render(initial, True, (20, 24, 30))
                surface.blit(init_s, init_s.get_rect(center=ctr))

            # Name (+ optional metrics sub-text)
            name_x = row_rect.x + self._ROW_NAME_XOFF
            name_col = rank_color if rank == 1 else colors.TEXT_BODY
            name_surf = name_font.render(display, True, name_col)
            if has_metrics:
                name_y = row_y + max(4, (row_h // 2 - name_surf.get_height()) // 2)
            else:
                name_y = row_y + (row_h - name_surf.get_height()) // 2
            surface.blit(name_surf, (name_x, name_y))

            pd = self._metrics_for_display(display) if has_metrics else {}
            if pd:
                sc_block = pd.get("scores", {})
                final_v = sc_block.get("final", "—")
                code_q  = sc_block.get("code_quality", "—")
                gp_v    = sc_block.get("gameplay", "—")
                sub_text = _clip_text(
                    self.app.t(
                        "scores.stats_line",
                        overall=final_v,
                        quality=code_q,
                        gameplay=gp_v,
                    )
                )
                sub_surf = sub_font.render(sub_text, True, colors.TEXT_MUTED)
                surface.blit(sub_surf, (name_x, name_y + name_surf.get_height() + 3))

            # Score number — vertically centred, right-aligned
            num_surf = num_font.render(str(sc), True, rank_color)
            num_x = row_rect.right - 14 - num_surf.get_width()
            num_y = row_y + (row_h - num_surf.get_height()) // 2
            surface.blit(num_surf, (num_x, num_y))

            row_y += row_h + _ROW_GAP

    # ── Scrollbar ─────────────────────────────────────────────────────────────

    def _draw_scrollbar(self, surface: pygame.Surface, x: int, vp_top: int, vp_h: int) -> None:
        track = pygame.Rect(x, vp_top, _SCROLLBAR_W, vp_h)
        pygame.draw.rect(surface, (60, 48, 30), track, border_radius=4)

        ratio    = self._scroll.viewport_height / max(1, self._scroll.content_height)
        thumb_h  = max(24, int(vp_h * ratio))
        scroll_r = self._scroll.max_offset
        thumb_y  = vp_top + int((vp_h - thumb_h) * self._scroll.offset / max(1, scroll_r))
        thumb    = pygame.Rect(x, thumb_y, _SCROLLBAR_W, thumb_h)
        pygame.draw.rect(surface, (160, 130, 80), thumb, border_radius=4)

    # ── Analysis helpers ──────────────────────────────────────────────────────

    def _build_analysis_sections(self) -> list[dict]:
        sections: list[dict] = []
        line_h = _ANALYSIS_PT + 8

        if self.replay_meta:
            from engine.core.scenario_registry import scenario_display_name

            scenario_raw = self.replay_meta.get("scenario", "")
            scenario_display = scenario_display_name(scenario_raw, self.app.lang())
            seed = self.replay_meta.get("seed", "?")
            n_turns = len(self.replay_meta.get("turns", []))
            ctx = self.app.t(
                "scores.context",
                scenario=scenario_display,
                seed=seed,
                turns=n_turns,
            )
        elif self.session_dir:
            ctx = self.app.t("scores.session", name=self.session_dir.name)
        else:
            return sections

        sections.append({"type": "context", "text": _clip_text(ctx), "h": line_h + 4})

        if self.metrics:
            from ui.coach_data import list_player_metrics

            for i, (pid, pdata) in enumerate(list_player_metrics(self.metrics)):
                display  = self._display_name(pid)
                sc_block = pdata.get("scores", {})
                final_v  = sc_block.get("final", "—")
                code_q   = sc_block.get("code_quality", "—")
                gp_v     = sc_block.get("gameplay", "—")
                runtime  = pdata.get("runtime", {})
                crashes  = runtime.get("crash_count", 0)
                timeouts = runtime.get("timeout_count", 0)
                avg_ms   = runtime.get("avg_turn_time_ms", None)

                stats_parts = [
                    self.app.t("scores.final_pts", v=final_v),
                    self.app.t("scores.quality_pts", v=code_q),
                    self.app.t("scores.gameplay_pts", v=gp_v),
                ]
                if avg_ms is not None:
                    stats_parts.append(self.app.t("scores.avg_turn", ms=avg_ms))
                if crashes or timeouts:
                    stats_parts.append(
                        self.app.t("scores.crashes", n=crashes)
                        + "  "
                        + self.app.t("scores.timeouts", n=timeouts)
                    )
                stats_line = "   ".join(stats_parts)

                # Prefer a movement/logic feedback item over generic praise
                hint = _best_feedback_hint(pdata)

                # Compact movement summary line
                mv_line = _movement_summary(
                    pdata.get("movement", {}), lang=self.app.lang(),
                )

                if i > 0:
                    sections.append({"type": "divider", "h": 10})

                # Name on its own line, then stats, then optional movement, then hint
                n_extra = (1 if mv_line else 0) + (1 if hint else 0)
                entry_h = (1 + 1 + n_extra) * line_h + 4
                sections.append({
                    "type": "player",
                    "display": display,
                    "stats": _clip_text(stats_line),
                    "movement": mv_line,
                    "hint": hint,
                    "h": entry_h,
                })

        return sections

    def _draw_analysis_sections(
        self,
        surface: pygame.Surface,
        sections: list[dict],
        ax: int,
        ay: int,
        aw: int,
    ) -> None:
        af     = body_font(_ANALYSIS_PT)
        name_f = body_font(_ANALYSIS_NAME_PT)
        line_h = _ANALYSIS_PT + 8

        for sec in sections:
            if sec["type"] == "context":
                surface.blit(af.render(sec["text"], True, colors.PARCHMENT_TEXT), (ax, ay))
                ay += sec["h"]

            elif sec["type"] == "divider":
                div_y = ay + sec["h"] // 2
                pygame.draw.line(
                    surface, colors.PARCHMENT_EDGE,
                    (ax, div_y), (ax + aw, div_y),
                )
                ay += sec["h"]

            elif sec["type"] == "player":
                # Name line
                surface.blit(
                    name_f.render(sec["display"] + ":", True, (72, 50, 18)),
                    (ax, ay),
                )
                ay += line_h

                # Stats line (indented)
                surface.blit(
                    af.render(sec["stats"], True, colors.PARCHMENT_TEXT),
                    (ax + 14, ay),
                )
                ay += line_h

                # Movement summary line (indented, amber tint)
                mv_line = sec.get("movement", "")
                if mv_line:
                    surface.blit(
                        af.render(mv_line, True, (160, 120, 40)),
                        (ax + 14, ay),
                    )
                    ay += line_h

                # Hint line (indented, only if present)
                if sec["hint"]:
                    surface.blit(
                        af.render(sec["hint"], True, (100, 78, 38)),
                        (ax + 14, ay),
                    )
                    ay += line_h
