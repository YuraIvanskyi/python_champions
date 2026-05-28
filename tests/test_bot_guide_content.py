"""Bot guide content and layout helpers."""

from ui.bot_guide_content import guide_blocks_for_scenario
from ui.bot_guide_layout import measure_guide_content


def test_guide_blocks_all_scenarios() -> None:
    for sid in ("resource_wars", "boss_fight", "mana_pools"):
        blocks = guide_blocks_for_scenario(sid)
        assert blocks
        assert any(b.kind == "code" for b in blocks)
        assert not any("def make_turn" in b.text and b.kind != "code" for b in blocks)
        joined = "\n".join(
            line for b in blocks if b.kind == "code" for line in b.lines
        )
        assert '"MOVE_UP"' in joined
        assert "state.my_" in joined or "state.can_gather" in joined
        assert "API" not in "\n".join(
            (b.text for b in blocks if b.kind in ("heading", "paragraph"))
        )


def test_guide_boilerplate_no_working_logic() -> None:
    for sid in ("resource_wars", "boss_fight", "mana_pools"):
        code_lines = [
            line
            for b in guide_blocks_for_scenario(sid)
            if b.kind == "code"
            for line in b.lines
        ]
        joined = "\n".join(code_lines)
        assert 'return "' not in joined
        assert "if state." not in joined
        assert "for " not in joined


def test_measure_guide_content_positive() -> None:
    import os

    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame

    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1), flags=pygame.NOFRAME)
    blocks = guide_blocks_for_scenario("resource_wars")
    h = measure_guide_content(blocks, content_width=800)
    assert h > 200


def test_guide_mentor_float_wraps_intro() -> None:
    import os

    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame

    from ui.bot_guide_layout import _mentor_float_rect, _wrap_text, _width_at
    from ui.skin import typography

    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1), flags=pygame.NOFRAME)
    typography._game_cache.clear()
    typography._code_cache.clear()
    font = pygame.font.SysFont("consolas", 15)
    for sid in ("resource_wars", "boss_fight", "mana_pools"):
        blocks = guide_blocks_for_scenario(sid)
        float_rect = _mentor_float_rect(blocks, content_width=700, start_y=0)
        assert float_rect is not None
        assert float_rect.width > 100
        intro = blocks[1].text
        width_at = _width_at(700, float_rect, font.get_height() + 2)
        lines = _wrap_text(
            intro,
            font,
            start_y=float_rect.top,
            line_h=font.get_height() + 2,
            width_at=width_at,
        )
        assert len(lines) >= 2
        narrow_w = 700 - float_rect.width - 14
        assert font.size(lines[0])[0] <= narrow_w + 2


def test_unknown_scenario_falls_back_to_resource_wars() -> None:
    blocks = guide_blocks_for_scenario("unknown_xyz")
    rw = guide_blocks_for_scenario("resource_wars")
    assert blocks[0].text == rw[0].text
