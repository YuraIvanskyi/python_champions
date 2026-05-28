"""
Mana Pools bot — Ruslan.

Mana hoarder: focuses on filling up to max mana as fast as possible.
Chains gathers from multiple pools, uses ATTACK only to clear the way.

Available actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, GATHER, ATTACK, WAIT
"""

BOT_DISPLAY_NAME = "Ruslan"


def _manhattan(ax, ay, bx, by):
    return abs(ax - bx) + abs(ay - by)


def _move_toward(sx, sy, tx, ty, state):
    options = []
    if tx > sx:
        options.append(("MOVE_RIGHT", sx + 1, sy))
    elif tx < sx:
        options.append(("MOVE_LEFT", sx - 1, sy))
    if ty > sy:
        options.append(("MOVE_DOWN", sx, sy + 1))
    elif ty < sy:
        options.append(("MOVE_UP", sx, sy - 1))
    for action, nx, ny in options:
        if state.is_walkable(nx, ny):
            return action
    for action, nx, ny in reversed(options):
        if state.is_walkable(nx, ny):
            return action
    return "WAIT"


def make_turn(state):
    x, y = state.my_x(), state.my_y()
    energy = state.my_energy()
    max_e = state.max_energy()

    # Gather if possible — always prioritise filling up
    if state.can_gather():
        return "GATHER"

    # If nearly full, wait near a station (let it refill next gather)
    adj = state.adjacent_pools()
    if adj and energy >= max_e - 5:
        return "WAIT"

    # Attack a blocking rival only if they are right in our path to a station
    others = state.others_positions()
    stations = state.pools()
    if not stations:
        return "WAIT"

    nearest = state.nearest_pool()
    if not nearest:
        return "WAIT"

    tx, ty = nearest

    # Check if a rival is directly blocking the path (adjacent to us, in target direction)
    if energy >= 3:
        for _, ox, oy in others:
            if _manhattan(x, y, ox, oy) == 1:
                # They're between us and the station
                if _manhattan(ox, oy, tx, ty) < _manhattan(x, y, tx, ty):
                    return "ATTACK"

    return _move_toward(x, y, tx, ty, state)
