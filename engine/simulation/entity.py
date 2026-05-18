"""Entities placed on the map."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Entity:
    entity_id: str
    owner_id: str
    x: int
    y: int
