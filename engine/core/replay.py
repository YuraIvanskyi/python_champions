"""Load and step through stored replay.json files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.core.action import parse_action
from engine.core.live_game import build_render_state
from engine.core.opponents import opponent_player
from engine.core.player import Player
from engine.core.scenario_registry import create_scenario
from engine.core.turn_result import TurnResult


def load_replay(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ("seed", "scenario", "turns", "final_scores")
    for key in required:
        if key not in data:
            raise ValueError(f"Replay missing required field: {key}")
    return data


def players_from_replay(replay: dict[str, Any]) -> dict[str, Player]:
    """Build Player profiles from replay metadata, with defaults for older files."""
    stored = replay.get("players")
    if isinstance(stored, dict) and stored:
        players: dict[str, Player] = {}
        for player_id, meta in stored.items():
            if not isinstance(meta, dict):
                continue
            name = str(meta.get("display_name", player_id))
            icon = meta.get("icon")
            icon_path = str(icon) if icon else None
            is_student = bool(meta["is_student"]) if "is_student" in meta else player_id == "student"
            players[player_id] = Player(
                player_id=player_id,
                display_name=name,
                is_student=is_student,
                icon_path=icon_path,
            )
        return players

    mode = str(replay.get("opponent_mode", "greedy"))
    return {
        "student": Player("student", "You", is_student=True),
        "opponent": opponent_player(mode),
    }


def list_session_dirs(results_dir: Path) -> list[Path]:
    if not results_dir.is_dir():
        return []
    sessions = [p for p in results_dir.iterdir() if p.is_dir() and p.name.startswith("session_")]
    return sorted(sessions, key=lambda p: p.name, reverse=True)


class ReplaySession:
    """Reconstruct map state by replaying stored actions on a fresh scenario."""

    def __init__(self, replay: dict[str, Any]) -> None:
        self.replay = replay
        self.scenario_id = str(replay["scenario"])
        self.seed = int(replay["seed"])
        self.final_scores = dict(replay["final_scores"])
        self.turns_data: list[dict[str, Any]] = list(replay.get("turns", []))
        self.players = players_from_replay(replay)
        raw_ids = replay.get("player_ids")
        self.player_ids: list[str] | None = (
            list(raw_ids) if isinstance(raw_ids, list) and raw_ids else None
        )
        self.scenario = create_scenario(
            self.scenario_id,
            seed=self.seed,
            player_ids=self.player_ids,
        )
        self.scenario.setup()
        self.turn_index = -1
        self.last_turn: TurnResult | None = None

    @classmethod
    def from_path(cls, path: Path) -> ReplaySession:
        return cls(load_replay(path))

    @property
    def turn_count(self) -> int:
        return len(self.turns_data)

    def reset(self) -> None:
        """Rebuild scenario from seed (single setup — avoids double RNG consumption)."""
        self.scenario = create_scenario(
            self.scenario_id,
            seed=self.seed,
            player_ids=self.player_ids,
        )
        self.scenario.setup()
        self.turn_index = -1
        self.last_turn = None

    def get_render_state(self) -> dict:
        return build_render_state(self.scenario, players=self.players)

    def step_forward(self) -> TurnResult | None:
        next_index = self.turn_index + 1
        if next_index >= len(self.turns_data):
            return None
        turn_data = self.turns_data[next_index]
        actions = {pid: parse_action(val) for pid, val in turn_data["actions"].items()}
        result = self.scenario.apply_turn(actions)
        self.turn_index = next_index
        self.last_turn = result
        return result

    def step_backward(self) -> None:
        """Rewind by rebuilding from seed and replaying to target index."""
        target = self.turn_index - 1
        self.reset()
        for _ in range(target + 1):
            self.step_forward()

    def seek(self, index: int) -> None:
        """Jump to turn index (-1 = initial setup, 0 = after first turn)."""
        clamped = max(-1, min(index, len(self.turns_data) - 1))
        self.reset()
        for _ in range(clamped + 1):
            self.step_forward()
