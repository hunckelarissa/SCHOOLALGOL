# SCHOOLALGOL — School Algol (.alg)

Учебный язык программирования **School Algol** (расширение `.alg`) и его среда выполнения: интерпретатор на Python, семантический анализ, транспиляция в C, отладка SHAYDBG и плагин Eclipse **ALG**.

| Компонент | Версия | Источник |
|-----------|--------|----------|
| Движок (интерпретатор / транспилятор) | **1.2.1** | `version.py` |
| Плагин Eclipse `org.myau.shaya.ide` | **0.6.7** | `META-INF/MANIFEST.MF` |

Документы:

| Файл | Содержание |
|------|------------|
| **[GRAMMAR.md](GRAMMAR.md)** | Грамматика, семантика, RU/EN, ограничения C |
| **[IDE_SETUP.md](IDE_SETUP.md)** | Установка и настройка плагина ALG в Eclipse |
| **[docs/SHAYDBG.md](docs/SHAYDBG.md)** | Протокол Step Debug (SHAYDBG): события, команды, BP |
| **[TODO_2026.md](TODO_2026.md)** | Аудит 2026 и закрытый бэклог (CRLF, builtins, break/continue, C-паритет) |
| **[AUDIT.md](AUDIT.md)** | Исторический технический аудит прототипа (закрыт) |

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
| `test_basic.py`, `test_bilingual.py` | Базовые и билингвальные тесты |
| `test_audit_2026.py`, `test_backlog_2026.py`, `test_modules_arrays_2026.py` | Тесты аудита/бэклога 2026 |
| `pytest.ini` | Исключает `Gemini_reference/` из сбора тестов |
| `examples/`, `examples/en/` | Примеры (RU и EN) |
| `program.alg`, `utils.alg` | Демо-программа и модуль |
| `org.myau.shaya.ide/` | Исходники плагина Eclipse ALG |
| `install_dropins.ps1` | Синхронизация `*.py`, `tools/shaya-run.bat` (и опционально JAR / examples) в Eclipse dropins |
| `Gemini_reference/` | Справочный снимок (документы/код другого бренда) |

---

## Язык School Algol (.alg)

Подробности — в **[GRAMMAR.md](GRAMMAR.md)**. Кратко по возможностям движка **1.2.1**.

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
- `нц пока … кц` / `loop while … eloop`.
- `нц для i от a до b [шаг s] … кц` / `loop for … from … to … [step s] … eloop` — без шага направление ±1 выбирается автоматически.
- `выход` / `break`, `продолжить` / `continue` — только внутри цикла.
- `возврат` / `return` [выражение] — из процедуры/функции (с выражением — только при `рез`).
- `алг` / `proc` с `арг`/`рез` (`arg`/`res`); тело в `нач`…`кон` / `begin`…`end`.
- Операторы: `+ - * /`, сравнения `= <> > < >= <=`, логика `и`/`или`/`не` (`and`/`or`/`not`).

### Встроенные (RU / EN)

`открыть`/`open`, `закрыть`/`close`, `конецфайла`/`eof`, `корень`/`sqrt`, `модуль`/`abs`, `случ`/`rand`, `случцел`/`randint`, `длина`/`len`, `подстрока`/`substr`, `вверх`/`upper`, `вниз`/`lower`, `вцел`/`toint`, `ввещ`/`toreal`, `встроку`/`tostr`, `остаток`/`mod`, `целдел`/`div`, `степень`/`pow`, `мин`/`min`, `макс`/`max`, `округление`/`round`, `знак`/`sign`, `син`/`sin`, `кос`/`cos`, `найти`/`find`, `размер`/`size`.

Режимы файла: `чтение`/`read`, `запись`/`write`, `дозапись`/`append`.

### Интерпретатор и C

| Режим | Команда | Результат |
|-------|---------|-----------|
| Интерпретация | `python main.py файл.alg` или `--run` | выполнение в Python |
| Транспиляция | `python main.py файл.alg --transpile` | файл `файл.c` |
| Проверка | `python main.py файл.alg --check` | lex + parse + семантика, без выполнения |

В C: `файл` → `FILE*`; записи/перечисления; словари; forward-прототипы функций; параметры-`таб` как `(T*, len, offset)`; `--keep-cyrillic`, `--permissive`.

Вывод: целые без `.0`; логические — **да** / **нет** (в т.ч. результат функции типа `лог`).

**Ограничения паритета интерпретатор ↔ C:**

- `длина(число)` — в интерпретаторе длина `str(n)`; в C ожидается строка.
- `случ` / `случцел` — разные ГПСЧ (Python vs C), последовательности не совпадают.
- Словарь в C хранит только `double`.
- Сеть / host-API и упаковка VS Code из `Gemini_reference` в этот репозиторий не портированы.

### Отладка и диагностика CLI

