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
from engine.analysis.runtime import RuntimeCollector
from engine.sandbox.runner import SandboxedBot, run_turn_sandboxed


def _scenario_needs_external_opponent(scenario_id: str, *, student_count: int) -> bool:
    """Return True when practice mode should add a built-in computer player."""
    if scenario_id in ("boss_fight", "energy_stations"):
        return student_count < 2
    return True


def build_render_state(
    scenario: ScenarioBase,
    *,
    viewer: str | None = None,
    players: dict[str, Player] | None = None,
) -> dict[str, Any]:
    """Readonly map snapshot for UI rendering."""
    player_ids_fn = getattr(scenario, "player_ids", None)
    if callable(player_ids_fn):
        order = player_ids_fn()
    else:
        order = sorted(scenario.calculate_score().keys())
    resolved_viewer = viewer if viewer is not None else order[0]
    state = scenario.build_game_state(resolved_viewer)
    profiles = players or {}

    pos_fn = getattr(scenario, "positions_snapshot", None)
    if callable(pos_fn):
        pos_map = pos_fn()
        positions = {pid: [pos_map[pid][0], pos_map[pid][1]] for pid in order}
    else:
        positions = {
            "student": state["position"],
            "opponent": state["opponent_position"],
        }

    entities: list[dict[str, Any]] = []
    for pid in order:
        profile = profiles.get(pid)
        entry: dict[str, Any] = {
            "id": pid,
            "position": positions[pid],
        }
        if profile is not None:
            entry["display_name"] = profile.display_name
            if profile.icon_path:
                entry["icon"] = profile.icon_path
        entities.append(entry)

    display_names = {pid: p.display_name for pid, p in profiles.items()}
    result: dict[str, Any] = {
        "turn": state["turn"],
        "map_width": state["map_width"],
        "map_height": state["map_height"],
        "tiles": state["visible_tiles"],
        "entities": entities,
        "scores": scenario.calculate_score(),
        "display_names": display_names,
    }

    # Merge extras from scenarios that provide them (e.g. boss_fight)
    extras_fn = getattr(scenario, "render_extras", None)
    if callable(extras_fn):
        result.update(extras_fn())

    return result


