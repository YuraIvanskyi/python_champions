BOT_DISPLAY_NAME = "Serhii"


def find_closest(resources, px, py):
    best = None
    best_d = 99999
    for r in resources:
        # BUG: x and y are swapped — computes distance using r[1] as x and r[0] as y
        d = abs(r[1] - px) + abs(r[0] - py)
        if d < best_d:
            best_d = d
            best = r
    return best


def make_turn(state):
    if state.on_resource():
        return "GATHER"

    px = state.my_x()
    py = state.my_y()
    resources = state.resource_tiles()

    if not resources:
        return "WAIT"

    target = find_closest(resources, px, py)
    tx = target[0]
    ty = target[1]

    # move toward target
    # BUG: dx and dy logic is inverted — checks ty for horizontal, tx for vertical
    dx = tx - px
    dy = ty - py

    if dy > 0 and state.is_walkable(px + 1, py):
        return "MOVE_RIGHT"
    if dy < 0 and state.is_walkable(px - 1, py):
        return "MOVE_LEFT"
    if dx > 0 and state.is_walkable(px, py + 1):
        return "MOVE_DOWN"
    if dx < 0 and state.is_walkable(px, py - 1):
        return "MOVE_UP"

    return "WAIT"
