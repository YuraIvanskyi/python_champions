"""High complexity triggers educational feedback."""

from pathlib import Path

from engine.analysis.feedback import generate_feedback
from engine.analysis.static import analyze_static, static_to_dict
from engine.core.config import load_config


def test_high_complexity_feedback_message() -> None:
    config = load_config()
    bot_path = Path("tests/fixtures/complex_bot.py")
    static = static_to_dict(
        analyze_static(
            bot_path,
            ruff_select=config.analysis.ruff_select,
            forbidden_names=config.analysis.forbidden_imports,
        )
    )
    assert static["max_complexity"] >= 7

    feedback = generate_feedback(static=static, runtime={"timeout_count": 0})
    joined = " ".join(feedback).lower()
    assert "complex" in joined or "splitting" in joined or "functions" in joined
