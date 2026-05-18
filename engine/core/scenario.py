"""Scenario contract for turn-based simulations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from engine.core.action import Action
from engine.core.turn_result import TurnResult


class ScenarioBase(ABC):
    @abstractmethod
    def setup(self) -> None:
        """Initialize map, entities, and starting state."""

    @abstractmethod
    def apply_turn(self, actions: dict[str, Action]) -> TurnResult:
        """Apply player actions and return turn outcome."""

    @abstractmethod
    def calculate_score(self) -> dict[str, int]:
        """Current scores keyed by player id."""

    @abstractmethod
    def is_finished(self) -> bool:
        """Whether the scenario should stop the game loop."""

    def build_game_state(self, player_id: str) -> dict[str, Any]:
        """Readonly simplified state for a single bot."""
        raise NotImplementedError
