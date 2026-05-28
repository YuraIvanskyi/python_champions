"""AI prompt strings (en / uk)."""

from __future__ import annotations


def _ai_en() -> dict[str, str]:
    return {
        "ai.system": """\
You are an educational code analysis assistant for a student programming game.

Rules you must follow:
1. Do NOT generate full solutions or rewrite the student's code.
2. You MAY include a tiny code example (1–2 lines maximum) inside a fenced code block \
(``` … ```) when it concretely illustrates a specific improvement — for example showing \
the corrected form of a single bad expression. Keep the block self-contained.
3. Keep your student summary to at most 5 sentences.
4. Keep your teacher notes to at most 3 bullet points.
5. Be encouraging and constructive; avoid harsh language.
6. Base your analysis only on the metrics and feedback provided — including movement \
patterns — do not invent issues.
7. When describing the bot's strategy, refer to the action distribution and movement data provided.
""",
        "ai.system.uk_rule": "",
        "ai.prompt.scenario": "Scenario: {name}",
        "ai.prompt.turns": (
            "Turns played: {turns}  |  Resources gathered: {resources}"
            "  |  Score threshold (win): {threshold}"
        ),
        "ai.prompt.scores": (
            "Scores — gameplay: {gameplay}/100, code quality: {quality}/100,"
            " final (weighted 70/30): {final}"
        ),
        "ai.prompt.action_breakdown": "Bot action breakdown (what it did each turn):",
        "ai.prompt.action_line": "  - {action}: {count} turns ({pct}%)",
        "ai.prompt.score_progress": (
            "Score progression: first resource gathered on turn {first}; "
            "score at mid-game (turn {mid}): {mid_score}; "
            "final game score: {final_score}"
        ),
        "ai.prompt.runtime": (
            "Runtime: avg turn {avg:.1f} ms  |  timeouts: {timeouts}"
            "  |  crashes: {crashes}  |  invalid actions: {invalid}"
        ),
        "ai.prompt.movement_header": "Movement / pathfinding analysis:",
        "ai.prompt.movement_blocked": "  - Blocked move ratio: {blocked}%  |  Wait ratio: {wait}%",
        "ai.prompt.movement_stuck": "  - Stuck episodes: {stuck}{range}",
        "ai.prompt.movement_stuck_range": " (worst: turns {start}–{end})",
        "ai.prompt.movement_osc": "  - Oscillation (ping-pong) episodes: {osc}",
        "ai.prompt.movement_repeat": "  - Max consecutive same action: {repeat} turns",
        "ai.prompt.movement_stall": "  - Score stall while moving: {stall} turns",
        "ai.prompt.movement_unique": "  - Unique positions visited: {unique}% of turns",
        "ai.prompt.code_flags": "  - Code pattern flags: {flags}",
        "ai.flag.no_walkable": "no is_walkable() call",
        "ai.flag.constant_return": "constant return (no branching)",
        "ai.flag.no_target": "no goal-seeking helpers used",
        "ai.flag.no_fallback": "no WAIT/fallback in movement helper",
        "ai.prompt.code_structure": (
            "Code structure: make_turn complexity rank {rank}"
            "  |  max nesting depth: {depth}"
            "  |  function length: {lines} lines"
        ),
        "ai.prompt.feedback_header": "Feedback from static / runtime analysis:",
        "ai.prompt.feedback_item": "  - {item}",
        "ai.prompt.no_issues": "  (no issues detected)",
        "ai.prompt.ruff_header": "Top style / lint issues (Ruff rule ID → occurrences):",
        "ai.prompt.ruff_line": "  - {rule}: {count}",
        "ai.prompt.write_instruction": (
            "Please write:\n"
            "### Student Summary\n"
            "A short, friendly explanation referencing what actions the bot took most often "
            "and how that affected its score. Mention one concrete thing to improve.\n\n"
            "### Teacher Notes\n"
            "3 bullet points for the teacher covering: algorithm strategy, code quality "
            "observations, and one actionable next challenge for the student."
        ),
    }


