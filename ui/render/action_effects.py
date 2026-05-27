"""Short tile-local particles for combat, healing, and gather actions."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

import pygame

from ui.theme import TILE_SIZE

_EFFECT_MS = 480
_EFFECT_MS_SHORT = 360

_GATHER_RE = re.compile(r"^(?P<pid>.+)_gathered(?:_(?P<amount>\d+))?$")
_HEAL_SELF_RE = re.compile(r"^(?P<pid>.+)_healed_self(?:_fallback)?_(?P<amount>\d+)$")
_HEAL_ALLY_RE = re.compile(
    r"^(?P<pid>.+)_healed_ally_(?P<target>.+)_(?P<amount>\d+)$"
)
_PUSH_RE = re.compile(r"^(?P<pid>.+)_pushed_(?P<target>.+)$")
_PUSH_BLOCKED_RE = re.compile(r"^(?P<pid>.+)_push_blocked_(?P<target>.+)$")
_BOSS_ATTACK_RE = re.compile(r"^boss_attacked_(?P<pid>.+)$")


@dataclass(frozen=True)
class TileEffect:
    kind: str
    tile_x: int
    tile_y: int
    duration_ms: int = _EFFECT_MS
    age_ms: int = 0
    seeds: tuple[float, ...] = field(default_factory=tuple)


def _positions_from_render_state(render_state: dict) -> dict[str, tuple[int, int]]:
    positions: dict[str, tuple[int, int]] = {}
    for entity in render_state.get("entities", ()):
        pid = str(entity["id"])
        px, py = entity["position"]
        positions[pid] = (int(px), int(py))
    boss = render_state.get("boss_entity")
    if boss:
        bx, by = boss["position"]
        positions["__boss__"] = (int(bx), int(by))
    return positions


def _make_seeds(count: int, salt: int) -> tuple[float, ...]:
    return tuple(((salt * 17 + i * 31) % 97) / 97.0 for i in range(count))


def spawn_effects_from_turn(
    turn_result,
    render_state: dict,
    *,
    scenario_id: str | None = None,
) -> list[TileEffect]:
    """Build tile effects from scenario turn events and post-turn positions."""
    positions = _positions_from_render_state(render_state)
    effects: list[TileEffect] = []
    is_mana_scenario = scenario_id in ("energy_stations", "mana_pools") or bool(
        render_state.get("station_capacities")
    )
    salt = 0

    def _at(pid: str, kind: str, *, duration_ms: int = _EFFECT_MS) -> None:
        nonlocal salt
        pos = positions.get(pid)
        if pos is None:
            return
        seed_count = 10 if kind in ("attack", "hit") else 8
        effects.append(
            TileEffect(
                kind=kind,
                tile_x=pos[0],
                tile_y=pos[1],
                duration_ms=duration_ms,
                seeds=_make_seeds(seed_count, salt),
            )
        )
        salt += 1

    def _at_xy(x: int, y: int, kind: str, *, duration_ms: int = _EFFECT_MS) -> None:
        nonlocal salt
        effects.append(
            TileEffect(
                kind=kind,
                tile_x=x,
                tile_y=y,
                duration_ms=duration_ms,
                seeds=_make_seeds(10 if kind in ("attack", "hit") else 8, salt),
            )
        )
        salt += 1

    for event in turn_result.events:
        if m := _GATHER_RE.match(event):
            gather_kind = "gather_mana" if is_mana_scenario else "gather_resource"
            _at(m.group("pid"), gather_kind)
            continue

        if event.endswith("_attacked_boss"):
            pid = event[: -len("_attacked_boss")]
            _at(pid, "attack")
            boss_pos = positions.get("__boss__")
            if boss_pos is not None:
                _at_xy(boss_pos[0], boss_pos[1], "hit")
            continue

        if m := _BOSS_ATTACK_RE.match(event):
            _at(m.group("pid"), "hit")
            boss_pos = positions.get("__boss__")
            if boss_pos is not None:
                _at_xy(boss_pos[0], boss_pos[1], "attack", duration_ms=_EFFECT_MS_SHORT)
            continue

        if m := _HEAL_SELF_RE.match(event):
            if int(m.group("amount")) > 0:
                _at(m.group("pid"), "heal")
            continue

        if m := _HEAL_ALLY_RE.match(event):
            if int(m.group("amount")) <= 0:
                continue
            _at(m.group("pid"), "heal", duration_ms=_EFFECT_MS_SHORT)
            _at(m.group("target"), "healed")
            continue

        if m := _PUSH_RE.match(event):
            _at(m.group("pid"), "attack")
            _at(m.group("target"), "hit")
            continue

        if m := _PUSH_BLOCKED_RE.match(event):
            _at(m.group("pid"), "attack", duration_ms=_EFFECT_MS_SHORT)
            _at(m.group("target"), "hit", duration_ms=_EFFECT_MS_SHORT)

    return effects


class ActionEffectManager:
    """Tracks active tile effects and advances them each frame."""

    def __init__(self) -> None:
        self._effects: list[TileEffect] = []

    def clear(self) -> None:
        self._effects.clear()

    def spawn_from_turn(
        self,
        turn_result,
        render_state: dict,
        *,
        scenario_id: str | None = None,
    ) -> None:
        self._effects.extend(
            spawn_effects_from_turn(
                turn_result,
                render_state,
                scenario_id=scenario_id,
            )
        )

    def update(self, dt_ms: int) -> None:
        alive: list[TileEffect] = []
        for effect in self._effects:
            age = effect.age_ms + dt_ms
            if age < effect.duration_ms:
                alive.append(
                    TileEffect(
                        kind=effect.kind,
                        tile_x=effect.tile_x,
                        tile_y=effect.tile_y,
                        duration_ms=effect.duration_ms,
                        age_ms=age,
                        seeds=effect.seeds,
                    )
                )
        self._effects = alive

    def draw(
        self,
        surface: pygame.Surface,
        *,
        origin_x: int,
        origin_y: int,
    ) -> None:
        for effect in self._effects:
            _draw_effect(surface, effect, origin_x=origin_x, origin_y=origin_y)


def _tile_center(effect: TileEffect, *, origin_x: int, origin_y: int) -> tuple[int, int]:
    cx = origin_x + effect.tile_x * TILE_SIZE + TILE_SIZE // 2
    cy = origin_y + effect.tile_y * TILE_SIZE + TILE_SIZE // 2
    return cx, cy


def _draw_effect(
    surface: pygame.Surface,
    effect: TileEffect,
    *,
    origin_x: int,
    origin_y: int,
) -> None:
    t = effect.age_ms / max(effect.duration_ms, 1)
    cx, cy = _tile_center(effect, origin_x=origin_x, origin_y=origin_y)
    # Hold full strength longer, then fade out in the last third.
    fade = max(0.0, 1.0 - max(0.0, (t - 0.55) / 0.45))

    if effect.kind == "attack":
        _draw_attack_burst(surface, cx, cy, t, fade, effect.seeds)
    elif effect.kind == "hit":
        _draw_hit_flash(surface, cx, cy, t, fade, effect.seeds)
    elif effect.kind in ("heal", "healed"):
        _draw_heal_sparkles(surface, cx, cy, t, fade, effect.seeds, soft=effect.kind == "healed")
    elif effect.kind == "gather_mana":
        _draw_gather_sparkles(surface, cx, cy, t, fade, effect.seeds, mana=True)
    elif effect.kind == "gather_resource":
        _draw_gather_sparkles(surface, cx, cy, t, fade, effect.seeds, mana=False)


def _draw_attack_burst(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    t: float,
    fade: float,
    seeds: tuple[float, ...],
) -> None:
    core_r = max(4, TILE_SIZE // 6)
    core_alpha = int(220 * fade * max(0.0, 1.0 - t * 1.4))
    if core_alpha > 10:
        core = pygame.Surface((core_r * 2 + 6, core_r * 2 + 6), pygame.SRCALPHA)
        pygame.draw.circle(core, (255, 240, 180, core_alpha), (core_r + 3, core_r + 3), core_r)
        surface.blit(core, (cx - core_r - 3, cy - core_r - 3))

    ring_r = int((TILE_SIZE * 0.2) + t * TILE_SIZE * 0.48)
    ring_alpha = int(220 * fade)
    if ring_alpha > 8:
        ring = pygame.Surface((ring_r * 2 + 8, ring_r * 2 + 8), pygame.SRCALPHA)
        center = ring_r + 4
        pygame.draw.circle(ring, (255, 90, 30, ring_alpha // 2), (center, center), ring_r)
        pygame.draw.circle(ring, (255, 160, 50, ring_alpha), (center, center), ring_r, 3)
        surface.blit(ring, (cx - center, cy - center))

    for seed in seeds:
        angle = seed * math.tau + t * 1.1
        dist = (0.12 + seed * 0.55 + t * 0.65) * TILE_SIZE * 0.52
        px = int(cx + math.cos(angle) * dist)
        py = int(cy + math.sin(angle) * dist)
        alpha = int(255 * fade * (0.65 + seed * 0.35))
        size = max(3, int(3 + seed * 3))
        _draw_dot(surface, px, py, size, (255, 150, 40, alpha), glow=True)

    slash_len = int(TILE_SIZE * 0.34 * (0.55 + t * 0.45))
    slash_alpha = int(240 * fade)
    if slash_alpha > 8 and slash_len > 2:
        pad = slash_len + 6
        overlay = pygame.Surface((pad * 2, pad * 2), pygame.SRCALPHA)
        ox, oy = pad, pad
        for angle in (0.35, 2.1):
            x1 = int(ox + math.cos(angle) * slash_len)
            y1 = int(oy + math.sin(angle) * slash_len)
            x2 = int(ox - math.cos(angle) * slash_len)
            y2 = int(oy - math.sin(angle) * slash_len)
            pygame.draw.line(
                overlay, (255, 220, 120, slash_alpha // 2), (x1, y1), (x2, y2), 5,
            )
            pygame.draw.line(
                overlay, (255, 255, 210, slash_alpha), (x1, y1), (x2, y2), 2,
            )
        surface.blit(overlay, (cx - pad, cy - pad))


def _draw_hit_flash(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    t: float,
    fade: float,
    seeds: tuple[float, ...],
) -> None:
    half = TILE_SIZE // 2 - 1
    flash_alpha = int(165 * fade * max(0.0, 1.0 - t * 0.5))
    if flash_alpha > 6:
        flash = pygame.Surface((half * 2, half * 2), pygame.SRCALPHA)
        flash.fill((255, 40, 40, flash_alpha))
        pygame.draw.rect(flash, (255, 120, 120, min(255, flash_alpha + 40)), flash.get_rect(), 2)
        surface.blit(flash, (cx - half, cy - half))

    shock_r = int(TILE_SIZE * 0.18 + t * TILE_SIZE * 0.28)
    shock_alpha = int(180 * fade)
    if shock_alpha > 8:
        shock = pygame.Surface((shock_r * 2 + 6, shock_r * 2 + 6), pygame.SRCALPHA)
        center = shock_r + 3
        pygame.draw.circle(shock, (255, 80, 80, shock_alpha), (center, center), shock_r, 3)
        surface.blit(shock, (cx - center, cy - center))

    for seed in seeds:
        angle = seed * math.tau
        dist = (0.5 - t * 0.4 + seed * 0.1) * TILE_SIZE * 0.5
        px = int(cx + math.cos(angle) * dist)
        py = int(cy + math.sin(angle) * dist)
        alpha = int(255 * fade)
        size = max(3, int(3 + seed * 2))
        _draw_dot(surface, px, py, size, (255, 70, 70, alpha), glow=True)


def _draw_heal_sparkles(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    t: float,
    fade: float,
    seeds: tuple[float, ...],
    *,
    soft: bool,
) -> None:
    glow_r = int(TILE_SIZE * 0.22 + t * TILE_SIZE * 0.12)
    glow_alpha = int((120 if soft else 160) * fade)
    if glow_alpha > 8:
        glow = pygame.Surface((glow_r * 2 + 6, glow_r * 2 + 6), pygame.SRCALPHA)
        center = glow_r + 3
        pygame.draw.circle(glow, (80, 255, 160, glow_alpha // 2), (center, center), glow_r)
        surface.blit(glow, (cx - center, cy - center))

    lift = t * TILE_SIZE * 0.55
    core = (80, 255, 140) if not soft else (140, 255, 190)
    for seed in seeds:
        px = int(cx + (seed - 0.5) * TILE_SIZE * 0.42)
        py = int(cy - lift - seed * TILE_SIZE * 0.14)
        alpha = int((200 if soft else 255) * fade)
        size = max(3, int(3 + seed * 3)) if not soft else max(3, int(2 + seed * 2))
        _draw_dot(surface, px, py, size, (*core, alpha), glow=True)

    if not soft and fade > 0.2:
        plus_alpha = int(220 * fade)
        arm = max(5, TILE_SIZE // 5)
        pad = arm + 4
        overlay = pygame.Surface((pad * 2, pad * 2), pygame.SRCALPHA)
        ox, oy = pad, pad
        pygame.draw.line(
            overlay, (*core, plus_alpha // 2), (ox - arm, oy), (ox + arm, oy), 4,
        )
        pygame.draw.line(
            overlay, (*core, plus_alpha // 2), (ox, oy - arm), (ox, oy + arm), 4,
        )
        pygame.draw.line(
            overlay, (240, 255, 240, plus_alpha), (ox - arm, oy), (ox + arm, oy), 2,
        )
        pygame.draw.line(
            overlay, (240, 255, 240, plus_alpha), (ox, oy - arm), (ox, oy + arm), 2,
        )
        surface.blit(overlay, (cx - pad, cy - pad))


def _draw_gather_sparkles(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    t: float,
    fade: float,
    seeds: tuple[float, ...],
    *,
    mana: bool,
) -> None:
    ring_r = int(TILE_SIZE * 0.16 + t * TILE_SIZE * 0.22)
    ring_alpha = int(170 * fade)
    if ring_alpha > 8:
        ring_color = (130, 90, 255, ring_alpha) if mana else (255, 190, 50, ring_alpha)
        ring = pygame.Surface((ring_r * 2 + 6, ring_r * 2 + 6), pygame.SRCALPHA)
        center = ring_r + 3
        pygame.draw.circle(ring, ring_color, (center, center), ring_r, 2)
        surface.blit(ring, (cx - center, cy - center))

    lift = t * TILE_SIZE * 0.52
    if mana:
        colors = ((170, 120, 255), (210, 170, 255), (120, 210, 255))
    else:
        colors = ((255, 210, 60), (255, 150, 30), (255, 240, 130))

    for i, seed in enumerate(seeds):
        wobble = math.sin(t * math.pi * 2 + seed * 6.0) * TILE_SIZE * 0.12
        px = int(cx + wobble + (seed - 0.5) * TILE_SIZE * 0.36)
        py = int(cy - lift - i * 3)
        color = colors[i % len(colors)]
        alpha = int(255 * fade)
        _draw_dot(surface, px, py, max(3, int(3 + seed * 2)), (*color, alpha), glow=True)


def _draw_dot(
    surface: pygame.Surface,
    x: int,
    y: int,
    radius: int,
    rgba: tuple[int, int, int, int],
    *,
    glow: bool = False,
) -> None:
    if rgba[3] <= 0:
        return
    pad = 3 if glow else 1
    d = radius * 2 + pad * 2
    dot = pygame.Surface((d, d), pygame.SRCALPHA)
    center = radius + pad
    if glow and radius > 1:
        glow_alpha = max(20, rgba[3] // 3)
        pygame.draw.circle(dot, (*rgba[:3], glow_alpha), (center, center), radius + 2)
    pygame.draw.circle(dot, rgba, (center, center), radius)
    if glow:
        highlight = (min(255, rgba[0] + 60), min(255, rgba[1] + 60), min(255, rgba[2] + 60), rgba[3])
        pygame.draw.circle(dot, highlight, (center, center), max(1, radius // 2))
    surface.blit(dot, (x - center, y - center))
