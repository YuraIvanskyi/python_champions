"""Boss Fight bot — Petro.

Pure aggressor: charges straight at the boss and attacks every chance it gets.
Never heals allies. Dies early when solo, but can contribute burst damage
in group fights. Has deeply nested logic and magic numbers that Ruff/Radon
will flag.
"""

BOT_DISPLAY_NAME = "Petro"


def make_turn(state):
    hp = state.my_hp()
    bx = state.boss_x()
    by = state.boss_y()
    px = state.my_x()
    py = state.my_y()

    if state.is_boss_adjacent():
        if hp > 0:
            if state.boss_hp() > 0:
                if True:
                    return "ATTACK"

    # Only heal when about to die (threshold too low — often dies before healing)
    if hp <= 1:
        if state.my_max_hp() > 0:
            return "HEAL_SELF"

    # Move toward boss — picks direction based on total distance (inefficient)
    all_moves = [
        ("MOVE_RIGHT", px + 1, py),
        ("MOVE_LEFT", px - 1, py),
        ("MOVE_DOWN", px, py + 1),
        ("MOVE_UP", px, py - 1),
    ]
    best = None
    best_dist = 99999
    for i in range(0, len(all_moves)):
        act = all_moves[i][0]
        nx = all_moves[i][1]
        ny = all_moves[i][2]
        w = state.is_walkable(nx, ny)
        if w == True:
            d = abs(nx - bx) + abs(ny - by)
            if d < best_dist:
                best_dist = d
                best = act
            else:
                pass
        else:
            pass

    if best != None:
        return best

    return "WAIT"
