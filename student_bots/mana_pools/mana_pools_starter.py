"""Mana Pools starter bot.

Available actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, GATHER, ATTACK, WAIT

state methods (ManaPoolsView):
  my_energy()        — current mana level
  max_energy()       — maximum mana cap
  can_gather()       — True if adjacent to a pool with capacity > 0
  nearest_pool()  — (x, y) of closest pool, or None
  pools()         — all remaining pools as list of (x, y, capacity)
  adjacent_pools() — pools you can gather from: (x, y, capacity)
  my_x(), my_y()    — your position
  is_walkable(x, y) — True if the tile can be entered
  others_positions() — list of (player_id, x, y) for all other bots
"""


def make_turn(state):
    # Gather if standing next to a mana pool
    if state.can_gather():
        return "GATHER"

    # Move toward the nearest pool
    nearest = state.nearest_pool()
    if nearest:
        nx, ny = nearest
        if nx > state.my_x():
            return "MOVE_RIGHT"
        if nx < state.my_x():
            return "MOVE_LEFT"
        if ny > state.my_y():
            return "MOVE_DOWN"
        return "MOVE_UP"

    return "WAIT"
