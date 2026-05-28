"""AST-based movement heuristic tests."""

from __future__ import annotations

from pathlib import Path

from engine.analysis.static import analyze_movement_static


# ---------------------------------------------------------------------------
# Fixture bot sources
# ---------------------------------------------------------------------------

_CONSTANT_RETURN = """\
def make_turn(state):
    return "MOVE_RIGHT"
"""

_GOOD_BOT = """\
def make_turn(state):
    if state.can_gather():
        return "GATHER"
    nearest = state.nearest_pool()
    if nearest:
        nx, ny = nearest
        if state.is_walkable(nx, state.my_y()):
            return "MOVE_RIGHT"
    return "WAIT"
"""

_NO_GOAL = """\
def make_turn(state):
    if state.is_walkable(state.my_x() + 1, state.my_y()):
        return "MOVE_RIGHT"
    return "WAIT"
"""

_NO_WALKABLE = """\
def make_turn(state):
    nearest = state.nearest_pool()
    if nearest:
        nx, ny = nearest
        if nx > state.my_x():
            return "MOVE_RIGHT"
    return "WAIT"
"""

_NO_FALLBACK = """\
def make_turn(state):
    nearest = state.nearest_pool()
    if nearest:
        nx, ny = nearest
        if nx > state.my_x():
            return "MOVE_RIGHT"
        if nx < state.my_x():
            return "MOVE_LEFT"
    return "GATHER"
"""


def _write(tmp_path: Path, name: str, source: str) -> Path:
    p = tmp_path / name
    p.write_text(source, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_constant_return_flagged(tmp_path: Path) -> None:
    path = _write(tmp_path, "bot.py", _CONSTANT_RETURN)
    result = analyze_movement_static(path)
    assert result["constant_action_return"] is True


def test_good_bot_not_flagged(tmp_path: Path) -> None:
    path = _write(tmp_path, "bot.py", _GOOD_BOT)
    result = analyze_movement_static(path)
    assert result["constant_action_return"] is False
    assert result["no_walkable_check"] is False
    assert result["no_target_logic"] is False


def test_no_goal_flagged(tmp_path: Path) -> None:
    path = _write(tmp_path, "bot.py", _NO_GOAL)
    result = analyze_movement_static(path)
    assert result["no_target_logic"] is True


def test_no_walkable_check_flagged(tmp_path: Path) -> None:
    path = _write(tmp_path, "bot.py", _NO_WALKABLE)
    result = analyze_movement_static(path)
    assert result["no_walkable_check"] is True


def test_missing_fallback_flagged(tmp_path: Path) -> None:
    path = _write(tmp_path, "bot.py", _NO_FALLBACK)
    result = analyze_movement_static(path)
    # No WAIT returned and uses goal logic → missing_fallback
    assert result["missing_fallback"] is True


def test_make_turn_line_recorded(tmp_path: Path) -> None:
    path = _write(tmp_path, "bot.py", _GOOD_BOT)
    result = analyze_movement_static(path)
    assert result["make_turn_line"] == 1  # first line of make_turn


def test_syntax_error_returns_safe_defaults(tmp_path: Path) -> None:
    path = _write(tmp_path, "broken.py", "def make_turn(state:\n    return 'WAIT'")
    result = analyze_movement_static(path)
    assert result["constant_action_return"] is False
    assert result["no_walkable_check"] is False
    assert result["make_turn_line"] is None


def test_constant_return_also_sets_no_walkable(tmp_path: Path) -> None:
    """A trivially constant bot also has no walkable check and no target logic."""
    path = _write(tmp_path, "bot.py", _CONSTANT_RETURN)
    result = analyze_movement_static(path)
    assert result["no_walkable_check"] is True
    assert result["no_target_logic"] is True
