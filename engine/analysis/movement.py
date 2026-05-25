"""Replay-based movement pattern analysis.

Reconstructs player positions via ``ReplaySession`` re-simulation, then
derives behavioral metrics about stuck loops, oscillation, blocked moves,
and score-stall periods.  Results land in ``metrics.json`` under the
``"movement"`` key and feed the template feedback system.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Config defaults (overridden via AnalysisConfig.movement)
# ---------------------------------------------------------------------------

STUCK_WINDOW_TURNS: int = 10
STUCK_REVISIT_THRESHOLD: int = 3
CONSECUTIVE_ACTION_WARN: int = 8
BLOCKED_RATIO_WARN: float = 0.35
SCORE_STALL_WARN: int = 12
OSCILLATION_MIN_CYCLES: int = 3
MIN_TURNS_FOR_ANALYSIS: int = 5


@dataclass
class MovementConfig:
    stuck_window_turns: int = STUCK_WINDOW_TURNS
    stuck_revisit_threshold: int = STUCK_REVISIT_THRESHOLD
    consecutive_action_warn: int = CONSECUTIVE_ACTION_WARN
    blocked_ratio_warn: float = BLOCKED_RATIO_WARN
    score_stall_warn: int = SCORE_STALL_WARN
    oscillation_min_cycles: int = OSCILLATION_MIN_CYCLES
    min_turns_for_analysis: int = MIN_TURNS_FOR_ANALYSIS


@dataclass
class MovementMetrics:
    blocked_move_ratio: float = 0.0
    max_consecutive_same_action: int = 0
    wait_ratio: float = 0.0
    position_revisit_count: int = 0
    stuck_episodes: int = 0
    oscillation_episodes: int = 0
    score_stall_turns: int = 0
    unique_positions_ratio: float = 0.0
    worst_stuck_turn_range: list[int] = field(default_factory=list)
    analyzed: bool = False  # False when skipped (too few turns / no replay)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def analyze_movement(
    session_dir: Path,
    player_id: str,
    *,
    cfg: MovementConfig | None = None,
) -> MovementMetrics:
    """Return movement metrics for *player_id* derived from the session replay.

    Returns a zeroed, ``analyzed=False`` object when the replay is missing or
    has too few turns to be meaningful.
    """
    cfg = cfg or MovementConfig()

    replay_path = session_dir / "replay.json"
    if not replay_path.is_file():
        return MovementMetrics()

    try:
        import json
        replay: dict[str, Any] = json.loads(replay_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return MovementMetrics()

    turns: list[dict[str, Any]] = replay.get("turns", [])
    if len(turns) < cfg.min_turns_for_analysis:
        return MovementMetrics()

    positions = _reconstruct_positions(replay, player_id)
    return _compute_metrics(turns, positions, player_id, cfg)


# ---------------------------------------------------------------------------
# Position reconstruction
# ---------------------------------------------------------------------------

def _reconstruct_positions(
    replay: dict[str, Any],
    player_id: str,
) -> list[tuple[int, int] | None]:
    """Replay all actions and collect per-turn positions for *player_id*.

    Returns a list of length == turns, where each entry is (x, y) or None when
    the position could not be determined for that turn.
    """
    try:
        from engine.core.replay import ReplaySession
        session = ReplaySession(replay)
    except Exception:  # noqa: BLE001
        return []

    positions: list[tuple[int, int] | None] = []
    while True:
        result = session.step_forward()
        if result is None:
            break
        pos = _entity_position(session.get_render_state(), player_id)
        positions.append(pos)

    return positions


def _entity_position(
    render_state: dict[str, Any],
    player_id: str,
) -> tuple[int, int] | None:
    for entity in render_state.get("entities", []):
        if entity.get("id") == player_id:
            xy = entity.get("position")
            if xy and len(xy) >= 2:
                return (int(xy[0]), int(xy[1]))
    return None


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------

def _compute_metrics(
    turns: list[dict[str, Any]],
    positions: list[tuple[int, int] | None],
    player_id: str,
    cfg: MovementConfig,
) -> MovementMetrics:
    m = MovementMetrics(analyzed=True)
    total = len(turns)

    # ── Event-based counters (from replay events, no re-sim needed) ──────────
    blocked_count = 0
    moved_count = 0
    waited_count = 0
    for turn in turns:
        events: list[str] = turn.get("events", [])
        action = str(turn.get("actions", {}).get(player_id, ""))
        if f"{player_id}_blocked" in events:
            blocked_count += 1
        if f"{player_id}_moved" in events:
            moved_count += 1
        if f"{player_id}_waited" in events or action == "WAIT":
            waited_count += 1

    attempted_moves = moved_count + blocked_count
    m.blocked_move_ratio = (
        round(blocked_count / attempted_moves, 3) if attempted_moves else 0.0
    )
    m.wait_ratio = round(waited_count / total, 3) if total else 0.0

    # ── Consecutive same-action streak ───────────────────────────────────────
    m.max_consecutive_same_action = _max_consecutive_action(turns, player_id)

    # ── Position-based metrics (require reconstruction) ──────────────────────
    valid_positions = [p for p in positions if p is not None]
    if valid_positions:
        unique = len(set(valid_positions))
        m.unique_positions_ratio = round(unique / len(valid_positions), 3)
        m.position_revisit_count = _revisit_count(valid_positions)

        scores_per_turn = [
            (t.get("turn", i + 1), t.get("scores", {}).get(player_id, 0))
            for i, t in enumerate(turns)
        ]
        m.stuck_episodes, m.worst_stuck_turn_range = _detect_stuck(
            positions, scores_per_turn, cfg
        )
        m.oscillation_episodes = _detect_oscillation(positions, cfg.oscillation_min_cycles)
        m.score_stall_turns = _longest_score_stall(turns, player_id)

    return m


def _max_consecutive_action(turns: list[dict[str, Any]], player_id: str) -> int:
    max_run = 0
    run = 0
    prev: str | None = None
    for turn in turns:
        action = str(turn.get("actions", {}).get(player_id, ""))
        if not action:
            continue
        if action == prev:
            run += 1
        else:
            run = 1
        max_run = max(max_run, run)
        prev = action
    return max_run


def _revisit_count(positions: list[tuple[int, int]]) -> int:
    """Count how many positions were re-entered at any point."""
    seen: set[tuple[int, int]] = set()
    revisits = 0
    for pos in positions:
        if pos in seen:
            revisits += 1
        seen.add(pos)
    return revisits


def _detect_stuck(
    positions: list[tuple[int, int] | None],
    scores_per_turn: list[tuple[int, int]],
    cfg: MovementConfig,
) -> tuple[int, list[int]]:
    """Return (stuck_episode_count, worst_turn_range).

    A stuck episode is a window of ``stuck_window_turns`` consecutive turns
    where the same cell is revisited >= ``stuck_revisit_threshold`` times AND
    the score does not increase.
    """
    window = cfg.stuck_window_turns
    threshold = cfg.stuck_revisit_threshold
    n = len(positions)
    episodes = 0
    worst: list[int] = []
    worst_revisits = 0
    i = 0
    while i <= n - window:
        window_pos = [p for p in positions[i : i + window] if p is not None]
        if not window_pos:
            i += 1
            continue
        counts = Counter(window_pos)
        max_revisits = max(counts.values())
        # Score change in window
        start_score = scores_per_turn[i][1] if i < len(scores_per_turn) else 0
        end_idx = min(i + window - 1, len(scores_per_turn) - 1)
        end_score = scores_per_turn[end_idx][1] if end_idx < len(scores_per_turn) else 0
        if max_revisits >= threshold and end_score <= start_score:
            episodes += 1
            if max_revisits > worst_revisits:
                worst_revisits = max_revisits
                worst = [
                    scores_per_turn[i][0],
                    scores_per_turn[end_idx][0],
                ]
            i += window  # skip past this episode
        else:
            i += 1
    return episodes, worst


def _detect_oscillation(
    positions: list[tuple[int, int] | None],
    min_cycles: int,
) -> int:
    """Count A→B→A→B ping-pong episodes of at least *min_cycles* repetitions.

    Each distinct pair (A, B) that oscillates >= min_cycles times counts as one
    episode.  Overlapping pairs are de-duplicated.
    """
    valid = [p for p in positions if p is not None]
    if len(valid) < 4:
        return 0

    pair_counts: Counter[tuple[tuple[int, int], tuple[int, int]]] = Counter()
    for j in range(len(valid) - 3):
        a, b, c, d = valid[j], valid[j + 1], valid[j + 2], valid[j + 3]
        if a == c and b == d and a != b:
            key = (min(a, b), max(a, b))
            pair_counts[key] += 1

    return sum(1 for count in pair_counts.values() if count >= min_cycles)


def _longest_score_stall(
    turns: list[dict[str, Any]],
    player_id: str,
) -> int:
    """Return the longest run of consecutive turns with an unchanged score
    during which the bot was actually moving (not waiting)."""
    max_stall = 0
    run = 0
    prev_score: int | None = None
    for turn in turns:
        score = turn.get("scores", {}).get(player_id, 0)
        events: list[str] = turn.get("events", [])
        action = str(turn.get("actions", {}).get(player_id, ""))
        is_moving = (
            f"{player_id}_moved" in events
            or f"{player_id}_blocked" in events
            or action.startswith("MOVE_")
        )
        if prev_score is not None and score == prev_score and is_moving:
            run += 1
            max_stall = max(max_stall, run)
        else:
            run = 0
        prev_score = score
    return max_stall


# ---------------------------------------------------------------------------
# Empty defaults for when analysis is skipped
# ---------------------------------------------------------------------------

def empty_movement_dict() -> dict[str, Any]:
    return MovementMetrics().to_dict()
