"""Replay viewer for stored session replay.json files."""

from __future__ import annotations

from pathlib import Path

import pygame

from engine.core.replay import ReplaySession, list_session_dirs, load_replay
from ui.render.hud import draw_centered_text, draw_hud, draw_toolbar_strip
from ui.render.map_renderer import draw_map
from ui.theme import (
    COLOR_BG,
    COLOR_MUTED,
    FOOTER_PT,
    MAP_TOP,
    MARGIN_X,
    TOOLBAR_HEIGHT,
    content_width,
    footer_top,
    hud_text_top,
    toolbar_top,
)
from ui.widgets import Button, ListRow, WidgetGroup


class ReplayScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.sessions: list[Path] = []
        self.selected = 0
        self.replay: ReplaySession | None = None
        self.error = ""
        self._pick_mode = True
        self._session_rows: list[ListRow] = []
        self._picker_widgets = WidgetGroup()
        self._transport = WidgetGroup()
        self._build_transport()

    def _build_transport(self) -> None:
        y = toolbar_top()
        btn_h = TOOLBAR_HEIGHT - 8
        btn_y = y + 4
        self._back_btn = Button(pygame.Rect(24, btn_y, 64, btn_h), "Back", on_click=self._step_back)
        self._fwd_btn = Button(pygame.Rect(96, btn_y, 64, btn_h), "Next", on_click=self._step_fwd)
        self._home_btn = Button(pygame.Rect(168, btn_y, 72, btn_h), "Home", on_click=self._go_home)
        self._end_btn = Button(pygame.Rect(248, btn_y, 72, btn_h), "End", on_click=self._go_end)
        self._menu_btn = Button(
            pygame.Rect(680, btn_y, 96, btn_h),
            "Menu",
            on_click=self._back_to_menu,
        )
        self._transport = WidgetGroup(
            [self._back_btn, self._fwd_btn, self._home_btn, self._end_btn, self._menu_btn]
        )

    def on_enter(self) -> None:
        self._pick_mode = self.replay is None
        if self._pick_mode:
            self.sessions = list_session_dirs(self.app.results_dir)
            self.selected = 0
            self.error = ""
            self._rebuild_picker()

    def _rebuild_picker(self) -> None:
        self._picker_widgets = WidgetGroup()
        self._session_rows = []
        y = 100
        row_w = content_width()
        for index, session in enumerate(self.sessions[:12]):
            row = ListRow(
                pygame.Rect(MARGIN_X, y, row_w, 28),
                session.name,
                selected=index == self.selected,
                on_click=lambda i=index: self._select_session(i),
            )
            self._session_rows.append(row)
            self._picker_widgets.add(row)
            y += 32

        load_btn = Button(
            pygame.Rect(48, y + 8, 120, 36),
            "Load",
            on_click=self._load_selected,
        )
        back_btn = Button(
            pygame.Rect(180, y + 8, 120, 36),
            "Back",
            on_click=lambda: self.app.goto_menu(),
        )
        self._picker_widgets.add(load_btn)
        self._picker_widgets.add(back_btn)

    def _select_session(self, index: int) -> None:
        self.selected = index
        for i, row in enumerate(self._session_rows):
            row.selected = i == index

    def _load_selected(self) -> None:
        if not self.sessions:
            return
        replay_path = self.sessions[self.selected] / "replay.json"
        self.open_path(replay_path)

    def open_path(self, path: Path) -> None:
        self.error = ""
        try:
            data = load_replay(path)
            self.replay = ReplaySession(data)
            self._pick_mode = False
            self.app.replay_path = path
        except (OSError, ValueError, KeyError) as exc:
            self.error = f"Could not load replay: {exc}"
            self.replay = None
            self._pick_mode = True

    def _step_back(self) -> None:
        if self.replay is not None:
            self.replay.step_backward()

    def _step_fwd(self) -> None:
        if self.replay is not None:
            self.replay.step_forward()

    def _go_home(self) -> None:
        if self.replay is not None:
            self.replay.reset()

    def _go_end(self) -> None:
        if self.replay is not None:
            self.replay.seek(self.replay.turn_count - 1)

    def _back_to_menu(self) -> None:
        self.replay = None
        self._pick_mode = True
        self.app.goto_menu()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._pick_mode:
            if self._picker_widgets.handle_event(event):
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w) and self.sessions:
                    self._select_session((self.selected - 1) % len(self.sessions))
                elif event.key in (pygame.K_DOWN, pygame.K_s) and self.sessions:
                    self._select_session((self.selected + 1) % len(self.sessions))
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._load_selected()
                elif event.key == pygame.K_ESCAPE:
                    self.app.goto_menu()
            return

        if self.replay is None:
            return

        if self._transport.handle_event(event):
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_SPACE):
            self._step_fwd()
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self._step_back()
        elif event.key == pygame.K_HOME:
            self._go_home()
        elif event.key == pygame.K_END:
            self._go_end()
        elif event.key == pygame.K_ESCAPE:
            self.replay = None
            self._pick_mode = True
            self.on_enter()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        if self._pick_mode:
            self._draw_picker(surface)
            return

        if self.replay is None:
            return

        render_state = self.replay.get_render_state()
        draw_map(surface, render_state, origin_y=MAP_TOP)

        names = render_state.get("display_names", {})
        idx = self.replay.turn_index
        total = self.replay.turn_count
        last = self.replay.last_turn
        action_line = ""
        if last is not None:
            student_name = names.get("student", "student")
            opponent_name = names.get("opponent", "opponent")
            action_line = (
                f"{student_name}={last.actions['student'].value} "
                f"{opponent_name}={last.actions['opponent'].value}"
            )

        labeled_scores = {
            names.get(pid, pid): score for pid, score in render_state["scores"].items()
        }
        labeled_final = {
            names.get(pid, pid): score
            for pid, score in self.replay.final_scores.items()
        }

        draw_hud(
            surface,
            title="Replay",
            lines=[
                f"Turn {idx + 1} / {total} · scores {labeled_scores}",
                action_line,
                f"Final (stored): {labeled_final}",
            ],
            y_offset=hud_text_top(),
        )
        draw_toolbar_strip(surface, y=toolbar_top(), height=TOOLBAR_HEIGHT)
        self._transport.draw(surface)
        footer = pygame.font.SysFont("consolas,courier,monospace", FOOTER_PT)
        surface.blit(
            footer.render(
                "Keyboard: ←/→ step · Home/End · Esc back",
                True,
                COLOR_MUTED,
            ),
            (24, footer_top() + 4),
        )

    def _draw_picker(self, surface: pygame.Surface) -> None:
        draw_centered_text(surface, ["Replay sessions"], y_start=40, size=26)

        if not self.sessions:
            draw_centered_text(
                surface,
                ["No sessions in results/", "Run a game first (Run on menu)"],
                y_start=120,
                color=COLOR_MUTED,
                size=16,
            )
        else:
            font = pygame.font.SysFont("consolas,courier,monospace", 16)
            surface.blit(font.render("Click a session, then Load", True, COLOR_MUTED), (MARGIN_X, 72))
            self._picker_widgets.draw(surface)

        footer = pygame.font.SysFont("consolas,courier,monospace", FOOTER_PT)
        surface.blit(
            footer.render("Keyboard: ↑↓ select · Enter load · Esc menu", True, COLOR_MUTED),
            (MARGIN_X, footer_top() + 4),
        )

        if self.error:
            draw_centered_text(surface, [self.error], y_start=360, color=(255, 120, 120), size=16)
