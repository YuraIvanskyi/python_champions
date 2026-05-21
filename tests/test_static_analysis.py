"""Static analysis detects Ruff issues on student bots."""

from pathlib import Path

from engine.analysis.static import analyze_static
from engine.core.config import load_config


def test_ruff_detects_unused_import() -> None:
    config = load_config()
    bot_path = Path("tests/fixtures/ruff_bad_bot.py")
    metrics = analyze_static(
        bot_path,
        ruff_select=config.analysis.ruff_select,
        forbidden_names=config.analysis.forbidden_imports,
        enabled=True,
    )
    assert len(metrics.ruff_violations) >= 1
    codes = {v.code for v in metrics.ruff_violations}
    assert any(c.startswith("F") for c in codes)
