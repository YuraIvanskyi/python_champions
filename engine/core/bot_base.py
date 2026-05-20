"""Advanced student bot API."""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.core.action import Action
from engine.student_api import GameView


class BotBase(ABC):
    @abstractmethod
    def make_turn(self, state: GameView) -> str | Action:
        """Return an action string or Action enum member."""
