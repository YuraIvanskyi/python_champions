"""Localized bot-writing guide blocks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from engine.i18n import normalize_lang, translate

BlockKind = Literal["heading", "paragraph", "code", "bullet"]


@dataclass(frozen=True)
class GuideBlock:
    kind: BlockKind
    text: str = ""
    lines: tuple[str, ...] = ()


def guide_blocks_for_scenario(scenario_id: str, lang: str = "en") -> list[GuideBlock]:
    code = normalize_lang(lang)
    builders = {
        "resource_wars": _resource_wars_blocks,
        "boss_fight": _boss_fight_blocks,
        "energy_stations": _energy_stations_blocks,
    }
    fn = builders.get(scenario_id, _resource_wars_blocks)
    return list(fn(code))


def _h(lang: str, key: str) -> GuideBlock:
    return GuideBlock("heading", translate(key, lang=lang))


def _p(lang: str, key: str) -> GuideBlock:
    return GuideBlock("paragraph", translate(key, lang=lang))


def _c(lines: tuple[str, ...]) -> GuideBlock:
    return GuideBlock("code", lines=lines)


def _resource_wars_blocks(lang: str) -> list[GuideBlock]:
    return [
        _h(lang, "guide.rw.goal"),
        _p(lang, "guide.rw.goal_body"),
        _h(lang, "guide.rw.file"),
        _p(lang, "guide.rw.file_body"),
        _c((
            "# Optional — shown in the UI (sandbox-safe)",
            'BOT_DISPLAY_NAME = "Your Bot Name"',
            "",
            "def make_turn(state):",
            "    # Return one action string (see Actions)",
            "    ...",
        )),
        _p(lang, "guide.rw.advanced"),
        _c((
            "from engine.core.bot_base import BotBase",
            "",
            "class MyBot(BotBase):",
            "    def make_turn(self, state):",
            "        ...",
        )),
        _h(lang, "guide.rw.actions"),
        _c((
            "# Return one of these strings from make_turn:",
            '"MOVE_UP"',
            '"MOVE_DOWN"',
            '"MOVE_LEFT"',
            '"MOVE_RIGHT"    # move one cell',
            '"GATHER"        # on a resource tile (state.on_resource())',
            '"WAIT"          # skip movement this turn',
        )),
        _h(lang, "guide.rw.state"),
        _c((
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
        _h(lang, "guide.rw.tips"),
        _p(lang, "guide.rw.tips1"),
        _p(lang, "guide.rw.tips2"),
        _p(lang, "guide.rw.starter"),
    ]


def _boss_fight_blocks(lang: str) -> list[GuideBlock]:
    return [
        _h(lang, "guide.bf.goal"),
        _p(lang, "guide.bf.goal_body"),
        _h(lang, "guide.bf.file"),
        _p(lang, "guide.bf.file_body"),
        _c((
            'BOT_DISPLAY_NAME = "Your Bot Name"',
            "",
            "def make_turn(state):",
            "    # See actions and state functions below",
            "    ...",
        )),
        _h(lang, "guide.bf.actions"),
        _c((
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
        _h(lang, "guide.bf.state"),
        _c((
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
        _h(lang, "guide.bf.tips"),
        _p(lang, "guide.bf.tips1"),
        _p(lang, "guide.bf.starter"),
    ]


def _energy_stations_blocks(lang: str) -> list[GuideBlock]:
    return [
        _h(lang, "guide.es.goal"),
        _p(lang, "guide.es.goal_body"),
        _h(lang, "guide.es.file"),
        _p(lang, "guide.es.file_body"),
        _c((
            'BOT_DISPLAY_NAME = "Your Bot Name"',
            "",
            "def make_turn(state):",
            "    # See actions and state functions below",
            "    ...",
        )),
        _h(lang, "guide.es.actions"),
        _c((
            "# Return one of these strings from make_turn:",
            '"MOVE_UP"',
            '"MOVE_DOWN"',
            '"MOVE_LEFT"',
            '"MOVE_RIGHT"    # costs mana to move',
            '"GATHER"        # when state.can_gather()',
            '"ATTACK"        # push a nearby rival (costs more mana)',
            '"WAIT"',
        )),
        _h(lang, "guide.es.state"),
        _c((
            "state.my_energy()",
            "state.max_energy()",
            "state.can_gather()",
            "state.adjacent_stations()   # pools next to you",
            "state.nearest_station()     # (x, y) or None",
            "state.stations()            # (x, y, capacity)",
            "state.others_positions()    # rival locations",
            "# Also: my_x(), my_y(), is_walkable(x, y), turn(), …",
        )),
        _h(lang, "guide.es.tips"),
        _p(lang, "guide.es.tips1"),
        _p(lang, "guide.es.starter"),
    ]
