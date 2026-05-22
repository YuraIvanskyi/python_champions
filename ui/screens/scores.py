"""End-of-game score screen — RPG launcher visual redesign."""

from __future__ import annotations

import json
import os
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
_SCORE_PT = 22
_SESSION_PT = 13
_ANALYSIS_PT = 14
_BTN_H = 46
_BTN_W_PRIMARY = 180
_BTN_W_SECONDARY = 148
_BTN_GAP = 12


class ScoresScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.final_scores: dict[str, int] = {}
        self.session_dir: Path | None = None
        self.metrics: dict | None = None

        # Buttons — rects are repositioned each draw() based on content height
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

    def set_results(self, final_scores: dict[str, int], session_dir: Path | None) -> None:
        self.final_scores = final_scores
        self.session_dir = session_dir
        self.metrics = None
        if session_dir is not None:
            metrics_path = session_dir / "metrics.json"
            if metrics_path.is_file():
                self.metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        has_replay = session_dir is not None and (session_dir / "replay.json").is_file()
        self._view_replay.enabled = has_replay
        self._coach_btn.enabled = self.metrics is not None

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

    def draw(self, surface: pygame.Surface) -> None:
        skin.draw_background(surface)
        sw = surface.get_width()
        cw = content_width()
        mx = MARGIN_X

        # ── Banner ─────────────────────────────────────────────────────────────
        skin.draw_banner_title(surface, "Game Over", center_x=sw // 2, y=22, max_width=cw)

        # ── Score panel ────────────────────────────────────────────────────────
        n_scores = max(1, len(self.final_scores))
        score_panel_h = max(100, min(220, _PANEL_PAD * 2 + n_scores * (_SCORE_PT + 14) + 20))
        score_panel = pygame.Rect(mx, 90, cw, score_panel_h)
        skin.draw_panel_titled(surface, score_panel, "Final Scores", style="wood")

        # Score lines — centered, gold, large
        lines = sorted(self.final_scores.items(), key=lambda kv: kv[1], reverse=True)
        if not lines:
            lines = [("No scores recorded", 0)]

        score_font = body_font(_SCORE_PT)
        # Center block of score lines vertically inside the panel
        total_block_h = len(lines) * (_SCORE_PT + 12)
        score_block_y = score_panel.y + 45 + (score_panel_h - 45 - total_block_h) // 2

        for _rank, (player, score) in enumerate(lines):
            line_text = f"{player}  —  {score}"
            line_surf = score_font.render(line_text, True, colors.GOLD_TEXT)
            line_x = sw // 2 - line_surf.get_width() // 2
            old_clip = surface.get_clip()
            surface.set_clip(pygame.Rect(mx + 8, score_block_y, cw - 16, _SCORE_PT + 6))
            surface.blit(line_surf, (line_x, score_block_y))
            surface.set_clip(old_clip)
            score_block_y += _SCORE_PT + 12

        # ── Session row ────────────────────────────────────────────────────────
        session_y = score_panel.bottom + 10
        session_text = (
            f"Session: {self.session_dir.name}" if self.session_dir else "Session not saved"
        )
        sess_surf = body_font(_SESSION_PT).render(session_text, True, colors.TEXT_MUTED)
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(mx, session_y, cw, _SESSION_PT + 4))
        surface.blit(sess_surf, (sw // 2 - sess_surf.get_width() // 2, session_y))
        surface.set_clip(old_clip)

        # ── Analysis teaser ────────────────────────────────────────────────────
        analysis_lines: list[str] = []
        if self.metrics:
            block = self.metrics
            if "players" in self.metrics:
                players_dict = self.metrics["players"]
                if players_dict:
                    first_id = next(iter(players_dict))
                    block = players_dict[first_id]
                    if len(players_dict) > 1:
                        analysis_lines.append(
                            f"Analysis for {first_id} ({len(players_dict)} bots) — open Code Coach"
                        )
            scores_block = block.get("scores", {})
            final = scores_block.get("final", "—")
            code_q = scores_block.get("code_quality", "—")
            analysis_lines.append(f"Final score: {final}  ·  Code quality: {code_q}")
            feedback = block.get("feedback", [])
            if feedback:
                hint = str(feedback[0])
                if len(hint) > 90:
                    hint = hint[:87] + "…"
                analysis_lines.append(hint)

        analysis_bottom = session_y + _SESSION_PT + 8
        if analysis_lines:
            analysis_y = session_y + _SESSION_PT + 10
            teaser_h = _PANEL_PAD * 2 + 28 + len(analysis_lines) * (_ANALYSIS_PT + 10)
            teaser = pygame.Rect(mx, analysis_y, cw, teaser_h)
            skin.draw_panel_titled(surface, teaser, "Analysis", style="parchment")
            analysis_font = body_font(_ANALYSIS_PT)
            ay = analysis_y + 45
            old_clip = surface.get_clip()
            surface.set_clip(pygame.Rect(mx + 8, ay, cw - 16, teaser_h - 50))
            for line in analysis_lines[:3]:
                asurf = analysis_font.render(line, True, colors.PARCHMENT_TEXT)
                surface.blit(asurf, (mx + _PANEL_PAD, ay))
                ay += _ANALYSIS_PT + 10
            surface.set_clip(old_clip)
            analysis_bottom = teaser.bottom

        # ── Action buttons ─────────────────────────────────────────────────────
        # Adaptive: always placed just below the content, centred horizontally
        btn_y = analysis_bottom + 20
        total_btn_w = (
            _BTN_W_PRIMARY + _BTN_GAP
            + _BTN_W_SECONDARY + _BTN_GAP
            + _BTN_W_SECONDARY + _BTN_GAP
            + _BTN_W_SECONDARY
        )
        btn_x = sw // 2 - total_btn_w // 2

        self._play_again.rect = pygame.Rect(btn_x, btn_y, _BTN_W_PRIMARY, _BTN_H)
        btn_x += _BTN_W_PRIMARY + _BTN_GAP

        self._view_replay.rect = pygame.Rect(btn_x, btn_y, _BTN_W_SECONDARY, _BTN_H)
        btn_x += _BTN_W_SECONDARY + _BTN_GAP

        self._coach_btn.rect = pygame.Rect(btn_x, btn_y, _BTN_W_SECONDARY, _BTN_H)
        btn_x += _BTN_W_SECONDARY + _BTN_GAP

        self._open_results.rect = pygame.Rect(btn_x, btn_y, _BTN_W_SECONDARY, _BTN_H)

        self._widgets.draw(surface)

        # ── Footer ─────────────────────────────────────────────────────────────
        foot_surf = body_font(FOOTER_PT).render(
            "Enter / Space  menu  ·  V  replay  ·  C  coach",
            True,
            colors.TEXT_MUTED,
        )
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(mx, footer_top() + 4, cw, FOOTER_PT + 8))
        surface.blit(foot_surf, (mx, footer_top() + 4))
        surface.set_clip(old_clip)
