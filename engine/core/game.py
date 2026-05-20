"""Main turn loop."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from engine.core.config import AppConfig
from engine.core.live_game import LiveGame
from engine.core.player import Bot
from engine.core.turn_result import TurnResult


@dataclass
class RunResult:
    turn_log: list[TurnResult]
    final_scores: dict[str, int]
    text_log: list[str]
    session_dir: Path | None = None


def run_game(
    *,
    scenario_id: str,
    student_bots: list[Bot],
    seed: int,
    config: AppConfig,
    results_dir: Path | None = None,
    opponent_mode: str | None = None,
    ai_turn=None,
    max_turns: int | None = None,
    write_results: bool = True,
    print_summary: bool = True,
) -> RunResult:
    live = LiveGame(
        scenario_id=scenario_id,
        student_bots=student_bots,
        seed=seed,
        config=config,
        opponent_mode=opponent_mode,
        ai_turn=ai_turn,
        max_turns=max_turns,
    )
    try:
        while not live.is_finished():
            turn_result = live.step()
            if turn_result is not None and print_summary:
                line = live.text_log[-1]
                print(line)
    finally:
        session_dir = live.finish(
            results_dir=results_dir,
            write_results=write_results,
        )

    final_scores = live.scenario.calculate_score()
    if print_summary:
        print(f"Final scores: {final_scores}")
        if session_dir is not None:
            print(f"Wrote session to {session_dir}")

    return RunResult(
        turn_log=live.turn_log,
        final_scores=final_scores,
        text_log=live.text_log,
        session_dir=session_dir,
    )
