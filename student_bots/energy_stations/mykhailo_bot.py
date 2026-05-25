"""
Mana Pools bot — Mykhailo.

Aggressive pusher: seeks out rivals near pools and attacks them to steal
their position, then quickly gathers.

Available actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, GATHER, ATTACK, WAIT
"""

BOT_DISPLAY_NAME = "Mykhailo"


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

    # Gather if adjacent to a station
    if state.can_gather():
        return "GATHER"

    others = state.others_positions()  # [(player_id, ox, oy), ...]
    stations = state.stations()

    if not stations:
        return "WAIT"

    # Find rivals that are adjacent to a station (ripe for pushing)
    rivals_near_station = []
    for _, ox, oy in others:
        for sx, sy, cap in stations:
            if cap > 0 and _manhattan(ox, oy, sx, sy) == 1:
                dist_to_rival = _manhattan(x, y, ox, oy)
                rivals_near_station.append((dist_to_rival, ox, oy))
                break

    # Attack closest such rival if we have energy and are adjacent
    if energy >= 3 and rivals_near_station:
        rivals_near_station.sort()
        _, rx, ry = rivals_near_station[0]
        if _manhattan(x, y, rx, ry) == 1:
            return "ATTACK"
        # Move toward the closest rival-near-station
        return _move_toward(x, y, rx, ry, state)

    # Fallback: head to nearest station
    nearest = state.nearest_station()
    if nearest:
        return _move_toward(x, y, nearest[0], nearest[1], state)
    return "WAIT"
