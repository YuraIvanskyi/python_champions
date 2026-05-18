"""
Example student bot for Resource Wars.

Allowed API:
  - game_state["position"] -> [x, y]
  - game_state["resources"] -> int (score)
  - game_state["on_resource"] -> bool
  - game_state["visible_tiles"] -> list of {x, y, type}
  - game_state["map_width"], game_state["map_height"]

Return one of: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, GATHER, WAIT
"""


def make_turn(game_state):
    if game_state.get("on_resource"):
        return "GATHER"

    px, py = game_state["position"]
    best_action = "WAIT"
    best_dist = 10_000

    for action, dx, dy in (
        ("MOVE_UP", 0, -1),
        ("MOVE_DOWN", 0, 1),
        ("MOVE_LEFT", -1, 0),
        ("MOVE_RIGHT", 1, 0),
    ):
        nx, ny = px + dx, py + dy
        if not _walkable(game_state, nx, ny):
            continue
        dist = _manhattan_to_resource(game_state, nx, ny)
        if dist < best_dist:
            best_dist = dist
            best_action = action

    return best_action


def _walkable(game_state, x, y):
    if x < 0 or y < 0 or x >= game_state["map_width"] or y >= game_state["map_height"]:
        return False
    for tile in game_state["visible_tiles"]:
        if tile["x"] == x and tile["y"] == y:
            return tile["type"] != "obstacle"
    return False


def _manhattan_to_resource(game_state, x, y):
    best = 10_000
    for tile in game_state["visible_tiles"]:
        if tile["type"] == "resource":
            best = min(best, abs(tile["x"] - x) + abs(tile["y"] - y))
    return best
