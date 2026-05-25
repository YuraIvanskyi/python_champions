BOT_DISPLAY_NAME = "Daryna"

visited_tiles = []
last_move = "WAIT"
turn_count = 0


def make_turn(state):
    global visited_tiles, last_move, turn_count
    turn_count = turn_count + 1

    if state.on_resource() == True:
        last_move = "GATHER"
        return "GATHER"

    px = state.my_x()
    py = state.my_y()

    visited_tiles.append((px, py))
    if len(visited_tiles) > 20:
        visited_tiles = visited_tiles[-20:]

    all_resources = state.resource_tiles()

    if len(all_resources) == 0:
        return "WAIT"

    # just go to the first one in the list (not necessarily closest)
    goal_x = all_resources[0][0]
    goal_y = all_resources[0][1]

    preferred = []
    if goal_x > px:
        preferred.append("MOVE_RIGHT")
    elif goal_x < px:
        preferred.append("MOVE_LEFT")
    if goal_y > py:
        preferred.append("MOVE_DOWN")
    elif goal_y < py:
        preferred.append("MOVE_UP")

    for move in preferred:
        if move == "MOVE_RIGHT":
            if state.is_walkable(px + 1, py) == True:
                last_move = move
                return move
        elif move == "MOVE_LEFT":
            if state.is_walkable(px - 1, py) == True:
                last_move = move
                return move
        elif move == "MOVE_DOWN":
            if state.is_walkable(px, py + 1) == True:
                last_move = move
                return move
        elif move == "MOVE_UP":
            if state.is_walkable(px, py - 1) == True:
                last_move = move
                return move
        else:
            pass

    # fallback: try any open direction
    if state.is_walkable(px + 1, py) == True:
        return "MOVE_RIGHT"
    if state.is_walkable(px, py + 1) == True:
        return "MOVE_DOWN"
    if state.is_walkable(px - 1, py) == True:
        return "MOVE_LEFT"
    if state.is_walkable(px, py - 1) == True:
        return "MOVE_UP"

    return "WAIT"
