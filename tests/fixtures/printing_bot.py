"""Test bot that prints while playing (typical student debugging)."""

print("loaded!")


def make_turn(state):
    print("debug: x =", state.my_x())
    return "WAIT"