| Флаг | Назначение |
|------|------------|
| `--run` | Явный режим выполнения (по умолчанию) |
| `--verbose` | Этапы пайплайна и токены RU/EN в stderr |
| `--trace` | Пошаговая трассировка операторов |
| `--dump-ast` [`--dump-ast-format text\|json`] | Дерево разбора |
| `--repl` [`--lang ru\|en`] | Интерактивный режим |
| `--debug-protocol` | SHAYDBG JSONL (для Eclipse Step Debug); спека — [docs/SHAYDBG.md](docs/SHAYDBG.md) |
| `--break N` | Точка останова по номеру строки (можно повторять) |
| `--warnings-as-errors` | Предупреждения → exit 3 |
| `--keep-cyrillic` | С `--transpile`: кириллица в идентификаторах C |
| `--permissive` | С `--transpile`: неизвестные узлы → предупреждение |
| `--version` / `--help` | Версия / справка |

---

## Плагин ALG (Eclipse)

Плагин **`org.myau.shaya.ide` 0.6.7** — IDE для `.alg` поверх движка SCHOOLALGOL. В меню, перспективе и Preferences бренд **ALG** (Java-пакет `org.myau.shaya.ide` сохранён).

Полная установка — **[IDE_SETUP.md](IDE_SETUP.md)**.

### Возможности

- Редактор `.alg`: подсветка, автодополнение и шаблоны Ctrl+Space (RU и EN: `алг…` / `proc…`, `если…` / `if…` …).
- **ALG → Run** (Ctrl+Alt+R) — выполнить через `main.py`.
- **ALG → Check** (Ctrl+Alt+C) — `main.py --check` (lex + parse + семантика).
- **ALG → Step Debug** (Ctrl+Alt+Shift+D) — пошаговая отладка: breakpoints на линейке + `--debug-protocol` / SHAYDBG ([спека](docs/SHAYDBG.md)).
- **ALG → Run Last** (Ctrl+Alt+L).
- Мастер **ALG Project** / New Hello — образцы `Hello.alg` (RU) и `Hello_en.alg` (EN).
- Перспектива **ALG**, маркеры в Problems (подсказки по-русски), консоль с гиперссылками на строки.
- **Welcome** при первом запуске; **Учебный трек…** → `examples/track/`; **Грамматика…** → `GRAMMAR.md`.
- Редактирование: Toggle Comment (`|`), Go to Matching Block, Quick Outline, Go to Declaration (F3), Find References, Rename, Reindent и др.
- **Preferences → ALG:** Toolchain home, Extra args, Python, отступ, Check on save, **Validate…**, повтор Welcome.

Один движок: расширение `.alg` → `schoolalgol-shaya/interpreters/SchoolAlgol/main.py`. CLI Debug скрыт; для выполнения — Run, для шагов — Step Debug.

### Установка (кратко)

1. В Eclipse `dropins` положить JAR: `org.myau.shaya.ide_0.6.7.jar`.
2. Рядом — toolchain `dropins/schoolalgol-shaya/` (`tools/shaya-run.bat`, `interpreters/SchoolAlgol/*.py`).
3. Синхронизация из корня репозитория:

```powershell
cd F:\proj\SCHOOLALGOL
.\install_dropins.ps1
.\install_dropins.ps1 -PluginJar
.\install_dropins.ps1 -Examples   # учебный трек + примеры
```

4. Перезапустить Eclipse. При необходимости: **Preferences → ALG → Toolchain home** = путь к `schoolalgol-shaya`, **Validate…**.

Старые JAR `0.6.1`…`0.6.6` из dropins удалять (если файл «занят» — закройте Eclipse и удалите вручную). Разработка из исходников: PDE → Import `org.myau.shaya.ide` → Run As → Eclipse Application.

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
| `examples/01_hello.alg` … `05_arrays.alg`, `07_strings.alg` | базовые уроки (RU) |
| `examples/06_files.alg` | файловый I/O |
| `examples/09_records.alg` | записи |
| `examples/10_module.alg` | модули |
| `examples/en/*.alg` | те же темы на английских ключевых словах |
| `examples/track/README.md` | учебный трек (оглавление) |
| `program.alg` + `utils.alg` | сводная демо-программа |

---

## Тестирование

```bash
python -m pytest -q
```

`pytest.ini` ограничивает сбор тестов корнем репозитория (`Gemini_reference/` исключён).

| Файл | Фокус |
|------|--------|
| `test_basic.py` | лексер, парсер, интерпретатор, модули, GCC |
| `test_bilingual.py` | RU/EN синонимы |
| `test_audit_2026.py` | CRLF, void, break, builtins, SHAYDBG step\* |
| `test_backlog_2026.py` | да/нет, шаг, return, continue, C-прототипы |
| `test_modules_arrays_2026.py` | `module_loader`, `размер(таб)` в C |

При наличии `gcc` в PATH часть тестов проверяет паритет интерпретатор ↔ exe. Зависимости рантайма: `requirements.txt` (stdlib only).

---

## Связанные заметки

- Файловые пути в `открыть` и `использовать` **не фильтруются** (без sandbox) — ответственность автора программы и преподавателя.
- План аудита 2026 и его закрытие — [TODO_2026.md](TODO_2026.md); ранний аудит прототипа — [AUDIT.md](AUDIT.md). Актуальные версии — таблица в начале README и `version.py`.
