"""Phase 0 smoke tests."""

import engine
import engine.core


def test_import_engine() -> None:
    assert engine.__version__ == "0.1.0"


def test_import_engine_core() -> None:
    assert engine.core is not None
