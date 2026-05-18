"""Steppable live game session for UI and headless runners."""

from __future__ import annotations

import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

from engine.core.action import Action
from engine.core.config import AppConfig
from engine.core.opponents import opponent_player, resolve_ai_turn
from engine.core.player import Bot, Player
from engine.core.scenario import ScenarioBase
from engine.core.scenario_registry import create_scenario
from engine.core.session import write_session
from engine.core.turn_result import TurnResult
from engine.sandbox.runner import SandboxedBot, run_turn_sandboxed


def build_render_state(
    scenario: ScenarioBase,
    *,
    viewer: str = "student",
    players: dict[str, Player] | None = None,
) -> dict[str, Any]:
    """Readonly map snapshot for UI rendering."""
    state = scenario.build_game_state(viewer)
    profiles = players or {}
    entities = []
    for entity_id, position_key in (
        ("student", "position"),
        ("opponent", "opponent_position"),
    ):
        profile = profiles.get(entity_id)
        entry: dict[str, Any] = {
            "id": entity_id,
            "position": state[position_key],
        }
        if profile is not None:
            entry["display_name"] = profile.display_name
            if profile.icon_path:
                entry["icon"] = profile.icon_path
        entities.append(entry)

    display_names = {
        pid: p.display_name for pid, p in profiles.items()
    }
    return {
        "turn": state["turn"],
        "map_width": state["map_width"],
        "map_height": state["map_height"],
        "tiles": state["visible_tiles"],
        "entities": entities,
        "scores": scenario.calculate_score(),
        "display_names": display_names,
    }


class LiveGame:
    """Runs one scenario turn at a time using the same rules as headless CLI."""

    def __init__(
        self,
        *,
        scenario_id: str,
        student_bot: Bot,
        seed: int,
        config: AppConfig,
        opponent_mode: str | None = None,
        ai_turn: Callable[..., Action] | None = None,
        max_turns: int | None = None,
    ) -> None:
        effective_max = max_turns if max_turns is not None else config.engine.max_turns
        self.scenario_id = scenario_id
        self.student_bot = student_bot
        self.seed = seed
        self.config = config
        mode = opponent_mode or config.game.default_opponent
        self.opponent_mode = mode
        self.opponent_player = opponent_player(mode)
        self.players: dict[str, Player] = {
            "student": student_bot.player,
            "opponent": self.opponent_player,
        }
        self.scenario = create_scenario(scenario_id, seed=seed, max_turns=effective_max)
        self.scenario.setup()

        rng = random.Random(seed)
        self._rng = rng
        if ai_turn is not None:
            self._ai_fn = ai_turn
        else:
            resolved = resolve_ai_turn(mode)

            def _bound(state: dict[str, Any], r: random.Random = rng) -> Action:
                return resolved(state, r)

            self._ai_fn = _bound
        self._sandbox: SandboxedBot | None = None
        if student_bot.source_path:
            self._sandbox = SandboxedBot(Path(student_bot.source_path), config)

        self.turn_log: list[TurnResult] = []
        self.text_log: list[str] = [
            f"scenario={scenario_id} seed={seed} bot={student_bot.source_path} "
            f"opponent={mode}",
        ]
        self.last_turn: TurnResult | None = None
        self.status_message: str = ""
        self._closed = False

    def is_finished(self) -> bool:
        return self.scenario.is_finished()

    def get_render_state(self) -> dict:
        return build_render_state(self.scenario, players=self.players)

    def step(self) -> TurnResult | None:
        if self.is_finished():
            return None

        actions: dict[str, Action] = {}
        events_extra: list[str] = []

        student_state = self.scenario.build_game_state("student")
        if self.student_bot.source_path and self._sandbox is not None:
            action, sandbox_events, _ = run_turn_sandboxed(
                Path(self.student_bot.source_path),
                student_state,
                self.config,
                session=self._sandbox,
            )
            events_extra.extend(sandbox_events)
            if "sandbox_timeout" in sandbox_events:
                self.status_message = "Bot timed out — turn forfeited (WAIT)."
            elif any(e.startswith("bot_error:") for e in sandbox_events):
                self.status_message = "Bot error — turn forfeited (WAIT)."
        else:
            action = self.student_bot.make_turn(student_state)

        actions["student"] = action
        opponent_state = self.scenario.build_game_state("opponent")
        actions["opponent"] = self._ai_fn(opponent_state)

        turn_result = self.scenario.apply_turn(actions)
        turn_result.events.extend(events_extra)
        self.turn_log.append(turn_result)
        self.last_turn = turn_result

        student_label = self.players["student"].display_name
        opponent_label = self.players["opponent"].display_name
        line = (
            f"Turn {turn_result.turn_number}: "
            f"{student_label}={actions['student'].value} "
            f"{opponent_label}={actions['opponent'].value} "
            f"scores={turn_result.scores}"
        )
        self.text_log.append(line)
        return turn_result

    def finish(
        self,
        *,
        results_dir: Path | None = None,
        write_results: bool = True,
    ) -> Path | None:
        if self._closed:
            return None
        self._closed = True
        if self._sandbox is not None:
            self._sandbox.close()
            self._sandbox = None

        final_scores = self.scenario.calculate_score()
        self.text_log.append(f"Final scores: {final_scores}")

        if (
            write_results
            and results_dir is not None
            and self.student_bot.source_path
        ):
            return write_session(
                results_dir,
                seed=self.seed,
                scenario_id=self.scenario_id,
                bot_path=self.student_bot.source_path,
                turn_log=self.turn_log,
                final_scores=final_scores,
                text_log=self.text_log,
                players=self.players,
                opponent_mode=self.opponent_mode,
            )
        return None

    def close(self) -> None:
        if not self._closed:
            self.finish(write_results=False)
