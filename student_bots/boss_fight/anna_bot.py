"""
Boss Fight bot — Anna.

Smart cooperative fighter: heals allies when they're in danger, attacks when
safe, and kites the boss when HP is critically low.

Available actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT,
                   ATTACK, HEAL_SELF, HEAL_ALLY, WAIT
"""

BOT_DISPLAY_NAME = "Anna"


def _step_toward(sx, sy, tx, ty, state):
    """Return the best orthogonal move toward (tx, ty), or WAIT if stuck."""
    options = []
    if tx > sx:
        options.append(("MOVE_RIGHT", sx + 1, sy))
    elif tx < sx:
        options.append(("MOVE_LEFT", sx - 1, sy))
    if ty > sy:
        options.append(("MOVE_DOWN", sx, sy + 1))
    elif ty < sy:
        options.append(("MOVE_UP", sx, sy - 1))

    for action, nx, ny in options:
        if state.is_walkable(nx, ny):
            return action

    # fallback: try the secondary axis
    for action, nx, ny in reversed(options):
        if state.is_walkable(nx, ny):
            return action

    return "WAIT"


def make_turn(state):
    hp = state.my_hp()
    max_hp = state.my_max_hp()

    # Heal a dying ally first (team support)
    weakest = state.weakest_ally_id()
    if weakest is not None:
        ally_hp = state.ally_hp(weakest)
        if ally_hp is not None and ally_hp == 1:
            return "HEAL_ALLY"

    # Heal self if critically low
    if hp <= 1:
        return "HEAL_SELF"

    # Attack the boss if adjacent and HP is safe
    if state.is_boss_adjacent():
        if hp >= 2:
            return "ATTACK"
        return "HEAL_SELF"

    # Heal self if below half HP before closing in
    if hp < max_hp // 2:
        return "HEAL_SELF"

    # Move toward the boss
    return _step_toward(
        state.my_x(), state.my_y(),
        state.boss_x(), state.boss_y(),
        state,
    )
