# Gemini — интерпретатор и C-транспилятор языка .alg

![coverage](https://img.shields.io/badge/coverage-86%25-brightgreen)

**Версия: 1.1.0** · [История изменений](CHANGELOG.md) · [Релизы](RELEASE.md)

С **v1.1.0** поддерживается **двуязычный синтаксис**: русские и английские ключевые слова — синонимы (`алг`/`proc`, `нач`/`begin`, `вывод`/`output`, …). См. [GRAMMAR.md](GRAMMAR.md) и [examples/en/](examples/en/).

**Язык .alg** — самостоятельный учебный алгоритмический язык с русскими ключевыми словами.  
**Gemini** — среда выполнения: интерпретатор на Python, статический анализ, транспиляция в C и сборка через GCC.

---

## С чего начать

| Документ | Описание |
|----------|----------|
| **[QUICKSTART.md](QUICKSTART.md)** | Первая программа за 5 минут |
| **[PROGRAMMER.md](PROGRAMMER.md)** | **Руководство программиста** (полный учебник) |
| **[TUTORIAL.md](TUTORIAL.md)** | Краткий курс из 7 уроков (школа) |
| **[GRAMMAR.md](GRAMMAR.md)** | Грамматика, EBNF, семантика |
| **[EXERCISES.md](EXERCISES.md)** | Задачи для самостоятельной работы |

```bash
python main.py examples/01_hello.alg
```

---

## Возможности

- Процедуры и функции, модули `использовать "файл.alg"`
- Типы: `цел`, `вещ`, `лит`, `лог`, `файл`, `словарь`, `таб`, `запись`, `переч`
- Файловый I/O без sandbox — любые пути ОС
- Подробные ошибки на русском, подсказки, `--verbose`, `--trace`
- Семантический анализ **до** выполнения
- Транспиляция в C с паритет-тестами (интерпретатор ↔ GCC)
- REPL, дамп AST, TextMate-грамматика (`editor/alg/`)

---

## Требования

| Компонент | Назначение |
|-----------|------------|
| **Python 3.7+** | интерпретация (только stdlib) |
| **GCC** (опционально) | компиляция сгенерированного `.c` |
| **pytest** (опционально) | тесты — `pip install -r requirements-dev.txt` |

---

## Запуск

### Интерпретация

```bash
python main.py program.alg
python -m gemini program.alg
```

### Транспиляция в C

```bash
python main.py program.alg --transpile
gcc program.c -o program -lm
```

### Полный цикл

```bash
python launcher.py examples/01_hello.alg --verbose
```

### Флаги CLI

| Флаг | Описание |
|------|----------|
| `--verbose` | Этапы: лексер → парсер → семантика → выполнение (stderr) |
| `--trace` | Пошаговая трассировка операторов |
| `--transpile` | Генерация C вместо выполнения |
| `--dump-ast` | Вывод дерева разбора |
| `--repl` | Интерактивный режим |
| `--warnings-as-errors` | Предупреждения → код выхода 3 |
| `--keep-cyrillic` | Кириллица в идентификаторах C (UTF-8) |
| `--permissive` | Транспиляция: заглушка вместо ошибки на экзотике |

```bash
python main.py --help
```

---

## Принципы языка .alg

1. **Самобытность** — не классический ШАЯ; синтаксис `.alg` развивается отдельно (`таб`, `использовать`, `<>`, `нц для` …).
2. **Информативность** — подробные ошибки, verbose, предупреждения (`AssignTypeWarning`, `MemoryLeakWarning` …).
3. **Полный доступ к ОС** — без sandbox; пути в `открыть` не фильтруются. Ответственность — на авторе и преподавателе.

Подробнее: раздел 16 в [PROGRAMMER.md](PROGRAMMER.md), [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Примеры

Каталог **`examples/`** — 10 учебных программ:

| Файл | Тема |
|------|------|
| `01_hello.alg` | первая программа |
| `02_variables.alg` | типы и `:=` |
| `03_conditions.alg` | `если` / `иначе` |
| `04_loops.alg` | `нц для`, `нц пока` |
| `05_arrays.alg` | `таб` |
| `06_files.alg` | файловый I/O |
| `07_strings.alg` | строки и escape |
| `08_hosts.alg` | чтение системного файла |
| `09_records.alg` | `запись` |
| `10_module.alg` | `использовать` |

Демонстрация всех возможностей: **`program.alg`** + модуль **`utils.alg`**.

---

## Структура проекта

| Каталог / файл | Назначение |
|----------------|------------|
| `main.py`, `gemini/` | точки входа CLI |
| `lexer.py`, `parser.py`, `ast_nodes.py` | разбор исходников |
| `semantic_analyzer.py`, `types_model.py` | статический анализ |
| `interpreter.py`, `alg_builtins.py` | выполнение |
| `c_transpiler.py` | генерация C |
| `visitors.py` | базовый `NodeVisitor` |
| `errors.py`, `alg_warnings.py` | ошибки и предупреждения |
| `launcher.py` | интерпретация → C → GCC → exe |
| `examples/` | учебные примеры |
| `tests/` | 116+ тестов, паритет с GCC |
| `editor/alg/` | подсветка синтаксиса (VS Code / Cursor) |

### Документация

| Файл | Назначение |
|------|------------|
| [QUICKSTART.md](QUICKSTART.md) | быстрый старт |
| [PROGRAMMER.md](PROGRAMMER.md) | руководство программиста |
| [TUTORIAL.md](TUTORIAL.md) | курс из 7 уроков |
| [GRAMMAR.md](GRAMMAR.md) | грамматика |
| [EXERCISES.md](EXERCISES.md) | задачи |
| [TEACHER.md](TEACHER.md) | для преподавателя |
| [CONTRIBUTING.md](CONTRIBUTING.md) | для разработчиков |
| [BILINGUAL_TODO.md](BILINGUAL_TODO.md) | план двуязычного синтаксиса RU + EN (v1.1.0) |
| [TODO.md](TODO.md) | план v1.0.x (основной roadmap завершён) |
| [AUDIT.md](AUDIT.md) | технический аудит |

---

## Тесты

```bash
python -m pytest tests/ -q
python -m pytest tests/ -m "not slow" -q
python -m pytest tests/ --cov=. --cov-fail-under=80 -q
```

---

## C-транспилятор

Паритет с интерпретатором — для основных конструкций (`tests/programs/`).  
При вложенной строковой арифметике в одном выражении — `MemoryLeakWarning`; разбейте на присваивания в `лит`.

Тип `файл` → `FILE*`, режимы: «чтение» / «запись» / «дозапись». Пути не ограничиваются.

---

## Лицензия

[MIT](LICENSE)
