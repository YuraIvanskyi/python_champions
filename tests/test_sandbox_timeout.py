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
        action, events, _elapsed_ms = sandbox.run_turn(game_state)
    finally:
        sandbox.close()
    assert action is Action.WAIT
    assert any("sandbox_timeout" in e for e in events)


_STATE = {
    "position": [0, 0],
    "resources": 0,
    "on_resource": False,
    "map_width": 8,
    "map_height": 8,
    "visible_tiles": [],
}


def test_student_print_does_not_desync_protocol() -> None:
    config = load_config()
    config.engine.turn_timeout_ms = 2000
    sandbox = SandboxedBot(Path("tests/fixtures/printing_bot.py"), config)
    try:
        for _ in range(6):
            action, events, _elapsed_ms = sandbox.run_turn(_STATE)
            assert action is Action.WAIT
            assert events == []
    finally:
        sandbox.close()


def test_first_turn_budget_excludes_worker_startup() -> None:
    config = load_config()
    config.engine.turn_timeout_ms = 2000
    sandbox = SandboxedBot(Path("tests/fixtures/printing_bot.py"), config)
    try:
        # The ready handshake already happened in __init__; turn 1 only pays for make_turn.
        assert sandbox._proc is not None and sandbox._proc.poll() is None
        _action, events, elapsed_ms = sandbox.run_turn(_STATE)
    finally:
        sandbox.close()
    assert events == []
    assert elapsed_ms < 1000
