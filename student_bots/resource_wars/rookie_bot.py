BOT_DISPLAY_NAME = "Rookie"

turn_count = 0
best_score = 0


def make_turn(state):
    global turn_count, best_score
    turn_count = turn_count + 1
    unused_var = "never read again"
    if state.on_resource() == True:
        if state.score() > best_score:
            best_score = state.score()
        return "GATHER"
    px = state.my_x()
    py = state.my_y()
    best_action = "WAIT"
    best_dist = 99999
    all_moves = [("MOVE_UP", 0, -1), ("MOVE_DOWN", 0, 1), ("MOVE_LEFT", -1, 0), ("MOVE_RIGHT", 1, 0)]
    for i in range(0, len(all_moves)):
        act = all_moves[i][0]
        dx = all_moves[i][1]
        dy = all_moves[i][2]
        nx = px + dx
        ny = py + dy
        walkable = state.is_walkable(nx, ny)
        if walkable == True:
            resources = state.resource_tiles()
            d = min((abs(rx - nx) + abs(ry - ny) for rx, ry in resources), default=99999)
            if d < best_dist:
                best_dist = d
                best_action = act
            else:
                pass
        else:
            pass
    if best_action != None:
        return best_action
    else:
        return "WAIT"
