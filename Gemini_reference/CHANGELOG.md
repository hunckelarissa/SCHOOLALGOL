# История изменений

Формат основан на [Keep a Changelog](https://keepachangelog.com/). Версия синхронизирована с `version.py`.

## [1.1.0] — 2026-06-15

### Добавлено
- **Двуязычный синтаксис RU + EN** — английские ключевые слова как синонимы русских (`proc`, `begin`/`end`, `if`/`then`/`endif`, `loop`/`eloop`, `int`/`real`/`str`, …).
- Точка входа: `mainprogram` (синоним `основнаяпрограмма`).
- Модуль `builtin_names.py` — алиасы встроенных (`open`, `len`, `sqrt`, …) и режимов файла (`read`/`write`/`append`).
- `examples/en/` — примеры на английском синтаксисе.
- `tests/test_bilingual.py` — лексер, парсер, выполнение, builtins, циклы.
- `ast_compare.py`, `tests/test_bilingual_ast.py` — изоморфизм AST RU ↔ EN.
- CLI `--lang en` для REPL.
- `type_bilingual_label()`, `builtin_bilingual_label()` — подписи в предупреждениях и ошибках.
- `--verbose` — лог каждого токена с RU/EN-подписью.
- `suggestions.expand_bilingual_candidates()` — подсказки с учётом EN/RU алиасов builtins.
- `c_transpiler.py` — `// alg: mainprogram (основнаяпрограмма)` и наоборот для точки входа.

### Изменено
- `lang_tokens.py` — `_RU_KEYWORDS` + `_EN_KEYWORDS` → общий `KEYWORDS`.
- `constants.py`, `types_model.py` — `MAIN_PROGRAM_NAMES`, `TYPE_ALIASES`, `canonical_type()`.
- `interpreter.py`, `semantic_analyzer.py`, `c_transpiler.py`, `alg_builtins.py` — разрешение EN-имён.

### Документация
- `GRAMMAR.md` — раздел «Двуязычные ключевые слова».
- `QUICKSTART.md`, `PROGRAMMER.md`, `CONTRIBUTING.md`, `TUTORIAL.md` — EN-синтаксис.
- `BILINGUAL_TODO.md` — план реализации v1.1.0.

### Исправлено
- `examples/10_module.alg` — путь к модулю `../utils.alg` (раньше не находился `utils.alg`).
- `tests/helpers.gcc_compile_and_run` — явное удаление exe на Windows (WinError 5 в parity-тестах).

## [1.0.13] — 2025-06-15

### Добавлено
- `MemoryLeakWarning` — предупреждение о возможной утечке malloc в сгенерированном C.
- Тесты `TestTranspilerMemoryWarnings`.

### Завершено
- **P1-07** — verbose/предупреждения при вложенной `str_concat` и др.
- План TODO: основной roadmap закрыт; P5-08 и P6-06 отложены.

### Документация
- Обновлены **README.md**, **QUICKSTART.md**, **PROGRAMMER.md** (руководство программиста).
- **TUTORIAL.md** — ссылки на новые материалы.

## [1.0.12] — 2025-06-15

### Добавлено
- `visitors.py` — общий `NodeVisitor`, `AST_NODE_TYPES`, `iter_child_nodes`.
- `tests/test_visitors.py`.
- Чеклист узла AST в `CONTRIBUTING.md`.

### Улучшено
- `Interpreter`, `CTranspiler`, `SemanticAnalyzer` наследуют `visitors.NodeVisitor` (без дублирования dispatch).

## [1.0.11] — 2025-06-15

### Улучшено
- `parser.block()`: единый цикл `decl | statement` вместо двухфазной эвристики; явные правила для `ID ID` vs `ID :=`.
- Объявления и операторы могут чередоваться в теле блока (C-style).
- `GRAMMAR.md`: EBNF `body`, таблица различения decl/statement.
- `tests/test_parser.py`: 5 регрессионных тестов блока.

## [1.0.10] — 2025-06-15

### Добавлено
- `semantic_analyzer.py` — статический проход до выполнения/транспиляции (символы, типы, arity).
- `types_model.py` — общая модель типов и arity встроенных функций.
- `tests/test_semantic_analyzer.py` — 9 тестов анализатора.
- Пайплайн `main.py`: этап «Семантический анализ» (`--verbose` → таблица символов в stderr).

### Улучшено
- Ошибки (необъявленные имена, неверная arity, неизвестные типы) ловятся до запуска программы.

## [1.0.9] — 2025-06-15

### Добавлено
- `tests/test_file_io.py` — запись/чтение, `конецфайла`, EOF+verbose.
- `tests/test_stress.py` — маркер `@pytest.mark.slow` (цикл 10⁵, рекурсия 200).
- `RELEASE.md` — чеклист версионирования.

### Примечание
- P6-06 (Marketplace) отложен; грамматика в `editor/alg/`.
- Явные импорты AST (`P5-07`), бейдж покрытия, политика anti-sandbox в `CONTRIBUTING.md`.

## [1.0.8] — 2025-06-15

### Добавлено
- Обнаружение **циклического импорта** `использовать` (цепочка в сообщении).
- Пакет `gemini/` — `python -m gemini`.
- Расширенные тесты лексера (все ключевые слова, Unicode, комментарии).
- `examples/10_module.alg`, `tests/fixtures/` для модулей.

### Улучшено
- `GRAMMAR.md`: раздел «Числовая модель».
- Транспилятор: циклический импорт → `TranspilerError`.

## [1.0.7] — 2025-06-15

### Добавлено
- Подсказки «возможно, имелось в виду …» для неизвестных идентификаторов (Levenshtein).
- Мягкая проверка типов при `:=` (`AssignTypeWarning` для вещ → цел).
- TextMate-грамматика: `editor/alg/` (VS Code / Cursor).
- `tests/test_semantic.py`.

### Улучшено
- Ошибка `открыть`: путь, режим, errno.
- Сообщение при `RecursionError` с именем процедуры.
- `TUTORIAL.md`: сопоставление `.alg` и `.c`.

## [1.0.6] — 2025-06-15

### Добавлено
- `LICENSE` (MIT), `EXERCISES.md`, `TEACHER.md`.
- `examples/09_records.alg`.
- EBNF и таблица приоритетов операторов в `GRAMMAR.md`.
- `--trace`: значения переменных после `:=`.

### Улучшено
- Сообщение о выходе за границы массива включает имя массива.
- Документация EOF при `ввод` из файла.

## [1.0.5] — 2025-06-15

### Добавлено
- **REPL**: `python main.py --repl` — интерактивный ввод фрагментов `.alg`.
- **`--dump-ast`** — вывод AST (text/json) для разбора на уроке.
- **`--keep-cyrillic`** — кириллические идентификаторы в сгенерированном C.
- `examples/08_hosts.alg` — чтение системного файла hosts.
- Тесты встроенных функций (`tests/test_builtins.py`).
- `format_error` перенесён в `errors.py` (устранён циклический импорт).

## [1.0.4] — 2025-06-15

### Добавлено
- Операторы сравнения `>=`, `<=`, `<>` (расширение языка `.alg`).
- Escape-последовательности в строках: `\n`, `\t`, `\"`, `\\`.
- Режим `--trace` — пошаговая трассировка операторов в stderr.
- `launcher.py`: `--verbose`, замеры времени этапов.
- Паритет-тест `files.alg`, паритет `test_concat.alg`.
- `pyproject.toml` (pytest, coverage).

### Исправлено
- C-транспилятор: `лит` как `char*`, `strdup`/`free` при присваивании (краш при `ввод` из файла).
- Трассировка в теле процедур (не только в `visit_Block`).

## [1.0.3] — 2025-06

### Добавлено
- Полный паритет транспилятора: записи, enum, словари, массивы с offset, формат вывода, 14 встроенных функций.
- `--permissive` для транспиляции.
- Набор `tests/programs/*.alg` и раннер паритета Python vs GCC.
- Неявное объявление переменной в `нц для` с предупреждением.

### Исправлено
- Артефакты C (`if {;`), лишние пробелы в выводе.
- `alg_warnings.py` вместо `warnings.py` (конфликт со stdlib).

## [1.0.2] — 2025

### Добавлено
- Система предупреждений (`alg_warnings.py`), `--verbose`, `--warnings-as-errors`.
- Подробные ошибки с подсказками и контекстом.
- Тесты CLI, filesystem, verbose.

## [1.0.1] — ранее

- Базовый интерпретатор и транспилятор, `AUDIT.md`.
