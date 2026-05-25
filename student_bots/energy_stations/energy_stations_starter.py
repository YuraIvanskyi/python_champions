"""Energy Stations starter bot.

Available actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, GATHER, ATTACK, WAIT

state methods (EnergyStationsView):
  my_energy()        — current energy level
  max_energy()       — maximum energy cap
  can_gather()       — True if adjacent to a station with capacity > 0
  nearest_station()  — (x, y) of closest station, or None
  stations()         — all remaining stations as list of (x, y, capacity)
  adjacent_stations() — stations you can gather from: (x, y, capacity)
  my_x(), my_y()    — your position
  is_walkable(x, y) — True if the tile can be entered
  others_positions() — list of (player_id, x, y) for all other bots
"""


def make_turn(state):
    # Gather if standing next to a station
    if state.can_gather():
        return "GATHER"

    # Move toward the nearest station
    nearest = state.nearest_station()
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
