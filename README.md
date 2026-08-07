# SCHOOLALGOL — School Algol (.alg)

Учебный язык программирования **School Algol** (расширение `.alg`) и его среда выполнения: интерпретатор на Python, семантический анализ, транспиляция в C, отладка SHAYDBG и плагин Eclipse **ALG**.

| Компонент | Версия | Источник |
|-----------|--------|----------|
| Движок (интерпретатор / транспилятор) | **1.2.0** | `version.py` |
| Плагин Eclipse `org.myau.shaya.ide` | **0.6.4** | `META-INF/MANIFEST.MF` |

Документы:

| Файл | Содержание |
|------|------------|
| **[GRAMMAR.md](GRAMMAR.md)** | Грамматика, семантика, RU/EN, ограничения C |
| **[IDE_SETUP.md](IDE_SETUP.md)** | Установка и настройка плагина ALG в Eclipse |
| **[AUDIT.md](AUDIT.md)** | Исторический технический аудит (статус задач) |

Каталог `Gemini_reference/` — справочная копия родственного проекта (не путать с брендингом SCHOOLALGOL / ALG).

---

## Что это за проект

**SCHOOLALGOL** — пайплайн `Lexer → Parser → AST → SemanticAnalyzer → Interpreter | CTranspiler` для файлов `.alg`.

Язык — учебный алгоритмический диалект с русскими ключевыми словами (в духе школьного Алгола/ШАЯ, но **самостоятельный** синтаксис: `таб`, `использовать`, `словарь`, `<>`, `нц для` …). С **1.1.x** добавлены английские синонимы тех же токенов (`proc`/`begin`/`int`/`output` …); русские программы не ломаются. В одном файле допустимо смешение RU и EN.

**Плагин** `org.myau.shaya.ide` в UI называется **ALG**: редактор `.alg`, Run / Check / Step Debug, шаблоны, перспектива, настройки toolchain.

---

## Структура репозитория

| Путь | Назначение |
|------|------------|
| `main.py` | CLI: интерпретация, `--transpile`, `--check`, REPL, AST, SHAYDBG |
| `version.py` | Единая версия движка |
| `lexer.py`, `parser.py`, `ast_nodes.py` | Лексика, синтаксис, AST |
| `semantic_analyzer.py`, `types_model.py` | Статический анализ до выполнения |
| `interpreter.py`, `alg_builtins.py` | Интерпретатор и встроенные |
| `c_transpiler.py` | Генерация C |
| `builtin_names.py` | Алиасы встроенных RU ↔ EN |
| `module_loader.py` | Загрузка `использовать` / `import` |
| `repl.py`, `ast_dump.py` | REPL и `--dump-ast` |
| `shay_debug_protocol.py` | Протокол SHAYDBG (`--debug-protocol`) |
| `launcher.py` | Полный цикл: interpret → C → GCC → exe (для `program.alg`) |
| `test_basic.py`, `test_bilingual.py` | Тесты |
| `examples/`, `examples/en/` | Примеры (RU и EN) |
| `program.alg`, `utils.alg` | Демо-программа и модуль |
| `org.myau.shaya.ide/` | Исходники плагина Eclipse ALG |
| `install_dropins.ps1` | Синхронизация `*.py` (и опционально JAR) в Eclipse dropins |
| `Gemini_reference/` | Справочный снимок (документы/код другого бренда) |

---

## Язык School Algol (.alg)

Подробности — в **[GRAMMAR.md](GRAMMAR.md)**. Кратко по возможностям движка **1.2.0**.

### Обзор

- **Точка входа:** процедура без параметров `основнаяпрограмма` или `mainprogram` (имена регистронезависимы).
- **Комментарии:** строка начинается с `|`.
- **Двуязычность:** ключевые слова и встроенные — синонимы одного `TokenType` (модель «как в 1С»). См. таблицу в GRAMMAR.md.
- **Модули:** `использовать "файл.alg"` / `import "…"`. Путь относительно текущего файла, без sandbox; циклический импорт — ошибка с цепочкой.
- **Семантика:** перед выполнением и транспиляцией — `SemanticAnalyzer` (типы, объявления, вызовы). Предупреждения (`AssignTypeWarning`, `ImplicitDeclareWarning`, `MemoryLeakWarning` …); `--warnings-as-errors` → код выхода 3.

