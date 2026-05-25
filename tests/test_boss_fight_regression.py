"""Identical seed + bots → identical replay.json (determinism check)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from engine.core.config import load_config
from engine.core.game import run_game
from engine.core.loader import load_bot


def _run_once(tmp_dir: Path) -> dict:
    bot_path = Path("student_bots/boss_fight/boss_fight_starter.py")
    config = load_config()
    bots = [load_bot(bot_path)]
    result = run_game(
        scenario_id="boss_fight",
        student_bots=bots,
        seed=1,
        config=config,
        results_dir=tmp_dir,
        write_results=True,
        print_summary=False,
        run_analysis=False,
    )
    session_dir = result.session_dir
    assert session_dir is not None
    replay = json.loads((session_dir / "replay.json").read_text())
    return replay


@pytest.mark.skipif(
    not Path("student_bots/boss_fight/boss_fight_starter.py").is_file(),
    reason="starter bot not found",
)
def test_identical_seed_gives_identical_replay() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        replay1 = _run_once(tmp_dir)
        replay2 = _run_once(tmp_dir)

    assert replay1["turns"] == replay2["turns"], "Replay turns differ across identical runs"
    assert replay1["final_scores"] == replay2["final_scores"]


@pytest.mark.skipif(
    not Path("student_bots/boss_fight/boss_fight_starter.py").is_file(),
    reason="starter bot not found",
)
def test_headless_run_completes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        bot_path = Path("student_bots/boss_fight/boss_fight_starter.py")
        config = load_config()
        bots = [load_bot(bot_path)]
        result = run_game(
            scenario_id="boss_fight",
            student_bots=bots,
            seed=1,
            config=config,
            results_dir=Path(tmp),
            write_results=True,
            print_summary=False,
            run_analysis=False,
        )
    assert isinstance(result.final_scores, dict)
    assert len(result.final_scores) >= 1
    assert len(result.turn_log) > 0
