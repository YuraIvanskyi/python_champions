"""HUD mentor portrait layout."""

from __future__ import annotations

import os


def test_hud_mentor_offsets_text_column() -> None:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame

    from ui.render.hud import _hud_text_column, _mentor_surface, _wrap_text

    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1), flags=pygame.NOFRAME)

    panel = pygame.Rect(0, 0, 1024, 128)
    text_x, text_w, mentor = _hud_text_column(panel)
    assert mentor is not None
    assert text_x > 16
    assert text_w < panel.width - 32

    font = pygame.font.SysFont("consolas", 16)
    long_line = "Turn 7 · Explorer: 1 · Rookie: 0 · Last: Rookie=WAIT Explorer=MOVE_DOWN"
    wrapped = _wrap_text(long_line, font, min(text_w, 320))
    assert len(wrapped) >= 2
    for line in wrapped:
        assert font.size(line)[0] <= min(text_w, 320) + 2

    scaled = _mentor_surface(panel.height - 12)
    assert scaled is not None
    assert scaled.get_height() <= panel.height - 12
