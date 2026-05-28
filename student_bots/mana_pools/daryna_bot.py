"""
Mana Pools bot — Daryna.

Balanced explorer: picks a pool that no one else is near,
gathers efficiently, and retreats when rivals get too close.

Available actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, GATHER, ATTACK, WAIT
"""

BOT_DISPLAY_NAME = "Daryna"


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


def _move_away_from(sx, sy, fx, fy, state):
    """Try to move one step away from (fx, fy)."""
    dx = sx - fx
    dy = sy - fy
    options = []
    if dx > 0:
        options.append(("MOVE_RIGHT", sx + 1, sy))
    elif dx < 0:
        options.append(("MOVE_LEFT", sx - 1, sy))
    if dy > 0:
        options.append(("MOVE_DOWN", sx, sy + 1))
    elif dy < 0:
        options.append(("MOVE_UP", sx, sy - 1))
    for action, nx, ny in options:
        if state.is_walkable(nx, ny):
            return action
    return "WAIT"


def make_turn(state):
    x, y = state.my_x(), state.my_y()

    # Gather if adjacent to a station
    if state.can_gather():
        # Check if any rival is adjacent to us (potential push threat)
        others = state.others_positions()
        threatened = any(_manhattan(x, y, ox, oy) == 1 for _, ox, oy in others)
        if not threatened:
            return "GATHER"
        # Gather anyway but note the threat — energy is worth it
        return "GATHER"

    others = state.others_positions()
    stations = state.pools()
    if not stations:
        return "WAIT"

    # Find an uncrowded station: no rivals within distance 3
    rival_positions = [(ox, oy) for _, ox, oy in others]

    def rival_closeness(station):
        sx, sy, _ = station
        if not rival_positions:
            return 999
        return min(_manhattan(sx, sy, rx, ry) for rx, ry in rival_positions)

    # Pick station with best (capacity, rival-distance) score
    best = max(
        stations,
        key=lambda s: (rival_closeness(s), s[2], -(_manhattan(x, y, s[0], s[1]))),
    )
    return _move_toward(x, y, best[0], best[1], state)
