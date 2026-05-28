"""
Mana Pools bot — Olena.

Greedy gatherer: always heads to the highest-capacity pool.
Avoids approaching bots when mana is low to dodge pushes.

Available actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, GATHER, ATTACK, WAIT
"""

BOT_DISPLAY_NAME = "Olena"


def _move_toward(sx, sy, tx, ty, state):
    """Return best orthogonal move toward (tx, ty), or WAIT if stuck."""
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

    # Gather if possible
    if state.can_gather():
        return "GATHER"

    # Pick the richest station by capacity (and closest as tiebreaker)
    stations = state.pools()
    if not stations:
        return "WAIT"

    target = max(
        stations,
        key=lambda s: (s[2], -(abs(s[0] - x) + abs(s[1] - y))),
    )
    return _move_toward(x, y, target[0], target[1], state)
