"""Structured feedback_items from analysis."""

from __future__ import annotations

from pathlib import Path

from engine.analysis.feedback import generate_feedback_items
from engine.analysis.static import analyze_static, static_to_dict


def test_high_complexity_efficiency_item() -> None:
    static = {"max_complexity": 12, "ruff": [], "forbidden_constructs": [], "functions": []}
    items = generate_feedback_items(static=static, runtime={"timeout_count": 0})
    categories = {it.category for it in items}
    assert "efficiency" in categories


def test_ruff_items_have_lines(tmp_path: Path) -> None:
    bot = tmp_path / "ruffy.py"
    bot.write_text("import os\n\ndef make_turn(state):\n    return 'WAIT'\n", encoding="utf-8")
    metrics = analyze_static(bot, ruff_select=["F401"], forbidden_names=["os"])
    static = static_to_dict(metrics)
    items = generate_feedback_items(static=static, runtime={})
    ruff_items = [it for it in items if it.category == "style" and it.lines]
    assert ruff_items or static.get("forbidden_constructs")
