"""Session output: replay.json and logs.txt."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.core.bot_profile import player_dict
from engine.core.player import Player
from engine.core.turn_result import TurnResult


def write_session(
    results_dir: Path,
    *,
    seed: int,
    scenario_id: str,
    bot_path: str,
    turn_log: list[TurnResult],
    final_scores: dict[str, int],
    text_log: list[str],
    players: dict[str, Player] | None = None,
    opponent_mode: str | None = None,
) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    session_dir = results_dir / f"session_{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)

    replay: dict[str, Any] = {
        "seed": seed,
        "scenario": scenario_id,
        "bot": bot_path,
        "turns": [
            {
                "turn": tr.turn_number,
                "actions": {pid: act.value for pid, act in tr.actions.items()},
                "scores": tr.scores,
                "events": tr.events,
            }
            for tr in turn_log
        ],
        "final_scores": final_scores,
    }
    if opponent_mode is not None:
        replay["opponent_mode"] = opponent_mode
    if players:
        replay["players"] = {
            pid: player_dict(pid, p.display_name, p.icon_path)
            for pid, p in players.items()
        }

    (session_dir / "replay.json").write_text(
        json.dumps(replay, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (session_dir / "logs.txt").write_text("\n".join(text_log) + "\n", encoding="utf-8")
    return session_dir
