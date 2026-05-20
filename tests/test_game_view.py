"""GameView student API tests."""

from engine.student_api import GameView, TileKind


def _sample_state(**overrides):
    base = {
        "turn": 3,
        "player_id": "student",
        "position": [2, 4],
        "resources": 7,
        "on_resource": False,
        "map_width": 8,
        "map_height": 8,
        "opponent_position": [5, 1],
        "visible_tiles": [
            {"x": 2, "y": 4, "type": "empty"},
            {"x": 3, "y": 4, "type": "resource"},
            {"x": 2, "y": 5, "type": "obstacle"},
        ],
    }
    base.update(overrides)
    return base


def test_basic_getters() -> None:
    state = GameView.from_dict(_sample_state())
    assert state.turn() == 3
    assert state.player_id() == "student"
    assert state.my_x() == 2
    assert state.my_y() == 4
    assert state.position() == (2, 4)
    assert state.score() == 7
    assert state.on_resource() is False
    assert state.map_width() == 8
    assert state.map_height() == 8
    assert state.opponent_position() == (5, 1)


def test_tile_helpers() -> None:
    state = GameView.from_dict(_sample_state())
    assert state.tile_at(3, 4) == TileKind.RESOURCE
    assert state.has_resource_at(3, 4) is True
    assert state.is_obstacle(2, 5) is True
    assert state.is_walkable(2, 4) is True
    assert state.is_walkable(2, 5) is False
    assert state.tile_at(99, 99) is None
    assert state.is_inside(0, 0) is True
    assert state.is_inside(-1, 0) is False


def test_resource_tiles_and_distance() -> None:
    state = GameView.from_dict(_sample_state())
    assert state.resource_tiles() == [(3, 4)]
    assert state.manhattan_to_nearest_resource(2, 4) == 1
    assert state.manhattan_to_nearest_resource(0, 0) == 7


def test_on_resource_flag() -> None:
    state = GameView.from_dict(_sample_state(on_resource=True))
    assert state.on_resource() is True


def test_no_dict_access() -> None:
    state = GameView.from_dict(_sample_state())
    assert not hasattr(state, "__getitem__")
