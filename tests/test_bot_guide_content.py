"""Bot guide content and layout helpers."""

from ui.bot_guide_content import guide_blocks_for_scenario
from ui.bot_guide_layout import measure_guide_content


def test_guide_blocks_all_scenarios() -> None:
    for sid in ("resource_wars", "boss_fight", "energy_stations"):
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
    for sid in ("resource_wars", "boss_fight", "energy_stations"):
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
    blocks = guide_blocks_for_scenario("resource_wars")
    h = measure_guide_content(blocks, content_width=800)
    assert h > 200
    pygame.quit()


def test_unknown_scenario_falls_back_to_resource_wars() -> None:
    blocks = guide_blocks_for_scenario("unknown_xyz")
    rw = guide_blocks_for_scenario("resource_wars")
    assert blocks[0].text == rw[0].text