### Типы

| Тип | Смысл | Примечание |
|-----|--------|------------|
| `цел` / `int` | целое | в интерпретаторе арифметика через float; при дробном присваивании — предупреждение |
| `вещ` / `real` | вещественное | |
| `лит` / `str` | строка | escape: `\n` `\t` `\r` `\"` `\\` |
| `лог` / `bool` | логический | `да`/`нет`, `true`/`false` |
| `таб` / `tab` | массив `имя[нач:кон]` | произвольный начальный индекс; в C — offset |
| `файл` / `file` | файл | `открыть`/`закрыть`/`конецфайла` |
| `словарь` / `dict` | строковый ключ → число | в C — только `double` |
| `запись` / `rec` | структура | поля через `.` |
| `переч` / `enum` | перечисление | |

### Управление и процедуры

- Присваивание `:=`; `вывод` / `ввод` (в т.ч. в файл); формат `вывод x:ширина:точность`.
- `если … то … [иначе …] все` / `if … then … [else …] endif`.
- `нц пока … кц` / `loop while … eloop`; `нц для i от a до b … кц` / `loop for … from … to … eloop`.
- `алг` / `proc` с `арг`/`рез` (`arg`/`res`) — процедуры и функции; тело в `нач`…`кон` / `begin`…`end`.
- Операторы: `+ - * /`, сравнения `= <> > < >= <=`, логика `и`/`или`/`не` (`and`/`or`/`not`).

### Встроенные (RU / EN)

`открыть`/`open`, `закрыть`/`close`, `конецфайла`/`eof`, `корень`/`sqrt`, `модуль`/`abs`, `случ`/`rand`, `случцел`/`randint`, `длина`/`len`, `подстрока`/`substr`, `вверх`/`upper`, `вниз`/`lower`, `вцел`/`toint`, `ввещ`/`toreal`, `встроку`/`tostr`.

Режимы файла: `чтение`/`read`, `запись`/`write`, `дозапись`/`append`.

### Интерпретатор и C

| Режим | Команда | Результат |
|-------|---------|-----------|
| Интерпретация | `python main.py файл.alg` | выполнение в Python |
| Транспиляция | `python main.py файл.alg --transpile` | файл `файл.c` |
| Проверка | `python main.py файл.alg --check` | lex + parse + семантика, без выполнения |

В C: `файл` → `FILE*`; записи/перечисления; словари; `--keep-cyrillic`, `--permissive`.

**Ограничения паритета интерпретатор ↔ C:**

- `длина(число)` — в интерпретаторе длина `str(n)`; в C ожидается строка.
- `случ` / `случцел` — разные ГПСЧ (Python vs C), последовательности не совпадают.
- Словарь в C хранит только `double`.
- Сеть / host-API и упаковка VS Code из `Gemini_reference` в этот репозиторий не портированы.

### Отладка и диагностика CLI

| Флаг | Назначение |
|------|------------|
| `--verbose` | Этапы пайплайна и токены RU/EN в stderr |
| `--trace` | Пошаговая трассировка операторов |
| `--dump-ast` [`--dump-ast-format text\|json`] | Дерево разбора |
| `--repl` [`--lang ru\|en`] | Интерактивный режим |
| `--debug-protocol` | SHAYDBG JSONL (для Eclipse Step Debug) |
| `--break N` | Точка останова по номеру строки (можно повторять) |
| `--warnings-as-errors` | Предупреждения → exit 3 |
| `--keep-cyrillic` | С `--transpile`: кириллица в идентификаторах C |
| `--permissive` | С `--transpile`: неизвестные узлы → предупреждение |
| `--version` / `--help` | Версия / справка |

---

## Плагин ALG (Eclipse)

Плагин **`org.myau.shaya.ide` 0.6.4** — IDE для `.alg` поверх движка SCHOOLALGOL. В меню, перспективе и Preferences бренд **ALG** (Java-пакет `org.myau.shaya.ide` сохранён).

Полная установка — **[IDE_SETUP.md](IDE_SETUP.md)**.

### Возможности

