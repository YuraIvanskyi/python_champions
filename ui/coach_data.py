"""Load session metrics and bot source for the Code Coach screen."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_replay(session_dir: Path) -> dict[str, Any] | None:
    path = session_dir / "replay.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def player_ids_from_replay(replay: dict[str, Any]) -> list[str]:
    if "player_ids" in replay:
        return list(replay["player_ids"])
    if "players" in replay:
        return list(replay["players"].keys())
    return ["student"]


def bot_path_for_player(replay: dict[str, Any], player_id: str) -> Path | None:
    bot_files = replay.get("bot_files")
    if isinstance(bot_files, dict) and player_id in bot_files:
        return Path(bot_files[player_id])
    bots = replay.get("bots")
    player_ids = replay.get("player_ids")
    if isinstance(bots, list) and isinstance(player_ids, list):
        try:
            idx = player_ids.index(player_id)
            if idx < len(bots):
                return Path(bots[idx])
        except (ValueError, IndexError):
            pass
    if isinstance(bots, list) and len(bots) == 1:
        return Path(bots[0])
    bot = replay.get("bot")
    if isinstance(bot, str):
        return Path(bot)
    return None


def load_metrics_block(metrics: dict[str, Any], player_id: str) -> dict[str, Any]:
    if "players" in metrics:
        players = metrics["players"]
        if player_id in players:
            return players[player_id]
        if players:
            return next(iter(players.values()))
    return metrics


def list_player_metrics(metrics: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    if "players" in metrics:
        return [(pid, block) for pid, block in metrics["players"].items()]
    pid = metrics.get("gameplay", {}).get("player_id", "student")
    return [(pid, metrics)]


def read_bot_source(path: Path | None) -> list[str]:
    if path is None or not path.is_file():
        return ["# Bot source file not found"]
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ["# Could not read bot file"]
