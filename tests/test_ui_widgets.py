"""Widget hit-test geometry without a display."""

from __future__ import annotations

import pygame

from ui.widgets import Button, ListRow, TextField


def test_button_click_inside_rect() -> None:
    pygame.init()
    clicked: list[bool] = []

    btn = Button(pygame.Rect(10, 10, 80, 36), "Go", on_click=lambda: clicked.append(True))
    down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (40, 20), "button": 1})
    up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (40, 20), "button": 1})
    assert btn.handle_event(down)
    btn.handle_event(up)
    assert clicked


def test_button_miss_outside_rect() -> None:
    pygame.init()
    clicked: list[bool] = []
    btn = Button(pygame.Rect(10, 10, 80, 36), "Go", on_click=lambda: clicked.append(True))
    down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (200, 200), "button": 1})
    assert not btn.handle_event(down)
    assert not clicked


def test_list_row_select() -> None:
    pygame.init()
    selected: list[int] = []
    row = ListRow(
        pygame.Rect(0, 0, 200, 28),
        "Resource Wars",
        on_click=lambda: selected.append(1),
    )
    up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (10, 10), "button": 1})
    assert row.handle_event(up)
    assert selected == [1]


def test_text_field_types() -> None:
    pygame.init()
    current = "a"

    def on_change(text: str) -> None:
        nonlocal current
        current = text

    field = TextField(pygame.Rect(0, 0, 200, 36), text=current, on_change=on_change)
    field.focused = True
    key = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_b, "unicode": "b"})
    field.handle_event(key)
    assert current == "ab"
