"""Session output: replay.json and logs.txt."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.core.bot_profile import player_dict
from engine.core.player import Player
from engine.core.turn_result import TurnResult


def _posix_bot_path(path_str: str) -> str:
    """Normalize stored bot paths for cross-platform replays."""
    return Path(path_str).as_posix()


def write_session(
    results_dir: Path,
    *,
    seed: int,
    scenario_id: str,
    bot_path: str,
    bot_paths: list[str] | None = None,
    player_ids: list[str] | None = None,
    turn_log: list[TurnResult],
    final_scores: dict[str, int],
    text_log: list[str],
    players: dict[str, Player] | None = None,
    opponent_mode: str | None = None,
) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    session_dir = results_dir / f"session_{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)

    paths = [_posix_bot_path(p) for p in (bot_paths if bot_paths is not None else [bot_path])]

    replay: dict[str, Any] = {
        "schema_version": 2,
        "seed": seed,
        "scenario": scenario_id,
        "bot": _posix_bot_path(bot_path),
        "bots": paths,
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
    if player_ids is not None:
        replay["player_ids"] = list(player_ids)
    if opponent_mode is not None:
        replay["opponent_mode"] = opponent_mode
    if players:
        replay["players"] = {
            pid: player_dict(pid, p.display_name, p.icon_path, is_student=p.is_student)
            for pid, p in players.items()
            if p.player_id != "_none"
        }

    (session_dir / "replay.json").write_text(
        json.dumps(replay, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (session_dir / "logs.txt").write_text("\n".join(text_log) + "\n", encoding="utf-8")
    return session_dir
