"""

Example student bot for Resource Wars.
Optional presentation (sandbox-safe):
  BOT_DISPLAY_NAME = "Explorer"
  BOT_ICON_INDEX = 7          # portrait index 0-99 from the character sheet
  # or an explicit path:
  # BOT_ICON = "ui/assets/icons/char_007.png"
  # If neither is set, a random portrait is assigned from the character sheet.


Turn function receives a readonly GameView (state). Common calls:
  state.on_resource()          -> bool
  state.my_x(), state.my_y()   -> int
  state.score()                -> int (resources collected)
  state.is_walkable(x, y)      -> bool
  state.resource_tiles()       -> list of (x, y) for all visible resource tiles
  state.others_positions()     -> list of (player_id, x, y) on classroom maps

Legacy two-player helpers still work; with several rivals, opponent_x/y reflect the first other id.

Optional: from engine.student_api import GameView, TileKind

Return one of: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, GATHER, WAIT
"""

BOT_DISPLAY_NAME = "Explorer"


def make_turn(state):

    if state.on_resource():
        return "GATHER"

    px, py = state.position()
    resources = state.resource_tiles()
    best_action = "WAIT"
    best_dist = 10_000

    for action, dx, dy in (
        ("MOVE_UP", 0, -1),
        ("MOVE_DOWN", 0, 1),
        ("MOVE_LEFT", -1, 0),
        ("MOVE_RIGHT", 1, 0),
    ):
        nx, ny = px + dx, py + dy

        if not state.is_walkable(nx, ny):
            continue

        dist = min((abs(rx - nx) + abs(ry - ny) for rx, ry in resources), default=10_000)

        if dist < best_dist:
            best_dist = dist
            best_action = action

    return best_action