def _ai_uk() -> dict[str, str]:
    return {
        "ai.system": """\
Ти освітній помічник з аналізу коду для студентської програмувальної гри.

Правила:
1. НЕ надавай повних рішень і НЕ переписуй код студента.
2. МОЖНА додати крихітний приклад (1–2 рядки) у блоці ``` … ```, якщо він ілюструє конкретне покращення.
3. Підсумок для студента — щонайбільше 5 речень.
4. Нотатки для вчителя — щонайбільше 3 пункти списком.
5. Будь підтримуючим і конструктивним.
6. Спирайся лише на надані метрики та відгук — не вигадуй проблем.
7. Описуючи стратегію бота, посилайся на розподіл дій і дані руху.

ВАЖЛИВО: Усю відповідь пиши українською мовою.
""",
        "ai.system.uk_rule": "",
        "ai.prompt.scenario": "Сценарій: {name}",
        "ai.prompt.turns": (
            "Зіграно ходів: {turns}  |  Зібрано ресурсів: {resources}"
            "  |  Поріг перемоги: {threshold}"
        ),
        "ai.prompt.scores": (
            "Бали — геймплей: {gameplay}/100, якість коду: {quality}/100,"
            " підсумок (70/30): {final}"
        ),
        "ai.prompt.action_breakdown": "Розподіл дій бота (що робив кожен хід):",
        "ai.prompt.action_line": "  - {action}: {count} ходів ({pct}%)",
        "ai.prompt.score_progress": (
            "Прогрес рахунку: перший ресурс на ході {first}; "
            "рахунок на середині (хід {mid}): {mid_score}; "
            "фінальний рахунок: {final_score}"
        ),
        "ai.prompt.runtime": (
            "Виконання: сер. хід {avg:.1f} мс  |  таймаути: {timeouts}"
            "  |  падіння: {crashes}  |  недопустимі дії: {invalid}"
        ),
        "ai.prompt.movement_header": "Аналіз руху / пошуку шляху:",
        "ai.prompt.movement_blocked": "  - Заблоковані ходи: {blocked}%  |  WAIT: {wait}%",
        "ai.prompt.movement_stuck": "  - Епізоди застрягання: {stuck}{range}",
        "ai.prompt.movement_stuck_range": " (найгірше: ходи {start}–{end})",
        "ai.prompt.movement_osc": "  - Осциляції (туда-сюди): {osc}",
        "ai.prompt.movement_repeat": "  - Макс. однакових дій поспіль: {repeat} ходів",
        "ai.prompt.movement_stall": "  - Рух без набору очок: {stall} ходів",
        "ai.prompt.movement_unique": "  - Унікальних позицій: {unique}% ходів",
        "ai.prompt.code_flags": "  - Прапорці в коді: {flags}",
        "ai.flag.no_walkable": "немає виклику is_walkable()",
        "ai.flag.constant_return": "постійний return (без розгалужень)",
        "ai.flag.no_target": "немає пошуку цілі",
        "ai.flag.no_fallback": "немає WAIT/запасного варіанту",
        "ai.prompt.code_structure": (
            "Структура коду: складність make_turn {rank}"
            "  |  макс. вкладеність: {depth}"
            "  |  довжина функції: {lines} рядків"
        ),
        "ai.prompt.feedback_header": "Відгук зі статичного / runtime аналізу:",
        "ai.prompt.feedback_item": "  - {item}",
        "ai.prompt.no_issues": "  (серйозних зауважень не виявлено)",
        "ai.prompt.ruff_header": "Топ стильових зауважень (Ruff ID → кількість):",
        "ai.prompt.ruff_line": "  - {rule}: {count}",
        "ai.prompt.write_instruction": (
            "Напиши:\n"
            "### Підсумок для студента\n"
            "Коротке дружнє пояснення: які дії бот робив найчастіше і як це вплинуло на рахунок. "
            "Згадай одну конкретну річ для покращення.\n\n"
            "### Нотатки для вчителя\n"
            "3 пункти: стратегія алгоритму, якість коду, одне наступне завдання для студента."
        ),
    }
