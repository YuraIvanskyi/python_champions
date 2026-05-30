"""HUD mentor portrait and bot card layout."""

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


def test_bot_name_truncation_and_card_width() -> None:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame

    from ui.render.hud import HudBotEntry, _BOT_NAME_MAX, _bot_card_width, _truncate_name
    from ui.skin.typography import body_font

    pygame.font.init()

    long_name = "A" * 40
    truncated = _truncate_name(long_name)
    assert len(truncated) <= _BOT_NAME_MAX
    assert truncated.endswith("…")

    name_font = body_font(13)
    score_font = body_font(13)
    action_font = body_font(12)
    short_entry = HudBotEntry("Rookie", None, "Score: 0", "WAIT")
    long_action_entry = HudBotEntry(
        "Rookie",
        None,
        "Score: 0",
        "Sandbox error - turn forfeited (WAIT)",
    )
    short_w = _bot_card_width(
        short_entry, name_font=name_font, score_font=score_font, action_font=action_font,
    )
    long_action_w = _bot_card_width(
        long_action_entry, name_font=name_font, score_font=score_font, action_font=action_font,
    )
    long_name_entry = HudBotEntry(long_name, None, "Score: 0", "WAIT")
    long_name_w = _bot_card_width(
        long_name_entry, name_font=name_font, score_font=score_font, action_font=action_font,
    )
    assert long_action_w >= short_w
    assert long_name_w >= short_w
    assert long_action_w >= action_font.size(long_action_entry.action_line)[0]


def test_hud_header_line_includes_turn() -> None:
    from ui.render.hud import hud_header_line

    header = hud_header_line(title="Resource Wars", seed=7, turn=17, lang="en")
    assert "Resource Wars" in header
    assert "Seed 7" in header
    assert "Turn 17" in header


def test_build_hud_bot_entries_uses_entity_order() -> None:
    from ui.render.hud import build_hud_bot_entries

    render_state = {
        "entities": [
            {"id": "b", "display_name": "Beta"},
            {"id": "a", "display_name": "Alpha"},
        ],
        "scores": {"a": 3, "b": 1},
        "display_names": {"a": "Alpha", "b": "Beta"},
    }
    entries = build_hud_bot_entries(render_state, None, lang="en")
    assert [entry.name for entry in entries] == ["Beta", "Alpha"]
    assert entries[0].score_line == "Score: 1"
    assert entries[1].action_line == "—"
