"""Sandbox enforces wall-clock timeout on runaway bots."""

from pathlib import Path

from engine.core.action import Action
from engine.core.config import load_config
from engine.sandbox.runner import SandboxedBot


def test_infinite_loop_bot_times_out() -> None:
    config = load_config()
    config.engine.turn_timeout_ms = 200
    bot_path = Path("tests/fixtures/infinite_bot.py")
    game_state = {
        "position": [0, 0],
        "resources": 0,
        "on_resource": False,
        "map_width": 8,
        "map_height": 8,
        "visible_tiles": [],
    }
    sandbox = SandboxedBot(bot_path, config)
    try:
        action, events = sandbox.run_turn(game_state)
    finally:
        sandbox.close()
    assert action is Action.WAIT
    assert any("sandbox_timeout" in e for e in events)
