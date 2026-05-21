"""Fixture bot with high cyclomatic complexity for feedback tests."""


def make_turn(game_state):
    px, py = game_state["position"]
    action = "WAIT"
    for tile in game_state["visible_tiles"]:
        if tile["type"] == "resource":
            if tile["x"] > px:
                if tile["y"] > py:
                    if tile["x"] - px > 2:
                        if tile["y"] - py > 2:
                            action = "MOVE_RIGHT"
                        else:
                            action = "MOVE_DOWN"
                    else:
                        action = "MOVE_RIGHT"
                elif tile["y"] < py:
                    action = "MOVE_UP"
                else:
                    action = "MOVE_RIGHT"
            elif tile["x"] < px:
                action = "MOVE_LEFT"
    return action
