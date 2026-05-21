"""Runtime metrics collected during simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuntimeMetrics:
    turn_times_ms: list[float] = field(default_factory=list)
    timeout_count: int = 0
    crash_count: int = 0
    invalid_action_count: int = 0
    total_turns: int = 0

    @property
    def avg_turn_time_ms(self) -> float:
        if not self.turn_times_ms:
            return 0.0
        return sum(self.turn_times_ms) / len(self.turn_times_ms)

    @property
    def max_turn_time_ms(self) -> float:
        if not self.turn_times_ms:
            return 0.0
        return max(self.turn_times_ms)


class RuntimeCollector:
    """Accumulates per-turn sandbox and scenario events."""

    def __init__(self) -> None:
        self.metrics = RuntimeMetrics()

    def record_turn(
        self,
        *,
        events: list[str],
        turn_time_ms: float,
        player_id: str = "student",
    ) -> None:
        self.metrics.total_turns += 1
        self.metrics.turn_times_ms.append(turn_time_ms)

        if "sandbox_timeout" in events:
            self.metrics.timeout_count += 1
        if any(
            e.startswith("bot_error:")
            or e.startswith("sandbox_dead")
            or e.startswith("sandbox_write_error:")
            for e in events
        ):
            self.metrics.crash_count += 1
        if any(e.startswith("invalid_action:") for e in events):
            self.metrics.invalid_action_count += 1
        if f"{player_id}_gather_failed" in events:
            self.metrics.invalid_action_count += 1

    def to_dict(self) -> dict[str, Any]:
        m = self.metrics
        return {
            "turn_times_ms": [round(t, 2) for t in m.turn_times_ms],
            "avg_turn_time_ms": round(m.avg_turn_time_ms, 2),
            "max_turn_time_ms": round(m.max_turn_time_ms, 2),
            "timeout_count": m.timeout_count,
            "crash_count": m.crash_count,
            "invalid_action_count": m.invalid_action_count,
            "total_turns": m.total_turns,
        }
