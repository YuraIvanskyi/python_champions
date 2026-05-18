"""Headless turn loop smoke test."""

from pathlib import Path

from engine.core.config import load_config
from engine.core.game import run_game
from engine.core.loader import load_bot


def test_ten_turns_headless() -> None:
    bot = load_bot(Path("student_bots/example_bot.py"))
    config = load_config()
    result = run_game(
        scenario_id="resource_wars",
        student_bot=bot,
        seed=42,
        config=config,
        results_dir=None,
        max_turns=10,
        write_results=False,
        print_summary=False,
    )
    assert len(result.turn_log) == 10
    assert "student" in result.final_scores
