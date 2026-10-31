"""Regression tests for ISS-064 .. ISS-071 (Code Coach accuracy)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from engine.analysis.feedback import generate_feedback_items
from engine.analysis.movement import MovementConfig, _compute_metrics
from engine.analysis.runtime import RuntimeCollector
from engine.analysis.static import analyze_static
from engine.core.action import Action
from engine.i18n import plural_suffix, translate
from engine.i18n.feedback_strings import (
    DEFAULT_GOAL_HELPERS,
    SCENARIO_GATHER_CHECK,
    SCENARIO_GOAL_HELPERS,
)
from engine.i18n.messages_en import MESSAGES_EN
from engine.i18n.messages_uk import MESSAGES_UK
from engine.simulation.map import TileType
from engine.student_api import GameView
from engine.student_api.boss_fight_view import BossFightView
from engine.student_api.mana_pools_view import ManaPoolsView
from scenarios.mana_pools.game import ManaPoolsScenario
from scenarios.resource_wars.game import ResourceWarsScenario

CFG = MovementConfig()


def _analyze(tmp_path: Path, source: str):
    path = tmp_path / "bot.py"
    path.write_text(source, encoding="utf-8")
    return analyze_static(path, ruff_select=["E", "F", "W"], forbidden_names=[], enabled=True)


def _items(static=None, runtime=None, movement=None, **kw):
    return generate_feedback_items(
        static=static or {}, runtime=runtime or {}, movement=movement or {},
        movement_cfg=CFG, **kw,
    )


# -- ISS-064 -----------------------------------------------------------------

def test_profile_constants_not_reported_as_unused(tmp_path: Path) -> None:
    metrics = _analyze(
        tmp_path,
        'BOT_DISPLAY_NAME = "Ada"\nBOT_ICON_INDEX = 7\nBOT_ICON = "x"\n\n\n'
        'def make_turn(state):\n    return "WAIT"\n',
    )
    assert metrics.unused_names == []


def test_real_unused_module_name_still_reported(tmp_path: Path) -> None:
    metrics = _analyze(tmp_path, 'LIMIT = 3\n\n\ndef make_turn(state):\n    return "WAIT"\n')
    assert metrics.unused_names == ["LIMIT"]


# -- ISS-065 -----------------------------------------------------------------

@pytest.mark.parametrize("lang", ["en", "uk"])
def test_f821_and_f841_get_different_cards(lang: str) -> None:
    def card(code: str):
        static = {"ruff": [{"code": code, "line": 3, "message": "m"}]}
        return next(i for i in _items(static=static, language=lang) if i.category == "style")

    undefined, unused = card("F821"), card("F841")
    assert undefined.title != unused.title
    assert undefined.fix_hint != unused.fix_hint
    if lang == "en":
        assert "Undefined" in undefined.title
        assert "Delete" not in undefined.fix_hint
        assert "Unused" in unused.title


# -- ISS-066 -----------------------------------------------------------------

def test_empty_translation_is_not_treated_as_missing() -> None:
    assert translate("feedback.plural.one", lang="en") == ""
    assert translate("feedback.plural.one", lang="uk") == ""


@pytest.mark.parametrize(
    ("count", "suffix"),
    [(1, ""), (2, "и"), (4, "и"), (5, "ів"), (11, "ів"),
     (12, "ів"), (21, ""), (22, "и"), (25, "ів")],
)
def test_ukrainian_plural_forms(count: int, suffix: str) -> None:
    assert plural_suffix(count, lang="uk") == suffix


def test_english_plural_forms() -> None:
    assert plural_suffix(1) == ""
    assert plural_suffix(2) == "s"


@pytest.mark.parametrize("lang", ["en", "uk"])
@pytest.mark.parametrize("count", [1, 2, 5])
def test_stuck_card_never_leaks_keys_or_placeholders(lang: str, count: int) -> None:
    mv = {"analyzed": True, "stuck_episodes": count, "oscillation_episodes": count}
    for item in _items(movement=mv, language=lang):
        assert "feedback." not in item.message
        assert "{" not in item.message


def test_missing_format_argument_does_not_leak_placeholder() -> None:
    text = translate("feedback.stuck.message", lang="uk", count=3)
    assert "{" not in text


# -- ISS-067 -----------------------------------------------------------------

def _two_bot_resource_wars() -> ResourceWarsScenario:
    s = ResourceWarsScenario(seed=1, player_ids=["a", "b"])
    s.setup()
    for y in range(s._map.height):
        for x in range(s._map.width):
            s._map.set_tile(x, y, TileType.EMPTY)
    return s


def test_blocked_event_names_the_cause() -> None:
    s = _two_bot_resource_wars()
    s._entities["a"].x, s._entities["a"].y = 0, 0
    s._entities["b"].x, s._entities["b"].y = 3, 3
    s._map.set_tile(1, 0, TileType.OBSTACLE)

    assert "a_blocked_by_edge" in s.apply_turn({"a": Action.MOVE_LEFT, "b": Action.WAIT}).events
    assert "a_blocked_by_obstacle" in s.apply_turn({"a": Action.MOVE_RIGHT, "b": Action.WAIT}).events
    s._entities["b"].x, s._entities["b"].y = 0, 1
    events = s.apply_turn({"a": Action.MOVE_DOWN, "b": Action.WAIT}).events
    assert "a_blocked" in events and "a_blocked_by_unit" in events


def test_simultaneous_entry_is_a_conflict_not_a_unit() -> None:
    s = _two_bot_resource_wars()
    s._entities["a"].x, s._entities["a"].y = 2, 3
    s._entities["b"].x, s._entities["b"].y = 4, 3
    events = s.apply_turn({"a": Action.MOVE_RIGHT, "b": Action.MOVE_LEFT}).events
    assert "a_moved" in events
    assert "b_blocked_by_conflict" in events


def test_mana_pools_pool_and_conflict_causes() -> None:
    s = ManaPoolsScenario(seed=7, player_ids=["p1", "p2"])
    s.setup()
    for y in range(s._map.height):
        for x in range(s._map.width):
            s._map.set_tile(x, y, TileType.EMPTY)
    s._pool_capacities.clear()
    s._positions["p1"] = (2, 3)
    s._positions["p2"] = (4, 3)
    events = s.apply_turn({"p1": Action.MOVE_RIGHT, "p2": Action.MOVE_LEFT}).events
    assert "p2_blocked_by_conflict" in events
    s._map.set_tile(5, 3, TileType.POOL)
    s._pool_capacities[(5, 3)] = 3
    events = s.apply_turn({"p1": Action.WAIT, "p2": Action.MOVE_RIGHT}).events
    assert "p2_blocked_by_obstacle" in events


def _blocked_turns(cause: str, n: int = 6) -> list[dict]:
    return [
        {"turn": i + 1, "actions": {"p": "MOVE_UP"}, "scores": {"p": 0},
         "events": ["p_blocked", f"p_blocked_by_{cause}"]}
        for i in range(n)
    ]


def test_movement_metrics_count_blocked_causes() -> None:
    m = _compute_metrics(_blocked_turns("unit"), [None] * 6, "p", CFG)
    assert m.blocked_causes == {"unit": 6}


@pytest.mark.parametrize(
    ("cause", "needle"),
    [("unit", "is_free"), ("conflict", "same cell"), ("edge", "is_inside"), ("obstacle", "is_walkable")],
)
def test_blocked_card_follows_dominant_cause(cause: str, needle: str) -> None:
    mv = {"analyzed": True, "blocked_move_ratio": 0.8, "blocked_causes": {cause: 9, "obstacle": 1}}
    item = next(i for i in _items(movement=mv) if "blocked" in i.title.lower())
    assert needle in item.message + item.fix_hint


def test_blocked_card_without_cause_data_keeps_obstacle_wording() -> None:
    mv = {"analyzed": True, "blocked_move_ratio": 0.8}
    item = next(i for i in _items(movement=mv) if "blocked" in i.title.lower())
    assert "obstacles" in item.message


# -- ISS-068 -----------------------------------------------------------------

def test_api_names_in_catalogs_exist_on_views() -> None:
    api = set()
    for cls in (GameView, ManaPoolsView, BossFightView):
        api |= {n for n in dir(cls) if not n.startswith("_")}
    texts = [*MESSAGES_EN.values(), *MESSAGES_UK.values()]
    texts += [*SCENARIO_GOAL_HELPERS.values(), DEFAULT_GOAL_HELPERS, *SCENARIO_GATHER_CHECK.values()]
    mentioned = {m for t in texts for m in re.findall(r"state\.(\w+)\(", t)}
    assert mentioned, "expected the catalogs to mention student API calls"
    assert mentioned <= api, f"unknown API in hints: {sorted(mentioned - api)}"


@pytest.mark.parametrize("scenario_id", ["resource_wars", "mana_pools", "boss_fight", None])
def test_goal_hints_are_scenario_aware(scenario_id: str | None) -> None:
    static = {"movement": {"no_target_logic": True, "make_turn_line": 3}}
    item = next(i for i in _items(static=static, scenario_id=scenario_id) if "goal" in i.title.lower())
    assert "nearest_station" not in item.message + item.fix_hint
    expected = SCENARIO_GOAL_HELPERS.get(scenario_id or "", DEFAULT_GOAL_HELPERS)
    assert expected in item.fix_hint


# -- ISS-069 -----------------------------------------------------------------

def _view_data(**extra):
    tiles = [{"x": x, "y": y, "type": "empty"} for x in range(4) for y in range(4)]
    tiles.append({"x": 3, "y": 3, "type": "obstacle"})
    tiles.append({"x": 0, "y": 3, "type": "pool"})
    data = {
        "position": [0, 0], "map_width": 4, "map_height": 4, "visible_tiles": tiles,
        "others": {"rival": [1, 0]},
    }
    data.update(extra)
    return data


def test_is_free_accounts_for_units_unlike_is_walkable() -> None:
    view = GameView(_view_data())
    assert view.is_walkable(1, 0) and not view.is_free(1, 0)
    assert view.is_free(0, 1)
    assert not view.is_free(3, 3) and not view.is_free(-1, 0)
    assert not view.is_free(0, 3)  # pool


def test_boss_cell_is_not_free() -> None:
    view = BossFightView(_view_data(boss_position={"x": 2, "y": 2}))
    assert view.is_walkable(2, 2) and not view.is_free(2, 2)
    assert view.is_free(0, 1)


# -- ISS-070 / ISS-071 -------------------------------------------------------

def test_failed_gather_counted_identically_in_both_scenarios() -> None:
    rw = [{"turn": i + 1, "actions": {"p": "GATHER"}, "scores": {"p": 0},
           "events": ["p_gather_failed"]} for i in range(5)]
    mp = [{"turn": i + 1, "actions": {"p": "GATHER"}, "scores": {"p": 0},
           "events": ["p_gather_failed_not_adjacent" if i % 2 else "p_gather_failed_no_capacity"]}
          for i in range(5)]
    for turns in (rw, mp):
        m = _compute_metrics(turns, [None] * 5, "p", CFG)
        assert m.failed_gather_count == 5
        assert m.failed_gather_turns == [1, 2, 3, 4, 5]


def test_failed_gather_does_not_touch_invalid_action_count() -> None:
    collector = RuntimeCollector()
    collector.record_turn(events=["invalid_action:bad"], turn_time_ms=1.0, player_id="p")
    collector.record_turn(events=["p_gather_failed"], turn_time_ms=1.0, player_id="p")
    assert collector.metrics.invalid_action_count == 1


@pytest.mark.parametrize(
    ("scenario_id", "check"),
    [("resource_wars", "on_resource"), ("mana_pools", "can_gather")],
)
def test_wasted_gather_card(scenario_id: str, check: str) -> None:
    mv = {"analyzed": True, "failed_gather_count": 4, "failed_gather_turns": [2, 5, 9, 12]}
    item = next(i for i in _items(movement=mv, scenario_id=scenario_id) if "GATHER" in i.title)
    assert "4 times" in item.message and "2, 5, 9, 12" in item.message
    assert check in item.fix_hint


def test_no_wasted_gather_card_below_threshold() -> None:
    mv = {"analyzed": True, "failed_gather_count": 1, "failed_gather_turns": [2]}
    assert not any("GATHER" in i.title for i in _items(movement=mv))


def test_idle_turns_card() -> None:
    mv = {"analyzed": True, "wait_ratio": 0.6}
    item = next(i for i in _items(movement=mv) if "idle" in i.title.lower())
    assert "60%" in item.message
    low = {"analyzed": True, "wait_ratio": 0.1}
    assert not any("idle" in i.title.lower() for i in _items(movement=low))
