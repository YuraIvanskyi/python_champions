"""Feedback template strings (en / uk) — merged into message catalogs."""

from __future__ import annotations

# Ruff prefix → (title_key_suffix uses same prefix)
RUFF_PREFIXES = (
    "E1", "E2", "E3", "E4", "E5", "E7", "E9", "W2", "W3", "W5", "W6",
    "F4", "F8", "F9", "N", "B", "C9", "E", "W", "F",
)


def _feedback_en() -> dict[str, str]:
    ruff_titles = {
        "E1": "Indentation issue",
        "E2": "Whitespace issue",
        "E3": "Blank line issue",
        "E4": "Import order",
        "E5": "Line too long",
        "E7": "Statement issue",
        "E9": "Runtime error",
        "W2": "Trailing whitespace",
        "W3": "Blank line warning",
        "W5": "Line-break warning",
        "W6": "Deprecated syntax",
        "F4": "Unused import",
        "F8": "Unused name",
        "F9": "Undefined name",
        "N": "Naming convention",
        "B": "Possible bug",
        "C9": "High complexity",
        "E": "Style issue",
        "W": "Style warning",
        "F": "Code problem",
    }
    ruff_hints = {
        "F4": "Remove or sort the import at the top of the file.",
        "E4": "Remove or sort the import at the top of the file.",
        "F8": "Delete the name if you don't use it, or use it in your logic.",
        "F9": "Check the spelling — the name must be defined before you use it.",
        "E1": "Fix the indentation — use 4 spaces per level.",
        "E2": "Remove extra spaces or add a missing one around the operator.",
        "W2": "Remove extra spaces or add a missing one around the operator.",
        "E3": "Add or remove the blank line as the message describes.",
        "W3": "Add or remove the blank line as the message describes.",
        "E5": "Break the long line into two shorter ones.",
        "E7": "Rewrite the statement as shown in the message.",
        "B": "Read the message carefully — this pattern can hide a bug.",
        "N": "Rename the variable/function to follow the naming rule shown.",
    }
    d: dict[str, str] = {
        "feedback.ruff.default_title": "Style check",
        "feedback.ruff.default_hint": "Read the message and fix the highlighted line.",
        "feedback.turn_timeout.title": "Turn timeout",
        "feedback.turn_timeout.message": (
            "Your bot timed out on one or more turns. "
            "Try simpler logic or fewer loops so each turn finishes faster."
        ),
        "feedback.turn_timeout.fix_hint": "Shorten loops and avoid heavy work inside make_turn.",
        "feedback.crash.title": "Bot crashed",
        "feedback.crash.message": (
            "Your bot crashed during the game. "
            "Check for typos, missing keys in game_state, or bad return values."
        ),
        "feedback.crash.fix_hint": "Run the bot locally and fix the first error Python reports.",
        "feedback.crash_cap.title": "Code quality capped at 50",
        "feedback.crash_cap.message": (
            "Because your bot crashed, the maximum code quality score is capped at 50/100. "
            "A bot that crashes cannot earn full quality points even with clean style."
        ),
        "feedback.crash_cap.fix_hint": "Fix the crash first — once the bot runs without errors, the cap is lifted.",
        "feedback.invalid_actions.title": "Invalid actions",
        "feedback.invalid_actions.message": (
            "Some turns used invalid actions (for example GATHER when not on a resource). "
            "Read the allowed actions in the bot template comments."
        ),
        "feedback.invalid_actions.fix_hint": "Use GameView helpers (on_resource, is_walkable) before returning an action.",
        "feedback.high_complexity.title": "High complexity",
        "feedback.high_complexity.message": (
            "Your code has high cyclomatic complexity. "
            "Try splitting logic into smaller functions with clear names."
        ),
        "feedback.high_complexity.fix_hint": "Extract one helper per decision (movement, gathering, targeting).",
        "feedback.growing_complexity.title": "Growing complexity",
        "feedback.growing_complexity.message": (
            "Some functions are getting complex. "
            "Extract helper functions for repeated conditions."
        ),
        "feedback.growing_complexity.fix_hint": "Name helpers after what they check, e.g. should_gather(state).",
        "feedback.deep_nesting.title": "Deep nesting",
        "feedback.deep_nesting.message": (
            "Deeply nested if/for blocks make code hard to follow. "
            "Use early returns or helper functions to flatten structure."
        ),
        "feedback.deep_nesting.fix_hint": "Return early when a condition fails instead of wrapping more code.",
        "feedback.long_function.title": "Long function",
        "feedback.long_function.message": (
            "One of your functions is very long. "
            "Break it into smaller steps — each function should do one clear job."
        ),
        "feedback.long_function.fix_hint": "Split make_turn into decide_action + small helpers.",
        "feedback.style_many.title": "Style check ({count} issues)",
        "feedback.style_many.message": (
            "Found {count} style issues in your code. "
            "Fix the highlighted lines — clean code is easier to read and debug."
        ),
        "feedback.style_many.fix_hint": "Work through the highlighted lines one by one.",
        "feedback.forbidden.title": "Forbidden imports",
        "feedback.forbidden.message": (
            "Your bot uses imports or calls that are not allowed in the sandbox "
            "(for example os or subprocess). Stick to the student API only."
        ),
        "feedback.forbidden.fix_hint": "Remove blocked imports; use only GameView and allowed actions.",
        "feedback.unused_vars.title": "Unused variables",
        "feedback.unused_vars.message": (
            "You have variables that are assigned but never used. "
            "Remove dead code or use those variables in your logic."
        ),
        "feedback.unused_vars.fix_hint": "Delete assignments you do not need, or wire them into decisions.",
        "feedback.low_maint.title": "Low maintainability: {name}",
        "feedback.low_maint.message": (
            "Function '{name}' has low maintainability. "
            "Simplify conditions and shorten the function."
        ),
        "feedback.low_maint.fix_hint": "Break this function into two smaller ones.",
        "feedback.slow_turns.title": "Slow turns",
        "feedback.slow_turns.message": (
            "Turns are taking a long time on average. "
            "Avoid scanning the whole map every turn if you can cache simpler rules."
        ),
        "feedback.slow_turns.fix_hint": "Cache last direction or nearest resource instead of full-map scans.",
        "feedback.syntax.title": "Syntax error",
        "feedback.syntax.message": (
            "Your bot file has a Python syntax error. "
            "The game cannot analyze code quality until the file parses correctly."
        ),
        "feedback.syntax.fix_hint": "Fix the syntax error shown when you run the file in Python.",
        "feedback.praise.title": "Looking good",
        "feedback.praise.message": (
            "Nice work — no major issues flagged. "
            "Keep refactoring as you add features."
        ),
        "feedback.praise.fix_hint": "Try a harder opponent or add smarter gathering logic.",
        "feedback.stuck.title": "Stuck between obstacles",
        "feedback.stuck.message": (
            "Your bot got stuck {count} time{plural}{range} — "
            "it kept revisiting the same cell without gaining any score."
        ),
        "feedback.stuck.fix_hint": "When a move is blocked, try a different direction or WAIT, then pick a new target.",
        "feedback.oscillation.title": "Bouncing between two tiles",
        "feedback.oscillation.message": (
            "Your bot ping-ponged between the same two tiles {count} time{plural}. "
            "This wastes turns and prevents progress."
        ),
        "feedback.oscillation.fix_hint": "Break the loop: pick a different target tile or wait one turn before re-trying.",
        "feedback.repeat_action.title": "Repeating the same move",
        "feedback.repeat_action.message": (
            "Your bot returned the same action {count} turns in a row. "
            "A stuck bot wastes turns that could be spent gathering resources."
        ),
        "feedback.repeat_action.fix_hint": "Track whether the last move succeeded; if blocked, choose a different direction.",
        "feedback.blocked_moves.title": "Many blocked moves",
        "feedback.blocked_moves.message": (
            "Your bot tried to move into obstacles {pct}% of the time.{extra} "
            "Checking for walls before moving will save turns."
        ),
        "feedback.blocked_moves.extra_no_walkable": " The code does not check is_walkable() before moving.",
        "feedback.blocked_moves.fix_hint": "Call is_walkable(x, y) before returning MOVE_* to avoid walking into walls.",
        "feedback.no_walkable.title": "No obstacle check in code",
        "feedback.no_walkable.message": (
            "Your bot never calls is_walkable() or is_obstacle(). "
            "Adding obstacle checks lets the bot pick safer paths."
        ),
        "feedback.no_walkable.message_static": (
            "Your bot never calls is_walkable() or is_obstacle(). "
            "Without obstacle checks the bot will walk into walls."
        ),
        "feedback.no_walkable.fix_hint": "Add: if state.is_walkable(nx, ny): before each MOVE_ return.",
        "feedback.score_stall.title": "Moving without scoring",
        "feedback.score_stall.message": (
            "Your bot moved for {stall} turns in a row without increasing its score. "
            "It may be heading in the wrong direction or targeting empty tiles."
        ),
        "feedback.score_stall.fix_hint": (
            "Head toward resources/stations; use nearest_station() or resource_tiles() to find active targets."
        ),
        "feedback.no_branch.title": "No decision logic in make_turn",
        "feedback.no_branch.message": (
            "make_turn always returns the same fixed action with no branching. "
            "The bot cannot react to the map or game state."
        ),
        "feedback.no_branch.fix_hint": (
            "Add if/elif branches to choose different actions based on state.on_resource(), "
            "state.nearest_station(), etc."
        ),
        "feedback.no_branch.fix_hint_static": (
            "Add if/elif branches based on state.on_resource(), state.nearest_station(), etc."
        ),
        "feedback.no_target.title": "No goal-seeking in code",
        "feedback.no_target.message": (
            "Your bot never uses helpers like on_resource(), nearest_station(), or can_gather(). "
            "Without goal logic it moves randomly and misses easy score opportunities."
        ),
        "feedback.no_target.message_static": (
            "Your bot never uses helpers like on_resource() or nearest_station(). "
            "Goal-seeking logic turns random walking into effective play."
        ),
        "feedback.no_target.fix_hint": "Use state.nearest_station() or state.resource_tiles() to pick a target each turn.",
        "feedback.no_fallback.title": "No fallback when path is blocked",
        "feedback.no_fallback.message": (
            "Your movement helper has no WAIT or alternate direction when the direct path is blocked. "
            "Adding a fallback prevents the bot from freezing."
        ),
        "feedback.no_fallback.fix_hint": "Return 'WAIT' or a perpendicular direction when is_walkable() returns False.",
        "feedback.stuck.range": " (around turns {start}–{end})",
        "feedback.plural.s": "s",
        "feedback.plural.empty": "",
    }
    for prefix, title in ruff_titles.items():
        d[f"feedback.ruff.{prefix}.title"] = title
    for prefix, hint in ruff_hints.items():
        d[f"feedback.ruff.{prefix}.fix_hint"] = hint
    return d


