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
from ui.theme import FOOTER_PT, MARGIN_X, content_width, footer_top
from ui.widgets import Button, WidgetGroup

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

_RANK_COLORS = [
    colors.GOLD_TEXT,         # 1st — gold
    (190, 196, 215),          # 2nd — silver
    (185, 126, 65),           # 3rd — bronze
]
_RANK_LABELS = ["1ST", "2ND", "3RD", "4TH", "5TH", "6TH"]

# Height per player row in score panel
_ROW_H_WITH_SUB = 50   # name line + sub-scores line
_ROW_H_SIMPLE   = 38   # name line only


class ScoresScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.final_scores: dict[str, int] = {}
        self.session_dir: Path | None = None
        self.metrics: dict | None = None
        self.replay_meta: dict | None = None

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
        """Return human-friendly display name for a player ID."""
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
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.app.goto_menu()
        elif event.key == pygame.K_v:
            self._open_replay()
        elif event.key == pygame.K_c:
            self._open_coach()
        elif event.key == pygame.K_ESCAPE:
            self.app.goto_menu()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        skin.draw_background(surface)
        sw = surface.get_width()
        cw = content_width()
        mx = MARGIN_X

        # ── Banner ────────────────────────────────────────────────────────────
        skin.draw_banner_title(surface, "Game Over", center_x=sw // 2, y=22, max_width=cw)

        # ── Score panel ───────────────────────────────────────────────────────
        lines = sorted(self.final_scores.items(), key=lambda kv: kv[1], reverse=True)
        if not lines:
            lines = [("—", 0)]

        has_metrics = self.metrics is not None
        row_h = _ROW_H_WITH_SUB if has_metrics else _ROW_H_SIMPLE
        score_panel_h = 45 + 8 + len(lines) * row_h + 10 + _PANEL_PAD
        score_panel = pygame.Rect(mx, 90, cw, score_panel_h)
        skin.draw_panel_titled(surface, score_panel, "Final Scores", style="wood")

        # Assign ranks (equal scores share the same rank)
        ranked: list[tuple[int, str, int]] = []
        prev_score: int | None = None
        prev_rank = 0
        for i, (pid, sc) in enumerate(lines):
            if sc != prev_score:
                prev_rank = i + 1
            ranked.append((prev_rank, pid, sc))
            prev_score = sc

        name_font  = body_font(_SCORE_NAME_PT)
        num_font   = body_font(_SCORE_NUM_PT)
        sub_font   = body_font(_SCORE_SUB_PT)
        badge_font = body_font(_BADGE_PT)

        badge_area_w = 40   # fixed width for rank badge column
        row_y = score_panel.y + 45 + 8

        for rank, pid, sc in ranked:
            rank_color = (
                _RANK_COLORS[rank - 1] if rank <= len(_RANK_COLORS) else colors.TEXT_MUTED
            )
            is_top = rank == 1

            # Subtle gold tint behind the winner row
            if is_top and len(ranked) > 1:
                hl = pygame.Surface((cw - 20, row_h), pygame.SRCALPHA)
                hl.fill((255, 205, 48, 22))
                surface.blit(hl, (mx + 10, row_y))

            # Rank badge
            badge_label = _RANK_LABELS[rank - 1] if rank <= len(_RANK_LABELS) else f"{rank}TH"
            badge_surf = badge_font.render(badge_label, True, rank_color)
            bx = mx + _PANEL_PAD
            by = row_y + (row_h // 2) - badge_surf.get_height() // 2
            surface.blit(badge_surf, (bx, by))

            # Player display name
            display   = self._display_name(pid)
            name_col  = rank_color if is_top else colors.TEXT_BODY
            name_surf = name_font.render(display, True, name_col)
            name_x    = mx + _PANEL_PAD + badge_area_w
            name_y    = row_y + 4
            surface.blit(name_surf, (name_x, name_y))

            # Resource score (right-aligned, large)
            num_surf = num_font.render(str(sc), True, rank_color)
            num_x = mx + cw - _PANEL_PAD - num_surf.get_width()
            num_y = row_y + (name_surf.get_height() - num_surf.get_height()) // 2 + 4
            surface.blit(num_surf, (num_x, num_y))

            # "resources" mini-label just left of the number
            res_surf = sub_font.render("resources", True, colors.TEXT_MUTED)
            res_x = num_x - res_surf.get_width() - 6
            res_y = num_y + num_surf.get_height() - res_surf.get_height() - 1
            old_clip = surface.get_clip()
            surface.set_clip(pygame.Rect(name_x, num_y, res_x - name_x - 4, num_surf.get_height() + 4))
            surface.blit(res_surf, (res_x, res_y))
            surface.set_clip(old_clip)

            # Sub-scores row (only when metrics available)
            if has_metrics and self.metrics:
                pd = self.metrics.get("players", {}).get(pid, {})
                if pd:
                    sc_block = pd.get("scores", {})
                    final_v  = sc_block.get("final", "—")
                    code_q   = sc_block.get("code_quality", "—")
                    gp_v     = sc_block.get("gameplay", "—")
                    sub_text = (
                        f"Final: {final_v} pts   Quality: {code_q}/100   Gameplay: {gp_v}/100"
                    )
                    sub_surf = sub_font.render(sub_text, True, colors.TEXT_MUTED)
                    sub_x = name_x
                    sub_y = name_y + name_surf.get_height() + 4
                    clip_w = res_x - sub_x - 8
                    old_clip = surface.get_clip()
                    surface.set_clip(pygame.Rect(sub_x, sub_y, max(0, clip_w), _SCORE_SUB_PT + 4))
                    surface.blit(sub_surf, (sub_x, sub_y))
                    surface.set_clip(old_clip)

            row_y += row_h

        # ── Session ID row ────────────────────────────────────────────────────
        session_y = score_panel.bottom + 8
        session_text = (
            f"Session: {self.session_dir.name}" if self.session_dir else "Session not saved"
        )
        sess_surf = body_font(_SESSION_PT).render(session_text, True, colors.TEXT_MUTED)
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(mx, session_y, cw, _SESSION_PT + 4))
        surface.blit(sess_surf, (sw // 2 - sess_surf.get_width() // 2, session_y))
        surface.set_clip(old_clip)

        # ── Analysis panel ────────────────────────────────────────────────────
        analysis_bottom = session_y + _SESSION_PT + 8
        analysis_sections = self._build_analysis_sections()

        if analysis_sections:
            analysis_y = session_y + _SESSION_PT + 10
            # Compute inner content height
            inner_h = 0
            for sec in analysis_sections:
                inner_h += sec["h"]
            teaser_h = 45 + inner_h + _PANEL_PAD
            teaser = pygame.Rect(mx, analysis_y, cw, teaser_h)
            content_rect = skin.draw_panel_titled(surface, teaser, "Analysis", style="parchment")

            ay = content_rect.y
            ax = content_rect.x
            aw = content_rect.width

            old_clip = surface.get_clip()
            surface.set_clip(pygame.Rect(ax - 4, ay, aw + 8, teaser_h))
            self._draw_analysis_sections(surface, analysis_sections, ax, ay, aw)
            surface.set_clip(old_clip)
            analysis_bottom = teaser.bottom

        # ── Action buttons ────────────────────────────────────────────────────
        btn_y = analysis_bottom + 20
        total_btn_w = (
            _BTN_W_PRIMARY  + _BTN_GAP
            + _BTN_W_SECONDARY + _BTN_GAP
            + _BTN_W_SECONDARY + _BTN_GAP
            + _BTN_W_SECONDARY
        )
        btn_x = sw // 2 - total_btn_w // 2

        self._play_again.rect   = pygame.Rect(btn_x, btn_y, _BTN_W_PRIMARY,   _BTN_H)
        btn_x += _BTN_W_PRIMARY + _BTN_GAP

        self._view_replay.rect  = pygame.Rect(btn_x, btn_y, _BTN_W_SECONDARY, _BTN_H)
        btn_x += _BTN_W_SECONDARY + _BTN_GAP

        self._coach_btn.rect    = pygame.Rect(btn_x, btn_y, _BTN_W_SECONDARY, _BTN_H)
        btn_x += _BTN_W_SECONDARY + _BTN_GAP

        self._open_results.rect = pygame.Rect(btn_x, btn_y, _BTN_W_SECONDARY, _BTN_H)

        self._widgets.draw(surface)

        # ── Footer ────────────────────────────────────────────────────────────
        foot_surf = body_font(FOOTER_PT).render(
            "Enter / Space  menu  ·  V  replay  ·  C  coach",
            True,
            colors.TEXT_MUTED,
        )
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(mx, footer_top() + 4, cw, FOOTER_PT + 8))
        surface.blit(foot_surf, (mx, footer_top() + 4))
        surface.set_clip(old_clip)

    # ── Analysis helpers ──────────────────────────────────────────────────────

    def _build_analysis_sections(self) -> list[dict]:
        """Build a list of section dicts describing analysis content and heights."""
        sections: list[dict] = []
        line_h = _ANALYSIS_PT + 8

        # Context line: scenario, seed, turns
        if self.replay_meta:
            scenario_raw = self.replay_meta.get("scenario", "")
            scenario_display = scenario_raw.replace("_", " ").title()
            seed    = self.replay_meta.get("seed", "?")
            n_turns = len(self.replay_meta.get("turns", []))
            ctx = f"Scenario: {scenario_display}   Seed: {seed}   {n_turns} turns played"
        elif self.session_dir:
            ctx = f"Session: {self.session_dir.name}"
        else:
            return sections

        sections.append({"type": "context", "text": ctx, "h": line_h + 4})

        # Per-player entries
        if self.metrics:
            players_dict = self.metrics.get("players", {})
            for i, (pid, pdata) in enumerate(players_dict.items()):
                display   = self._display_name(pid)
                sc_block  = pdata.get("scores", {})
                final_v   = sc_block.get("final", "—")
                code_q    = sc_block.get("code_quality", "—")
                gp_v      = sc_block.get("gameplay", "—")
                runtime   = pdata.get("runtime", {})
                crashes   = runtime.get("crash_count", 0)
                timeouts  = runtime.get("timeout_count", 0)
                avg_ms    = runtime.get("avg_turn_time_ms", None)

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
                hint = str(feedback[0]) if feedback else ""
                if len(hint) > 80:
                    hint = hint[:77] + "…"

                # Thin divider before players except the first
                if i > 0:
                    sections.append({"type": "divider", "h": 10})

                entry_h = line_h + (line_h if hint else 0)
                sections.append({
                    "type": "player",
                    "display": display,
                    "stats": stats_line,
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
        """Render analysis sections at (ax, ay) within available width aw."""
        af      = body_font(_ANALYSIS_PT)
        name_f  = body_font(_ANALYSIS_NAME_PT)
        line_h  = _ANALYSIS_PT + 8

        for sec in sections:
            if sec["type"] == "context":
                surf = af.render(sec["text"], True, colors.PARCHMENT_TEXT)
                surface.blit(surf, (ax, ay))
                ay += sec["h"]

            elif sec["type"] == "divider":
                div_y = ay + sec["h"] // 2
                pygame.draw.line(
                    surface, colors.PARCHMENT_EDGE,
                    (ax, div_y), (ax + aw, div_y),
                )
                ay += sec["h"]

            elif sec["type"] == "player":
                # Name label + stats on same line when it fits, else stacked
                name_surf = name_f.render(sec["display"] + ":", True, (72, 50, 18))
                name_w = name_surf.get_width() + 8
                surface.blit(name_surf, (ax, ay))

                stats_surf = af.render(sec["stats"], True, colors.PARCHMENT_TEXT)
                stats_x = ax + name_w
                avail = aw - name_w
                if stats_surf.get_width() > avail > 0:
                    # Truncate stats to fit
                    text = sec["stats"]
                    while len(text) > 1:
                        text = text[:-1]
                        candidate = af.render(text + "…", True, colors.PARCHMENT_TEXT)
                        if candidate.get_width() <= avail:
                            stats_surf = candidate
                            break
                surface.blit(stats_surf, (stats_x, ay))
                ay += line_h

                if sec["hint"]:
                    hint_surf = af.render(sec["hint"], True, (100, 78, 38))
                    surface.blit(hint_surf, (ax + 14, ay))
                    ay += line_h
