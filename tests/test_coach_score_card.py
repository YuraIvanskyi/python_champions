"""Code Coach score card mentor layout."""

from __future__ import annotations

import os


def test_score_card_offsets_text_for_mentor() -> None:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame

    from ui.render.quest_card import _mentor2_surface, score_card_text_column

    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1), flags=pygame.NOFRAME)

    rect = pygame.Rect(0, 0, 380, 116)
    text_x, text_w = score_card_text_column(rect)
    mentor = _mentor2_surface(rect.height - 16)

    assert mentor is not None
    assert text_x > 12
    assert text_w < rect.width - 40

    greeting = "Lets see your results, Explorer!"
    from ui.render.quest_card import _wrap_text
    from ui.skin.typography import body_font

    font = body_font(14)
    lines = _wrap_text(greeting, font, text_w)
    assert lines
    assert "Explorer" in lines[0]
