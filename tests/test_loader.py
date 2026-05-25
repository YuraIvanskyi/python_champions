"""Student bot loader tests."""

from pathlib import Path

from engine.core.loader import load_bot


def test_load_example_bot() -> None:
    bot = load_bot(Path("student_bots/resource_wars/example_bot.py"))
    assert bot.player.is_student
    assert bot.player.display_name == "Explorer"
    assert bot.make_turn is not None
    state = {
        "position": [0, 0],
        "resources": 0,
        "on_resource": False,
        "map_width": 8,
        "map_height": 8,
        "visible_tiles": [],
    }
    action = bot.make_turn(state)
    assert action in {
        "MOVE_UP",
        "MOVE_DOWN",
        "MOVE_LEFT",
        "MOVE_RIGHT",
        "GATHER",
        "WAIT",
    }
