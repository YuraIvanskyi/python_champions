"""Resource Wars multi-student (Phase 2.7) rules."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from engine.core.action import Action
from engine.core.config import load_config
from engine.core.live_game import LiveGame
from engine.core.loader import load_bot, student_player_id_for_path
from scenarios.resource_wars.game import ResourceWarsScenario


def test_three_players_distinct_positions() -> None:
    scenario = ResourceWarsScenario(7, player_ids=["p0_a", "p1_b", "p2_c"])
    scenario.setup()
    snap = scenario.positions_snapshot()
    assert set(snap) == {"p0_a", "p1_b", "p2_c"}
    assert len({tuple(v) for v in snap.values()}) == 3


def test_apply_turn_requires_all_players() -> None:
    scenario = ResourceWarsScenario(1, player_ids=["p0_a", "p1_b"])
    scenario.setup()
    with pytest.raises(KeyError):
        scenario.apply_turn({"p0_a": Action.WAIT})


def test_wait_event_order_is_sorted_by_player_id() -> None:
    scenario = ResourceWarsScenario(0, player_ids=["zebra", "alpha"])
    scenario.setup()
    result = scenario.apply_turn({"zebra": Action.WAIT, "alpha": Action.WAIT})
    waited = [e for e in result.events if e.endswith("_waited")]
    assert waited == ["alpha_waited", "zebra_waited"]


def test_live_game_two_student_paths_no_builtin_ai(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    template = (Path("student_bots") / "example_bot.py").read_text(encoding="utf-8")
    a = tmp_path / "aa.py"
    b = tmp_path / "bb.py"
    a.write_text(template, encoding="utf-8")
    b.write_text(template, encoding="utf-8")
    bots = [
        load_bot(a, player_id=student_player_id_for_path(a, 0)),
        load_bot(b, player_id=student_player_id_for_path(b, 1)),
    ]
    config = load_config(Path("configs/default.toml"))
    live = LiveGame(
        scenario_id="resource_wars",
        student_bots=bots,
        seed=99,
        config=config,
        opponent_mode="greedy",
    )
    assert set(live.scenario.player_ids()) == {"p0_aa", "p1_bb"}
    live.finish(write_results=False)


def test_cli_runs_two_distinct_bots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(root)
    template = (root / "student_bots" / "example_bot.py").read_text(encoding="utf-8")
    one = tmp_path / "one.py"
    two = tmp_path / "two.py"
    one.write_text(template, encoding="utf-8")
    two.write_text(template, encoding="utf-8")
    out = tmp_path / "results"
    cmd = [
        sys.executable,
        "-m",
        "engine.cli",
        "run",
        "--scenario",
        "resource_wars",
        "--bots",
        str(one),
        str(two),
        "--seed",
        "5",
        "--results-dir",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True, cwd=root)
    replay_path = next(out.glob("session_*/replay.json"))
    data = json.loads(replay_path.read_text(encoding="utf-8"))
    assert len(data["bots"]) == 2
    assert len(data["player_ids"]) == 2
