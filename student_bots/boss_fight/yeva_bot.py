"""Boss Fight bot — Yeva.

Simple approach: always moves toward the boss and attacks.
Has a NameError bug — calls an undefined function `find_adjacent_boss_cell`
that was never implemented. Will crash at runtime when the boss is not adjacent.
"""

BOT_DISPLAY_NAME = "Yeva"


def make_turn(state):
    if state.is_boss_adjacent():
        return "ATTACK"

    if state.my_hp() < 2:
        return "HEAL_SELF"

    bx = state.boss_x()
    by = state.boss_y()
    px = state.my_x()
    py = state.my_y()

    # ERROR: find_adjacent_boss_cell is never defined — NameError at runtime
    target = find_adjacent_boss_cell(bx, by, state)

    if target is None:
        # fallback: just move toward boss directly
        if bx > px:
            return "MOVE_RIGHT"
        if bx < px:
            return "MOVE_LEFT"
        if by > py:
            return "MOVE_DOWN"
        return "MOVE_UP"

    tx, ty = target
    if tx > px:
        return "MOVE_RIGHT"
    if tx < px:
        return "MOVE_LEFT"
    if ty > py:
        return "MOVE_DOWN"
    return "MOVE_UP"
