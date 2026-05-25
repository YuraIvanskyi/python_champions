"""End-of-game score screen — RPG launcher visual redesign."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pygame

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

_ROW_H_WITH_SUB = 50
_ROW_H_SIMPLE   = 38

# Vertical layout constants
_BANNER_BOTTOM = 86      # top of scrollable viewport
_BTN_MARGIN_B  = 16      # gap below buttons to screen bottom


def _clip_text(text: str) -> str:
    """Only truncate genuinely over-long strings."""
    if len(text) > _MAX_TEXT_LEN:
        return text[:_MAX_TEXT_LEN - 1] + "…"
    return text


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
        skin.draw_banner_title(surface, "Game Over", center_x=sw // 2, y=22, max_width=cw)

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
        score_panel_h = 45 + 8 + len(lines) * row_h + 10 + _PANEL_PAD

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
        skin.draw_panel_titled(surface, score_panel, "Final Scores", style="wood")
        self._draw_score_rows(surface, lines, score_panel, mx, panel_w, has_metrics, row_h)
        y += score_panel_h

        # Session ID
        y += 8
        session_text = _clip_text(
            f"Session: {self.session_dir.name}" if self.session_dir else "Session not saved"
        )
        sess_surf = body_font(_SESSION_PT).render(session_text, True, colors.TEXT_MUTED)
        surface.blit(sess_surf, (sw // 2 - sess_surf.get_width() // 2, y))
        y += session_block_h

        # Analysis panel
        if analysis_sections:
            analysis_panel = pygame.Rect(mx, y, panel_w, analysis_panel_h)
            content_rect = skin.draw_panel_titled(
                surface, analysis_panel, "Analysis", style="parchment"
            )
            self._draw_analysis_sections(
                surface, analysis_sections,
                content_rect.x, content_rect.y, content_rect.width,
            )

        surface.set_clip(old_clip)

        # Scrollbar
        if self._scroll.max_offset > 0:
            self._draw_scrollbar(surface, mx + panel_w + _SCROLLBAR_PAD, vp_top, vp_h)

    # ── Score rows ────────────────────────────────────────────────────────────

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

        badge_area_w = 40

        ranked: list[tuple[int, str, int]] = [
            (i + 1, pid, sc) for i, (pid, sc) in enumerate(lines)
        ]

        row_y = score_panel.y + 45 + 8

        for rank, pid, sc in ranked:
            rank_color = (
                _RANK_COLORS[rank - 1] if rank <= len(_RANK_COLORS) else colors.TEXT_MUTED
            )
            is_top = rank == 1

            if is_top and len(ranked) > 1:
                hl = pygame.Surface((panel_w - 20, row_h), pygame.SRCALPHA)
                hl.fill((255, 205, 48, 22))
                surface.blit(hl, (mx + 10, row_y))

            badge_label = _RANK_LABELS[rank - 1] if rank <= len(_RANK_LABELS) else f"{rank}TH"
            badge_surf = badge_font.render(badge_label, True, rank_color)
            surface.blit(badge_surf, (
                mx + _PANEL_PAD,
                row_y + (row_h // 2) - badge_surf.get_height() // 2,
            ))

            display  = _clip_text(self._display_name(pid))
            name_col = rank_color if is_top else colors.TEXT_BODY
            name_surf = name_font.render(display, True, name_col)
            name_x = mx + _PANEL_PAD + badge_area_w
            name_y = row_y + 4
            surface.blit(name_surf, (name_x, name_y))

            num_surf = num_font.render(str(sc), True, rank_color)
            num_x = mx + panel_w - _PANEL_PAD - num_surf.get_width()
            num_y = row_y + (name_surf.get_height() - num_surf.get_height()) // 2 + 4
            surface.blit(num_surf, (num_x, num_y))

            res_surf = sub_font.render("resources", True, colors.TEXT_MUTED)
            res_x = num_x - res_surf.get_width() - 6
            res_y = num_y + num_surf.get_height() - res_surf.get_height() - 1
            surface.blit(res_surf, (res_x, res_y))

            if has_metrics and self.metrics:
                pd = self.metrics.get("players", {}).get(pid, {})
                if pd:
                    sc_block = pd.get("scores", {})
                    final_v  = sc_block.get("final", "—")
                    code_q   = sc_block.get("code_quality", "—")
                    gp_v     = sc_block.get("gameplay", "—")
                    sub_text = _clip_text(
                        f"Final: {final_v} pts   Quality: {code_q}/100   Gameplay: {gp_v}/100"
                    )
                    sub_surf = sub_font.render(sub_text, True, colors.TEXT_MUTED)
                    sub_x = name_x
                    sub_y = name_y + name_surf.get_height() + 4
                    surface.blit(sub_surf, (sub_x, sub_y))

            row_y += row_h

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
            scenario_raw     = self.replay_meta.get("scenario", "")
            scenario_display = scenario_raw.replace("_", " ").title()
            seed    = self.replay_meta.get("seed", "?")
            n_turns = len(self.replay_meta.get("turns", []))
            ctx = f"Scenario: {scenario_display}   Seed: {seed}   {n_turns} turns played"
        elif self.session_dir:
            ctx = f"Session: {self.session_dir.name}"
        else:
            return sections

        sections.append({"type": "context", "text": _clip_text(ctx), "h": line_h + 4})

        if self.metrics:
            players_dict = self.metrics.get("players", {})
            for i, (pid, pdata) in enumerate(players_dict.items()):
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
                    f"Final: {final_v} pts",
                    f"Quality: {code_q}/100",
                    f"Gameplay: {gp_v}/100",
                ]
                if avg_ms is not None:
                    stats_parts.append(f"Avg turn: {avg_ms:.2f} ms")
                if crashes or timeouts:
                    stats_parts.append(f"Crashes: {crashes}  Timeouts: {timeouts}")
                stats_line = "   ".join(stats_parts)

                feedback = pdata.get("feedback", [])
                hint = _clip_text(str(feedback[0])) if feedback else ""

                if i > 0:
                    sections.append({"type": "divider", "h": 10})

                # Name on its own line, then stats, then hint
                n_lines = 1 + 1 + (1 if hint else 0)  # name + stats + optional hint
                entry_h = n_lines * line_h + 4
                sections.append({
                    "type": "player",
                    "display": display,
                    "stats": _clip_text(stats_line),
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

                # Hint line (indented, only if present)
                if sec["hint"]:
                    surface.blit(
                        af.render(sec["hint"], True, (100, 78, 38)),
                        (ax + 14, ay),
                    )
                    ay += line_h
