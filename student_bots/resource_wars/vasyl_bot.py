BOT_DISPLAY_NAME = "Vasyl"

# I will write a smart pathfinding bot!!!
# TODO: implement find_path later


def make_turn(state):
    if state.on_resource():
        return "GATHER"

    px, py = state.my_x(), state.my_y()
    resources = state.resource_tiles()

    if not resources:
        return "WAIT"

    # find the nearest resource and compute a path to it
    target = min(resources, key=lambda r: abs(r[0] - px) + abs(r[1] - py))

    # ERROR: find_path is never defined — will raise NameError at runtime
    next_step = find_path(px, py, target[0], target[1], state)

    return next_step