- Редактор `.alg`: подсветка, автодополнение и шаблоны Ctrl+Space (RU и EN: `алг…` / `proc…`, `если…` / `if…` …).
- **ALG → Run** (Ctrl+Alt+R) — выполнить через `main.py`.
- **ALG → Check** (Ctrl+Alt+C) — `main.py --check` (lex + parse + семантика).
- **ALG → Step Debug** (Ctrl+Alt+Shift+D) — пошаговая отладка: breakpoints на линейке + `--debug-protocol` / SHAYDBG.
- **ALG → Run Last** (Ctrl+Alt+L).
- Мастер **ALG Project** / New Hello — образцы `Hello.alg` (RU) и `Hello_en.alg` (EN).
- Перспектива **ALG**, маркеры в Problems, консоль с гиперссылками на строки.
- Редактирование: Toggle Comment (`|`), Go to Matching Block, Quick Outline, Go to Declaration (F3), Find References, Rename, Reindent и др.
- **Preferences → ALG:** Toolchain home, Extra args, Python, отступ, Check on save, кнопка **Validate…**.

Один движок: расширение `.alg` → `schoolalgol-shaya/interpreters/SchoolAlgol/main.py`. Отдельный CLI Debug (`--debug`) для SCHOOLALGOL не используется — для выполнения Run, для шагов Step Debug.

### Установка (кратко)

1. В Eclipse `dropins` положить JAR: `org.myau.shaya.ide_0.6.4.jar`.
2. Рядом — toolchain `dropins/schoolalgol-shaya/` (`tools/shaya-run.bat`, `interpreters/SchoolAlgol/*.py`).
3. Синхронизация Python из корня репозитория:

```powershell
cd F:\proj\SCHOOLALGOL
.\install_dropins.ps1
# опционально JAR:
.\install_dropins.ps1 -PluginJar
```

4. Перезапустить Eclipse. При необходимости: **Preferences → ALG → Toolchain home** = путь к `schoolalgol-shaya`, **Validate…**.

Старые JAR `0.6.1`…`0.6.3` из dropins удалять. Разработка из исходников: PDE → Import `org.myau.shaya.ide` → Run As → Eclipse Application.

### Использование

1. **Window → Perspective → Open Perspective → ALG**.
2. **File → New → Project → ALG Project** или открыть свой `.alg`.
3. **ALG → Run** / **Check** / поставить breakpoint и **Step Debug**.
4. При необходимости указать **Preferences → ALG → Python** (полный путь к `python.exe`).

---

## Быстрый старт

### Python (движок)

Требования: **Python 3.7+** (только стандартная библиотека). Для сборки `.c` — **GCC** (или другой C-компилятор).

```bash
python main.py examples/en/01_hello.alg
python main.py program.alg --check
python main.py program.alg --transpile
python main.py --repl --lang ru
python main.py --version
```

Полный цикл для `program.alg` (interpret → C → gcc → exe):

```bash
python launcher.py
```

### Eclipse (плагин)

См. раздел выше и **[IDE_SETUP.md](IDE_SETUP.md)**. После dropins + `install_dropins.ps1` — перспектива ALG и Run.

---

## Примеры

| Путь | Тема |
|------|------|
| `examples/06_files.alg` | файловый I/O |
| `examples/09_records.alg` | записи |
| `examples/10_module.alg` | модули |
| `examples/en/*.alg` | те же темы на английских ключевых словах |
| `program.alg` + `utils.alg` | сводная демо-программа |

---

## Тестирование

```bash
python -m pytest test_basic.py test_bilingual.py -q
```

Или без pytest (unittest-стиль, если тесты запускаются как скрипт — см. сами файлы). Покрывают лексер/парсер, интерпретатор, билингвальность, модули, транспиляцию (и GCC при наличии `gcc` в PATH).

Зависимости рантайма: `requirements.txt` (stdlib only). Отдельного LICENSE-файла в корне нет.

---

## Связанные заметки

- Файловые пути в `открыть` и `использовать` **не фильтруются** (без sandbox) — ответственность автора программы и преподавателя.
- `AUDIT.md` описывает закрытые пункты аудита прототипа; актуальные версии и CLI — в этом README и `version.py`.
