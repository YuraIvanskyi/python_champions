"""Boss Fight starter bot.

Available actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, ATTACK, HEAL_SELF, HEAL_ALLY, WAIT

state methods (BossFightView):
  my_hp()           — current HP
  my_max_hp()       — max HP
  is_alive()        — True while HP > 0
  boss_x()          — boss column
  boss_y()          — boss row
  boss_hp()         — current boss HP
  boss_max_hp()     — max boss HP
  is_boss_adjacent() — True when boss is orthogonally next to you
  ally_hp(player_id) — HP of a named ally, or None
  weakest_ally_id() — player_id of the living ally with the lowest HP, or None
  my_x(), my_y()    — your position
  is_walkable(x, y) — True if the tile can be entered
"""


def make_turn(state):
    # Heal self if critically low
    if state.my_hp() < 2:
        return "HEAL_SELF"

    # Attack boss if adjacent
    if state.is_boss_adjacent():
        return "ATTACK"

    # Move toward boss
    bx, by = state.boss_x(), state.boss_y()
    if bx > state.my_x():
        return "MOVE_RIGHT"
    if bx < state.my_x():
        return "MOVE_LEFT"
    if by > state.my_y():
        return "MOVE_DOWN"
    return "MOVE_UP"
