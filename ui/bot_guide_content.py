"""Scenario-specific bot-writing help shown in the launcher guide screen."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BlockKind = Literal["heading", "paragraph", "code", "bullet"]


@dataclass(frozen=True)
class GuideBlock:
    kind: BlockKind
    text: str = ""
    lines: tuple[str, ...] = ()


def guide_blocks_for_scenario(scenario_id: str) -> list[GuideBlock]:
    builders = {
        "resource_wars": _resource_wars_blocks,
        "boss_fight": _boss_fight_blocks,
        "energy_stations": _energy_stations_blocks,
    }
    return list(builders.get(scenario_id, _resource_wars_blocks)())


def _resource_wars_blocks() -> list[GuideBlock]:
    return [
        GuideBlock("heading", "Goal"),
        GuideBlock(
            "paragraph",
            "Collect resources from tiles on the map. Each successful GATHER adds to your "
            "score. After 50 turns (or when the match ends), the bot with the highest "
            "score wins. Obstacles block movement; plan paths with state.is_walkable().",
        ),
        GuideBlock("heading", "File structure"),
        GuideBlock(
            "paragraph",
            "Save one .py file per bot. The engine loads it and calls make_turn(state) "
            "once per turn. You may use a simple function or a class — see boilerplate below.",
        ),
        GuideBlock("code", lines=(
            "# Optional — shown in the UI (sandbox-safe)",
            'BOT_DISPLAY_NAME = "Your Bot Name"',
            "",
            "def make_turn(state):",
            "    # Return one action string (see Actions)",
            "    ...",
        )),
        GuideBlock(
            "paragraph",
            "Advanced style: subclass BotBase and implement make_turn(self, state).",
        ),
        GuideBlock("code", lines=(
            "from engine.core.bot_base import BotBase",
            "",
            "class MyBot(BotBase):",
            "    def make_turn(self, state):",
            "        ...",
        )),
        GuideBlock("heading", "Actions (return a string)"),
        GuideBlock("code", lines=(
            "# Return one of these strings from make_turn:",
            '"MOVE_UP"',
            '"MOVE_DOWN"',
            '"MOVE_LEFT"',
            '"MOVE_RIGHT"    # move one cell',
            '"GATHER"        # on a resource tile (state.on_resource())',
            '"WAIT"          # skip movement this turn',
        )),
        GuideBlock("heading", "Helpful functions on state"),
        GuideBlock("code", lines=(
            "state.my_x()",
            "state.my_y()",
            "state.position()           # (x, y)",
            "state.score()              # resources collected so far",
            "state.on_resource()        # True on a resource tile",
            "state.is_walkable(x, y)    # can you enter that cell?",
            "state.resource_tiles()     # list of (x, y) resources",
            "state.others_positions()   # (player_id, x, y) of rivals",
            "state.turn()",
            "state.map_width()",
            "state.map_height()",
        )),
        GuideBlock("heading", "Tips"),
        GuideBlock(
            "paragraph",
            "Check on_resource() before GATHER. Pick the move that gets you closer to "
            "the nearest resource (Manhattan distance). In classroom mode, several bots "
            "share the map — use others_positions() to avoid crowding.",
        ),
        GuideBlock(
            "paragraph",
            "Avoid os, subprocess, socket, and other blocked imports. Each turn has a "
            "time limit; heavy loops may forfeit the turn.",
        ),
        GuideBlock(
            "paragraph",
            "Starter path: student_bots/resource_wars/example_bot.py",
        ),
    ]


def _boss_fight_blocks() -> list[GuideBlock]:
    return [
        GuideBlock("heading", "Goal"),
        GuideBlock(
            "paragraph",
            "Cooperative PvE: your bot and allies fight a boss on a 10×10 map. Reduce "
            "boss HP to zero before turns run out (200 max). When your HP hits 0 you are "
            "out for the rest of the fight — heal before that happens.",
        ),
        GuideBlock("heading", "File structure"),
        GuideBlock(
            "paragraph",
            "One .py file per bot. Each turn you get a state object with boss and HP info.",
        ),
        GuideBlock("code", lines=(
            'BOT_DISPLAY_NAME = "Your Bot Name"',
            "",
            "def make_turn(state):",
            "    # See actions and state functions below",
            "    ...",
        )),
        GuideBlock("heading", "Actions (return a string)"),
        GuideBlock("code", lines=(
            "# Return one of these strings from make_turn:",
            '"MOVE_UP"',
            '"MOVE_DOWN"',
            '"MOVE_LEFT"',
            '"MOVE_RIGHT"',
            '"ATTACK"        # when state.is_boss_adjacent()',
            '"HEAL_SELF"     # restore your HP',
            '"HEAL_ALLY"     # heal weakest living ally',
            '"WAIT"',
        )),
        GuideBlock("heading", "Helpful functions on state"),
        GuideBlock("code", lines=(
            "state.my_hp()",
            "state.my_max_hp()",
            "state.is_alive()",
            "state.boss_x()",
            "state.boss_y()",
            "state.boss_hp()",
            "state.boss_max_hp()",
            "state.is_boss_adjacent()",
            "state.ally_hp(player_id)",
            "state.weakest_ally_id()",
            "# Also: my_x(), my_y(), is_walkable(x, y), turn(), …",
        )),
        GuideBlock("heading", "Tips"),
        GuideBlock(
            "paragraph",
            "Move next to the boss, then ATTACK. Use HEAL_SELF when HP is low. In "
            "multi-player practice, HEAL_ALLY helps a weak ally stay in the fight. "
            "Practice mode adds one AI ally; classroom mode is students only.",
        ),
        GuideBlock(
            "paragraph",
            "Starter path: student_bots/boss_fight/boss_fight_starter.py",
        ),
    ]


def _energy_stations_blocks() -> list[GuideBlock]:
    return [
        GuideBlock("heading", "Goal"),
        GuideBlock(
            "paragraph",
            "Competitive PvP on a 20×10 map. Gather mana from glowing pools (stations). "
            "Highest total mana when turns end wins. Moving and attacking spend mana; "
            "gathering refills it up to max_energy.",
        ),
        GuideBlock("heading", "File structure"),
        GuideBlock(
            "paragraph",
            "One .py file per bot. Each turn you get a state object with mana and pool info.",
        ),
        GuideBlock("code", lines=(
            'BOT_DISPLAY_NAME = "Your Bot Name"',
            "",
            "def make_turn(state):",
            "    # See actions and state functions below",
            "    ...",
        )),
        GuideBlock("heading", "Actions (return a string)"),
        GuideBlock("code", lines=(
            "# Return one of these strings from make_turn:",
            '"MOVE_UP"',
            '"MOVE_DOWN"',
            '"MOVE_LEFT"',
            '"MOVE_RIGHT"    # costs mana to move',
            '"GATHER"        # when state.can_gather()',
            '"ATTACK"        # push a nearby rival (costs more mana)',
            '"WAIT"',
        )),
        GuideBlock("heading", "Helpful functions on state"),
        GuideBlock("code", lines=(
            "state.my_energy()",
            "state.max_energy()",
            "state.can_gather()",
            "state.adjacent_stations()   # pools next to you",
            "state.nearest_station()     # (x, y) or None",
            "state.stations()            # (x, y, capacity)",
            "state.others_positions()    # rival locations",
            "# Also: my_x(), my_y(), is_walkable(x, y), turn(), …",
        )),
        GuideBlock("heading", "Tips"),
        GuideBlock(
            "paragraph",
            "Prioritize GATHER when next to a pool with capacity. Use nearest_station() "
            "to navigate. ATTACK can block a rival from your pool but costs more mana than "
            "moving — spend wisely. Empty pools stay on the map but have capacity 0.",
        ),
        GuideBlock(
            "paragraph",
            "Starter path: student_bots/energy_stations/energy_stations_starter.py",
        ),
    ]