def _feedback_uk() -> dict[str, str]:
    ruff_titles = {
        "E1": "Проблема з відступами",
        "E2": "Проблема з пробілами",
        "E3": "Проблема з порожніми рядками",
        "E4": "Порядок імпортів",
        "E5": "Занадто довгий рядок",
        "E7": "Проблема з оператором",
        "E9": "Помилка виконання",
        "W2": "Зайві пробіли в кінці",
        "W3": "Попередження про порожній рядок",
        "W5": "Попередження про перенос",
        "W6": "Застарілий синтаксис",
        "F4": "Невикористаний імпорт",
        "F8": "Невикористана назва",
        "F9": "Невизначена назва",
        "N": "Угода про імена",
        "B": "Можлива помилка",
        "C9": "Висока складність",
        "E": "Стильове зауваження",
        "W": "Стильове попередження",
        "F": "Проблема в коді",
    }
    ruff_hints = {
        "F4": "Прибери або впорядкуй імпорт на початку файлу.",
        "E4": "Прибери або впорядкуй імпорт на початку файлу.",
        "F8": "Видали назву, якщо не використовуєш, або застосуй її в логіці.",
        "F9": "Перевір написання — назва має бути визначена до використання.",
        "E1": "Виправ відступи — 4 пробіли на рівень.",
        "E2": "Прибери зайві пробіли або додай між оператором.",
        "W2": "Прибери зайві пробіли або додай між оператором.",
        "E3": "Додай або прибери порожній рядок, як у повідомленні.",
        "W3": "Додай або прибери порожній рядок, як у повідомленні.",
        "E5": "Розбий довгий рядок на два коротші.",
        "E7": "Перепиши оператор, як показано в повідомленні.",
        "B": "Уважно прочитай повідомлення — такий шаблон може ховати помилку.",
        "N": "Перейменуй змінну або функцію за правилом з повідомлення.",
    }
    d: dict[str, str] = {
        "feedback.ruff.default_title": "Перевірка стилю",
        "feedback.ruff.default_hint": "Прочитай повідомлення та виправ виділений рядок.",
        "feedback.turn_timeout.title": "Час ходу вичерпано",
        "feedback.turn_timeout.message": (
            "Твій бот не встигав на одному або кількох ходах. "
            "Спрости логіку або зменши кількість циклів, щоб кожен хід завершувався швидше."
        ),
        "feedback.turn_timeout.fix_hint": "Скороти цикли й не роби важкої роботи всередині make_turn.",
        "feedback.crash.title": "Бот аварійно завершився",
        "feedback.crash.message": (
            "Під час гри бот зіткнувся з помилкою. "
            "Перевір друкарські помилки, відсутні ключі в game_state або некоректні значення return."
        ),
        "feedback.crash.fix_hint": "Запусти бота локально й виправ першу помилку Python.",
        "feedback.crash_cap.title": "Якість коду обмежено до 50",
        "feedback.crash_cap.message": (
            "Через аварійне завершення максимальний бал якості коду — 50/100. "
            "Бот з падінням не отримає повний бал навіть за чистий стиль."
        ),
        "feedback.crash_cap.fix_hint": "Спочатку виправ падіння — після цього обмеження знімається.",
        "feedback.invalid_actions.title": "Недопустимі дії",
        "feedback.invalid_actions.message": (
            "Деякі ходи містили недопустимі дії (наприклад GATHER не на ресурсі). "
            "Переглянь дозволені дії в коментарях шаблону бота."
        ),
        "feedback.invalid_actions.fix_hint": "Використовуй GameView (on_resource, is_walkable) перед return дії.",
        "feedback.high_complexity.title": "Висока складність",
        "feedback.high_complexity.message": (
            "У коді висока цикломатична складність. "
            "Розбий логіку на менші функції з зрозумілими назвами."
        ),
        "feedback.high_complexity.fix_hint": "Винеси окрему допоміжну функцію на кожне рішення.",
        "feedback.growing_complexity.title": "Складність зростає",
        "feedback.growing_complexity.message": (
            "Деякі функції стають складними. "
            "Винеси повторювані умови в допоміжні функції."
        ),
        "feedback.growing_complexity.fix_hint": "Називай допоміжні функції за тим, що вони перевіряють.",
        "feedback.deep_nesting.title": "Глибока вкладеність",
        "feedback.deep_nesting.message": (
            "Глибоко вкладені if/for важко читати. "
            "Використовуй ранній return або допоміжні функції."
        ),
        "feedback.deep_nesting.fix_hint": "Повертайся раніше, коли умова не виконується.",
        "feedback.long_function.title": "Довга функція",
        "feedback.long_function.message": (
            "Одна з функцій дуже довга. "
            "Розбий на кроки — кожна функція має робити одну зрозумілу справу."
        ),
        "feedback.long_function.fix_hint": "Розділи make_turn на decide_action і дрібні допоміжні.",
        "feedback.style_many.title": "Перевірка стилю ({count} зауважень)",
        "feedback.style_many.message": (
            "Знайдено {count} стильових зауважень. "
            "Виправ виділені рядки — чистий код легше читати й налагоджувати."
        ),
        "feedback.style_many.fix_hint": "Проходь виділені рядки по одному.",
        "feedback.forbidden.title": "Заборонені імпорти",
        "feedback.forbidden.message": (
            "Бот використовує імпорти або виклики, заборонені в пісочниці "
            "(наприклад os або subprocess). Лишайся в межах студентського API."
        ),
        "feedback.forbidden.fix_hint": "Прибери заблоковані імпорти; лише GameView і дозволені дії.",
        "feedback.unused_vars.title": "Невикористані змінні",
        "feedback.unused_vars.message": (
            "Є змінні, яким присвоюють значення, але не використовують. "
            "Прибери зайвий код або застосуй їх у логіці."
        ),
        "feedback.unused_vars.fix_hint": "Видали зайві присвоєння або підключи їх до рішень.",
        "feedback.low_maint.title": "Низька підтримуваність: {name}",
        "feedback.low_maint.message": (
            "Функція «{name}» має низьку підтримуваність. "
            "Спрости умови й скороти функцію."
        ),
        "feedback.low_maint.fix_hint": "Розділи цю функцію на дві менші.",
        "feedback.slow_turns.title": "Повільні ходи",
        "feedback.slow_turns.message": (
            "Ходи в середньому тривають довго. "
            "Уникай повного сканування карти кожен хід — кешуй простіші правила."
        ),
        "feedback.slow_turns.fix_hint": "Запам’ятовуй останній напрямок або найближчий ресурс.",
        "feedback.syntax.title": "Синтаксична помилка",
        "feedback.syntax.message": (
            "У файлі бота синтаксична помилка Python. "
            "Гра не оцінить якість коду, доки файл не парситься."
        ),
        "feedback.syntax.fix_hint": "Виправ синтаксис, який показує Python при запуску файлу.",
        "feedback.praise.title": "Виглядає добре",
        "feedback.praise.message": (
            "Чудова робота — серйозних зауважень немає. "
            "Продовжуй покращувати код із новими можливостями."
        ),
        "feedback.praise.fix_hint": "Спробуй сильнішого суперника або розумніший збір ресурсів.",
        "feedback.stuck.title": "Застряг між перешкодами",
        "feedback.stuck.message": (
            "Бот застряг {count} раз{plural}{range} — "
            "повторював ту саму клітинку без набору очок."
        ),
        "feedback.stuck.fix_hint": "Якщо хід заблоковано — спробуй інший напрямок або WAIT.",
        "feedback.oscillation.title": "Стрибає між двома клітинками",
        "feedback.oscillation.message": (
            "Бот {count} раз{plural} ходив туди-сюди між двома клітинками. "
            "Це марнує ходи й гальмує прогрес."
        ),
        "feedback.oscillation.fix_hint": "Зміни ціль або зроби WAIT перед повторною спробою.",
        "feedback.repeat_action.title": "Повторює ту саму дію",
        "feedback.repeat_action.message": (
            "Бот {count} ходів поспіль повертав одну й ту саму дію. "
            "Застряглий бот марнує ходи, які можна витратити на ресурси."
        ),
        "feedback.repeat_action.fix_hint": "Відстежуй успіх останнього ходу; якщо блок — обери інший напрямок.",
        "feedback.blocked_moves.title": "Багато заблокованих ходів",
        "feedback.blocked_moves.message": (
            "Бот намагався йти в перешкоди {pct}% часу.{extra} "
            "Перевірка стін перед рухом економить ходи."
        ),
        "feedback.blocked_moves.extra_no_walkable": " Код не викликає is_walkable() перед рухом.",
        "feedback.blocked_moves.fix_hint": "Викликай is_walkable(x, y) перед MOVE_*.",
        "feedback.no_walkable.title": "Немає перевірки перешкод у коді",
        "feedback.no_walkable.message": (
            "Бот ніколи не викликає is_walkable() або is_obstacle(). "
            "Перевірки допомагають обирати безпечніші шляхи."
        ),
        "feedback.no_walkable.message_static": (
            "Бот ніколи не викликає is_walkable() або is_obstacle(). "
            "Без перевірок бот буде врізатися в стіни."
        ),
        "feedback.no_walkable.fix_hint": "Додай: if state.is_walkable(nx, ny): перед кожним MOVE_.",
        "feedback.score_stall.title": "Рух без набору очок",
        "feedback.score_stall.message": (
            "Бот {stall} ходів поспіль рухався без зростання рахунку. "
            "Можливо, йде не туди або цілиться в порожні клітинки."
        ),
        "feedback.score_stall.fix_hint": (
            "Йди до ресурсів/станцій; nearest_station() або resource_tiles() підкажуть ціль."
        ),
        "feedback.no_branch.title": "Немає логіки рішень у make_turn",
        "feedback.no_branch.message": (
            "make_turn завжди повертає одну й ту саму дію без розгалужень. "
            "Бот не реагує на карту чи стан гри."
        ),
        "feedback.no_branch.fix_hint": (
            "Додай if/elif за state.on_resource(), state.nearest_station() тощо."
        ),
        "feedback.no_branch.fix_hint_static": (
            "Додай if/elif за state.on_resource(), state.nearest_station() тощо."
        ),
        "feedback.no_target.title": "Немає пошуку цілі в коді",
        "feedback.no_target.message": (
            "Бот не використовує on_resource(), nearest_station() або can_gather(). "
            "Без цілей рух випадковий і легкі очки губляться."
        ),
        "feedback.no_target.message_static": (
            "Бот не використовує on_resource() або nearest_station(). "
            "Логіка цілей перетворює випадковий рух на ефективну гру."
        ),
        "feedback.no_target.fix_hint": "Використовуй nearest_station() або resource_tiles() для цілі кожен хід.",
        "feedback.no_fallback.title": "Немає запасного варіанту при блокуванні",
        "feedback.no_fallback.message": (
            "У допоміжній функції руху немає WAIT чи обходу, коли прямий шлях заблоковано. "
            "Запасний варіант не дає боту зависнути."
        ),
        "feedback.no_fallback.fix_hint": "Поверни 'WAIT' або перпендикулярний напрямок, якщо is_walkable() — False.",
        "feedback.stuck.range": " (близько ходів {start}–{end})",
        "feedback.plural.s": "и",
        "feedback.plural.empty": "",
    }
    for prefix, title in ruff_titles.items():
        d[f"feedback.ruff.{prefix}.title"] = title
    for prefix, hint in ruff_hints.items():
        d[f"feedback.ruff.{prefix}.fix_hint"] = hint
    return d
