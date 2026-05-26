"""AI report sticky mentor header layout."""

from __future__ import annotations

import os


def test_extract_advisory_note() -> None:
    from ui.screens.vllm_setup import _AI_ADVISORY_DEFAULT, _extract_advisory_note

    report = (
        "> ⚠️ AI-generated summary — advisory only. "
        "Numeric scores come from static analysis.\n\n"
        "## Player: bot_a\n\n"
        "### Student Summary\n"
        "Hello.\n"
    )
    advisory, body = _extract_advisory_note(report)
    assert "advisory only" in advisory.lower()
    assert "Player: bot_a" in body
    assert not body.lstrip().startswith(">")

    fallback, body2 = _extract_advisory_note("## Player: solo\n\nSummary text.")
    assert fallback == _AI_ADVISORY_DEFAULT
    assert "solo" in body2


def test_sticky_header_includes_teacher_trust_note() -> None:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame

    from ui.screens.vllm_setup import _AI_TEACHER_TRUST_NOTE, _sticky_note_lines
    from ui.skin.typography import body_font

    pygame.font.init()
    font = body_font(13)
    lines = _sticky_note_lines("AI-generated summary — advisory only.", font, 400)
    joined = " ".join(lines)
    assert "teacher" in joined.lower()
    assert _AI_TEACHER_TRUST_NOTE.split()[0] in joined


def test_parse_player_id() -> None:
    from ui.screens.vllm_setup import _parse_player_id

    assert _parse_player_id("Player: p0_daryna_bot") == "p0_daryna_bot"
    assert _parse_player_id("player: student") == "student"


def test_report_rows_skip_advisory_and_teacher_notes_mentor() -> None:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame

    from ui.screens.vllm_setup import (
        _STYLE_ADVISORY,
        _STYLE_BODY,
        _STYLE_HEADING,
        _STYLE_NUMBERED,
        _STYLE_PLAYER,
        _STYLE_SPACER,
        _build_report_rows,
        _measure_sticky_header,
    )
    from ui.skin import colors
    from ui.skin.typography import body_font, code_font

    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1), flags=pygame.NOFRAME)

    report = (
        "> ⚠️ AI-generated summary — advisory only. "
        "Numeric scores come from static analysis.\n\n"
        "## Player: p0__anna__bot\n\n"
        "### Student Summary\n"
        "Short summary here.\n\n"
        "### Teacher Notes\n"
        "1. Algorithm Strategy Analysis.\n"
    )

    f_head = body_font(16)
    f_player = body_font(15)
    f_body = body_font(14)
    f_small = body_font(13)
    f_code = code_font(13)
    style_cfg = {
        _STYLE_ADVISORY: (f_small, colors.TEXT_MUTED, 0, 6),
        _STYLE_PLAYER: (f_player, colors.WOOD_BORDER, 0, 10),
        _STYLE_HEADING: (f_head, colors.WOOD_FILL, 0, 8),
        _STYLE_NUMBERED: (f_body, colors.PARCHMENT_TEXT, 18, 5),
        _STYLE_BODY: (f_body, colors.PARCHMENT_TEXT, 0, 4),
        _STYLE_SPACER: (f_small, colors.PARCHMENT_TEXT, 0, 8),
    }

    rows = _build_report_rows(
        report,
        max_w=520,
        style_cfg=style_cfg,
        f_small=f_small,
        f_code=f_code,
    )

    assert not any(row[0] == _STYLE_ADVISORY for row in rows)
    assert not any("advisory only" in row[1].lower() for row in rows)
    assert any("Teacher Notes" in row[1] for row in rows)

    sticky_h, _ = _measure_sticky_header(
        max_w=520,
        advisory="AI-generated summary — advisory only. Numeric scores come from static analysis.",
        heading_font=body_font(15),
        body_font_obj=f_small,
    )
    assert sticky_h >= 88