class LiveGame:
    """Runs one scenario turn at a time using the same rules as headless CLI."""

    def __init__(
        self,
        *,
        scenario_id: str,
        student_bots: list[Bot],
        seed: int,
        config: AppConfig,
        opponent_mode: str | None = None,
        ai_turn: Callable[..., Action] | None = None,
        max_turns: int | None = None,
        boss_difficulty: int | None = None,
    ) -> None:
        if not student_bots:
            raise ValueError("At least one student bot is required")

        paths = [b.source_path for b in student_bots if b.source_path]
        resolved = [str(Path(p).resolve()) for p in paths]
        if len(resolved) != len(set(resolved)):
            raise ValueError("Duplicate bot file paths are not allowed")

        effective_max = max_turns
        self.scenario_id = scenario_id
        self.student_bots: list[Bot] = list(student_bots)
        self.seed = seed
        self.config = config
        _needs_opp = _scenario_needs_external_opponent(
            scenario_id, student_count=len(student_bots)
        )
        self.multi_student_match = len(student_bots) >= 2 or not _needs_opp

        if self.multi_student_match:
            self.opponent_mode = None
            self.opponent_player: Player | None = None
            player_ids = [b.player.player_id for b in student_bots]
            self.players = {b.player.player_id: b.player for b in student_bots}
        else:
            mode = opponent_mode or config.game.default_opponent
            self.opponent_mode = mode
            self.opponent_player = opponent_player(mode)
            self.players = {
                "student": student_bots[0].player,
                "opponent": self.opponent_player,
            }
            player_ids = ["student", "opponent"]

        self.boss_difficulty = boss_difficulty
        self.scenario = create_scenario(
            scenario_id,
            seed=seed,
            max_turns=effective_max,
            player_ids=player_ids,
            boss_difficulty=boss_difficulty,
        )
        self.scenario.setup()

        rng = random.Random(seed)
        self._rng = rng
        if self.multi_student_match:
            self._ai_fn = None
        elif ai_turn is not None:
            self._ai_fn = ai_turn
        else:
            resolved_ai = resolve_ai_turn(
                self.opponent_mode or "greedy",
                scenario_id=scenario_id,
            )

            def _bound(state: dict[str, Any], r: random.Random = rng) -> Action:
                return resolved_ai(state, r)

            self._ai_fn = _bound

        self._sandboxes: dict[str, SandboxedBot] = {}
        self._runtime_collectors: dict[str, RuntimeCollector] = {}
        for bot in student_bots:
            pid = bot.player.player_id
            self._runtime_collectors[pid] = RuntimeCollector()
            if bot.source_path:
                key = str(Path(bot.source_path).resolve())
                if key not in self._sandboxes:
                    self._sandboxes[key] = SandboxedBot(Path(key), config)

        bot_paths_str = ", ".join(str(p) for p in paths) if paths else "(in-memory)"
        opponent_part = (
            ""
            if self.multi_student_match
            else f" opponent={self.opponent_mode}"
        )
        boss_part = ""
        if scenario_id == "boss_fight":
            level = getattr(self.scenario, "_difficulty", boss_difficulty or 1)
            boss_part = f" boss_difficulty={level}"
        self.turn_log: list[TurnResult] = []
        self.text_log: list[str] = [
            f"scenario={scenario_id} seed={seed} bots={bot_paths_str}"
            f"{opponent_part}{boss_part}",
        ]
        self.last_turn: TurnResult | None = None
        self.status_message: str = ""
        self._closed = False

    def is_finished(self) -> bool:
        return self.scenario.is_finished()

    def get_render_state(self) -> dict:
        first = self.scenario.player_ids()[0]
        return build_render_state(self.scenario, viewer=first, players=self.players)

    def step(self) -> TurnResult | None:
        if self.is_finished():
            return None

        actions: dict[str, Action] = {}
        events_extra: list[str] = []

        for bot in self.student_bots:
            pid = bot.player.player_id
            state = self.scenario.build_game_state(pid)
            turn_events: list[str] = []
            turn_time_ms = 0.0
            if bot.source_path:
                key = str(Path(bot.source_path).resolve())
                sandbox = self._sandboxes.get(key)
                if sandbox is not None:
                    action, sandbox_events, turn_time_ms, _ = run_turn_sandboxed(
                        Path(bot.source_path),
                        state,
                        self.config,
                        session=sandbox,
                    )
                    turn_events.extend(sandbox_events)
                    events_extra.extend(sandbox_events)
                    if "sandbox_timeout" in sandbox_events:
                        label = bot.player.display_name
                        self.status_message = f"{label} timed out — turn forfeited (WAIT)."
                    elif any(e.startswith("bot_error:") for e in sandbox_events):
                        label = bot.player.display_name
                        self.status_message = f"{label} error — turn forfeited (WAIT)."
                else:
                    action = bot.make_turn(state)
            else:
                action = bot.make_turn(state)

            collector = self._runtime_collectors.get(pid)
            if collector is not None:
                collector.record_turn(
                    events=turn_events,
                    turn_time_ms=turn_time_ms,
                    player_id=pid,
                )
            actions[pid] = action

        if not self.multi_student_match and self._ai_fn is not None:
            opponent_state = self.scenario.build_game_state("opponent")
            actions["opponent"] = self._ai_fn(opponent_state)

        turn_result = self.scenario.apply_turn(actions)
        turn_result.events.extend(events_extra)
        self.turn_log.append(turn_result)
        self.last_turn = turn_result

        parts = []
        for pid in sorted(actions.keys()):
            label = self.players[pid].display_name
            parts.append(f"{label}={actions[pid].value}")
        line = f"Turn {turn_result.turn_number}: " + " ".join(parts) + f" scores={turn_result.scores}"
        self.text_log.append(line)
        return turn_result

    def finish(
        self,
        *,
        results_dir: Path | None = None,
        write_results: bool = True,
        run_analysis: bool = True,
    ) -> Path | None:
        if self._closed:
            return None
        self._closed = True
        for box in self._sandboxes.values():
            box.close()
        self._sandboxes.clear()

        final_scores = self.scenario.calculate_score()
        self.text_log.append(f"Final scores: {final_scores}")

        bot_paths: list[str] = []
        for b in self.student_bots:
            if b.source_path:
                bot_paths.append(str(Path(b.source_path)))
        if (
            write_results
            and results_dir is not None
            and bot_paths
        ):
            session_dir = write_session(
                results_dir,
                seed=self.seed,
                scenario_id=self.scenario_id,
                bot_path=bot_paths[0],
                bot_paths=bot_paths,
                player_ids=self.scenario.player_ids(),
                turn_log=self.turn_log,
                final_scores=final_scores,
                text_log=self.text_log,
                players=self.players,
                opponent_mode=self.opponent_mode,
            )
            if run_analysis:
                from engine.analysis.pipeline import run_analysis_for_session

                # Collect scenario-specific extra gameplay metrics per player.
                # Prefer the generic "scenario_metrics" hook; fall back to the
                # legacy "energy_metrics" name for backward compatibility.
                _extra_fn = getattr(self.scenario, "scenario_metrics", None) or getattr(
                    self.scenario, "energy_metrics", None
                )
                _scenario_metrics: dict | None = (
                    _extra_fn() if callable(_extra_fn) else None
                )

                for bot in self.student_bots:
                    if not bot.source_path:
                        continue
                    pid = bot.player.player_id
                    # Build per-player extra gameplay dict from scenario metrics
                    extra: dict | None = None
                    if _scenario_metrics:
                        extra = {
                            k: v[pid] if isinstance(v, dict) else v
                            for k, v in _scenario_metrics.items()
                            if not isinstance(v, dict) or pid in v
                        }
                    run_analysis_for_session(
                        session_dir,
                        bot_path=Path(bot.source_path),
                        config=self.config,
                        final_scores=final_scores,
                        scenario_id=self.scenario_id,
                        runtime_collector=self._runtime_collectors.get(pid),
                        player_id=pid,
                        extra_gameplay=extra,
                    )
            return session_dir
        return None

