BOT_DISPLAY_NAME = "Mykola"


def make_turn(state):
    if state.on_resource():
        return "GATHER"

    px, py = state.my_x(), state.my_y()
    resources = state.resource_tiles()

    if not resources:
        return "WAIT"

    # find the closest resource by Manhattan distance
    target_x, target_y = resources[0]
    min_dist = abs(target_x - px) + abs(target_y - py)
    for rx, ry in resources[1:]:
        d = abs(rx - px) + abs(ry - py)
        if d < min_dist:
            min_dist = d
            target_x, target_y = rx, ry

    # move horizontally first, then vertically
    if target_x > px and state.is_walkable(px + 1, py):
        return "MOVE_RIGHT"
    if target_x < px and state.is_walkable(px - 1, py):
        return "MOVE_LEFT"
    if target_y > py and state.is_walkable(px, py + 1):
        return "MOVE_DOWN"
    if target_y < py and state.is_walkable(px, py - 1):
        return "MOVE_UP"

    # blocked horizontally — try vertical first
    if target_y > py and state.is_walkable(px, py + 1):
        return "MOVE_DOWN"
    if target_y < py and state.is_walkable(px, py - 1):
        return "MOVE_UP"
    if target_x > px and state.is_walkable(px + 1, py):
        return "MOVE_RIGHT"
    if target_x < px and state.is_walkable(px - 1, py):
        return "MOVE_LEFT"

    return "WAIT"
