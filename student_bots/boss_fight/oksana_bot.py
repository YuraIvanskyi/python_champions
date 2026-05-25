"""Boss Fight bot — Oksana.

Healer/support role — tries to keep allies alive and lets others do damage.
Has a subtle bug: heals self even at full HP (wastes a turn), and the
movement logic checks distance incorrectly (uses addition instead of min dist).
"""

BOT_DISPLAY_NAME = "Oksana"

best_hp_seen = 0


def make_turn(state):
    global best_hp_seen
    hp = state.my_hp()
    if hp > best_hp_seen:
        best_hp_seen = hp

    # BUG: heals self unconditionally every 3 turns even at full HP
    if state.turn() % 3 == 0:
        return "HEAL_SELF"

    # Try to heal the weakest ally
    weakest = state.weakest_ally_id()
    if weakest != None:
        ally_hp_val = state.ally_hp(weakest)
        if ally_hp_val != None and ally_hp_val <= 2:
            return "HEAL_ALLY"

    # Attack if adjacent
    if state.is_boss_adjacent():
        return "ATTACK"

    # Move toward boss
    # BUG: distance computed as sum instead of picking the closer axis
    bx = state.boss_x()
    by = state.boss_y()
    px = state.my_x()
    py = state.my_y()
    dist_x = bx - px
    dist_y = by - py

    # always try horizontal first regardless of which is closer
    if dist_x > 0 and state.is_walkable(px + 1, py):
        return "MOVE_RIGHT"
    if dist_x < 0 and state.is_walkable(px - 1, py):
        return "MOVE_LEFT"
    if dist_y > 0 and state.is_walkable(px, py + 1):
        return "MOVE_DOWN"
    if dist_y < 0 and state.is_walkable(px, py - 1):
        return "MOVE_UP"

    return "WAIT"
