"""Boss Fight bot — Bohdan.

Attacks the boss and heals when low. Works fine but has several style issues
the Code Coach will flag: == True comparisons, magic numbers, unused variable,
and a very long line.
"""

BOT_DISPLAY_NAME = "Bohdan"

turn_count = 0
heal_count = 0


def make_turn(state):
    global turn_count, heal_count
    turn_count = turn_count + 1
    unused_note = "TODO: add dodge logic someday"

    bx = state.boss_x()
    by = state.boss_y()
    px = state.my_x()
    py = state.my_y()
    hp = state.my_hp()

    if state.is_boss_adjacent() == True:
        if hp <= 1 == True:
            heal_count = heal_count + 1
            return "HEAL_SELF"
        return "ATTACK"

    if hp <= 2:
        heal_count = heal_count + 1
        return "HEAL_SELF"

    # move toward boss — pick the axis with the bigger gap first
    if abs(bx - px) >= abs(by - py):
        if bx > px:
            if state.is_walkable(px + 1, py) == True:
                return "MOVE_RIGHT"
        elif bx < px:
            if state.is_walkable(px - 1, py) == True:
                return "MOVE_LEFT"
        if by > py:
            if state.is_walkable(px, py + 1) == True:
                return "MOVE_DOWN"
        elif by < py:
            if state.is_walkable(px, py - 1) == True:
                return "MOVE_UP"
    else:
        if by > py:
            if state.is_walkable(px, py + 1) == True:
                return "MOVE_DOWN"
        elif by < py:
            if state.is_walkable(px, py - 1) == True:
                return "MOVE_UP"
        if bx > px:
            if state.is_walkable(px + 1, py) == True:
                return "MOVE_RIGHT"
        elif bx < px:
            if state.is_walkable(px - 1, py) == True:
                return "MOVE_LEFT"

    return "WAIT"
