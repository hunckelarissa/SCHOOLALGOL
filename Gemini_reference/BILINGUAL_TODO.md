# TODO — двуязычный синтаксис .alg (RU + EN)

**Версия документа:** 1.0  
**Дата:** 15.06.2026  
**Целевая версия языка:** 1.1.0 (MINOR — новая возможность, полная обратная совместимость с русским синтаксисом)

Модель как в **1С:Предприятие**: русские и английские ключевые слова — **синонимы одного токена**. Внутри компилятора единый `TokenType`; парсер и семантика не различают язык написания.

**Канон в документации:** русский. **Английский:** равноправный синоним для международной и учебной аудитории.

Статус: `[ ]` — не начато, `[~]` — в работе, `[x]` — выполнено.

---

## Принципы (обязательны)

1. **Самобытность** — EN-синонимы не превращают `.alg` в ШАЯ; уникальные конструкции (`tab`, `rec`, `dict`, `import`, `loop`/`eloop`, `<>`) сохраняются.
2. **Один токен — много написаний** — расширение только `KEYWORDS` / алиасов builtins; **не** дублировать грамматику в парсере.
3. **Смешение в одном файле** — допустимо (`if` + `то` + `endif`); тесты обязаны это проверить.
4. **Регистронезависимость** — как сейчас: `IF`, `If`, `if` → `TokenType.ЕСЛИ`.
5. **Идентификаторы** — кириллица и латиница (уже в лексере); зарезервированные EN-слова (`if`, `for`, `int` …) нельзя использовать как имена переменных (как и русские аналоги).

---

## Таблица синонимов (утверждённый набор)

### Объявления и структура программы

| RU | EN (синонимы) | `TokenType` |
|----|---------------|-------------|
| алг | **proc** | АЛГ |
| арг | **arg** | АРГ |
| рез | **res** | РЕЗ |
| нач | **begin** | НАЧ |
| кон | **end** | КОН |
| конст | **const** | КОНСТ |
| использовать | **import** | ИСПОЛЬЗОВАТЬ |

### Типы

| RU | EN | `TokenType` |
|----|-----|-------------|
| цел | **int** | ЦЕЛ |
| вещ | **real** | ВЕЩ |
| лог | **bool** | ЛОГ |
| лит | **str** | ЛИТ |
| таб | **tab** | ТАБ |
| файл | **file** | ФАЙЛ |
| словарь | **dict** | СЛОВАРЬ |
| запись | **rec** | ЗАПИСЬ |
| переч | **enum** | ПЕРЕЧ |

### Операторы ввода-вывода

| RU | EN | `TokenType` |
|----|-----|-------------|
| ввод | **input** | ВВОД |
| вывод | **output** | ВЫВОД |

### Условия

| RU | EN | `TokenType` |
|----|-----|-------------|
| если | **if** | ЕСЛИ |
| то | **then** | ТО |
| иначе | **else** | ИНАЧЕ |
| все | **endif** | ВСЕ |

### Циклы

| RU | EN | `TokenType` |
|----|-----|-------------|
| нц | **loop** | НЦ |
| кц | **eloop** | КЦ |
| для | **for** | ДЛЯ |
| пока | **while** | ПОКА |
| от | **from** | ОТ |
| до | **to** | ДО |

### Логика и литералы

| RU | EN | `TokenType` |
|----|-----|-------------|
| да | **true** | ДА |
| нет | **false** | НЕТ |
| и | **and** | И |
| или | **or** | ИЛИ |
| не | **not** | НЕ |

### Операторы (без изменений)

`:=`, `=`, `<>`, `>=`, `<=`, `+`, `-`, `*`, `/`, `.`, `[]`, `()` — общие для обоих языков.

---

## Точка входа (главная программа)

| RU (сейчас) | EN (добавить) |
|-------------|---------------|
| основнаяпрограмма | **mainprogram** |

Оба имени вызываются при запуске. Реализация: `MAIN_PROGRAM_NAMES = ("основнаяпрограмма", "mainprogram")` в `constants.py`; проверки в `interpreter.py`, `semantic_analyzer.py`, `c_transpiler.py`, `repl.py`.

- [x] Список синонимов точки входа в `constants.py`
- [x] Обновить все сравнения с `MAIN_PROGRAM_NAME` (через `is_main_program` / `MAIN_PROGRAM_NAMES`)
- [x] Сообщения об ошибках: «ожидается `основнаяпрограмма` / `mainprogram`»

---

## Встроенные функции и процедуры (алиасы)

Отдельно от `KEYWORDS` — словарь `BUILTINS` и ветки в `c_transpiler.visit_SubroutineCall`.

| RU | EN (алиас) |
|----|------------|
| открыть | **open** |
| закрыть | **close** |
| конецфайла | **eof** |
| корень | **sqrt** |
| модуль | **abs** |
| случ | **rand** |
| случцел | **randint** |
| длина | **len** |
| подстрока | **substr** |
| вверх | **upper** |
| вниз | **lower** |
| вцел | **toint** |
| ввещ | **toreal** |
| встроку | **tostr** |

- [x] `builtin_names.py` — единый реестр `BUILTIN_ALIASES` → каноническое имя
- [x] `interpreter.py` — разрешение имени вызова через алиасы
- [x] `c_transpiler.py` — те же алиасы + генерация C
- [x] `types_model.py` — `BUILTIN_ARITY` по каноническим именам
- [x] `semantic_analyzer.py` — arity для EN-имён

---

## Режимы файлов (`открыть` / `open`)

Строковые литералы режима (семантика, не лексер):

| RU | EN |
|----|-----|
| чтение | **read** |
| запись | **write** |
| дозапись | **append** |

- [x] `alg_builtins.built_in_open` — `mode_map` с EN
- [x] `c_transpiler._file_mode_c` — EN-строки
- [x] Документировать в `GRAMMAR.md`

---

## Примеры эквивалентных программ

### RU (канон)

```alg
алг основнаяпрограмма
нач
  цел x
  если x > 0 то
    вывод "ok"
  все
кон
```

### EN (после внедрения)

```alg
proc mainprogram
begin
  int x
  if x > 0 then
    output "ok"
  endif
end
```

### Цикл

```alg
| Полностью RU
нц для i от 1 до 10
  вывод i
кц

| Полностью EN
loop for i from 1 to 10
  output i
eloop

| Смешанный (допустим после B2)
loop for i от 1 to 10
  output i
eloop
```

### Модуль

```alg
import "utils.alg"

proc mainprogram
begin
  output Fact(5)
end
```

---

## План реализации по фазам

### Фаза B0 — Спецификация (этот документ)

- [x] Таблица синонимов RU ↔ EN
- [x] Список затрагиваемых подсистем
- [x] Утверждение набора — **mainprogram**

### Фаза B1 — Лексер и токены (ядро)

**Файлы:** `lang_tokens.py`, `lexer.py`

- [x] Расширить `KEYWORDS` всеми EN-синонимами из таблицы выше
- [x] Вынести словарь в структурированный вид (`_RU_KEYWORDS`, `_EN_KEYWORDS`, merge)
- [x] Тест: EN-синонимы → ожидаемый `TokenType` (`tests/test_bilingual.py`)
- [x] Тест: регистронезависимость EN (`PROC`, `Proc`, `proc`)
- [x] Тест: `true`/`false` не путаются с идентификаторами `trueish` (целое слово)

**Критерий:** `python -m pytest tests/test_lexer.py -q` + новый `tests/test_bilingual_lexer.py`

### Фаза B2 — Парсер и AST

**Файлы:** `parser.py` (ожидается **без изменений**)

- [x] Тест: EN исходник парсится (`tests/test_bilingual.py`)
- [x] Тест: смешанный файл (`if` + `то` + `endif`)
- [x] Тест: пара RU/EN исходников → **изоморфный AST** (`tests/test_bilingual_ast.py`, `ast_compare.py`)

**Критерий:** `tests/test_bilingual_parser.py`

### Фаза B3 — Семантика и константы

**Файлы:** `constants.py`, `semantic_analyzer.py`, `suggestions.py`

- [x] `MAIN_PROGRAM_NAMES` — оба имени точки входа
- [x] `BUILTIN_ALIASES` — разрешение EN-имён встроенных (`builtin_names.py`)
- [x] Подсказки ошибок: EN/RU алиасы builtins (`expand_bilingual_candidates` в `suggestions.py`)
- [x] Сообщения: «не найдена `основнаяпрограмма` / `mainprogram`»

### Фаза B4 — Интерпретатор

**Файлы:** `interpreter.py`, `alg_builtins.py`

- [x] Вызовы builtins по EN-алиасам
- [x] Режимы `open(..., "read"|"write"|"append")`
- [x] `AssignTypeWarning` / типы: `цел / int`, `вцел / toint` в сообщениях
- [x] REPL: `--lang en` (обёртка `proc mainprogram` / `begin` / `end`)

### Фаза B5 — C-транспилятор

**Файлы:** `c_transpiler.py`, `types_model.py`

- [x] `visit_SubroutineCall` — EN builtins
- [x] `_file_mode_c` — EN режимы
- [x] `MAIN_PROGRAM_NAMES` — `main()` из `proc mainprogram`
- [x] Комментарии `// alg:` — для `mainprogram` / `основнаяпрограмма` дублируется синоним (`procedure_alg_comment` в `constants.py`)

### Фаза B6 — CLI и диагностика

**Файлы:** `main.py`, `errors.py`, `repl.py`

- [x] `ParserError`: bilingual-синонимы через `token_type_bilingual_label`
- [x] `format_error` / `_semantic_hint` — bilingual подсказки
- [x] `--verbose`: лог токенов с bilingual-подписью (`«proc» → алг / proc [АЛГ]`)

### Фаза B7 — Примеры и паритет

**Каталог:** `examples/en/`

- [x] `01_hello.alg` … `10_module.alg` — зеркала `examples/01_…`
- [x] `tests/programs/en/` — parity RU ↔ EN (интерпретатор + GCC)
- [x] `tests/test_bilingual_parity.py` — одинаковый stdout для пар RU/EN

### Фаза B8 — Документация

| Файл | Действие |
|------|----------|
| `GRAMMAR.md` | [x] раздел «Двуязычные ключевые слова» |
| `PROGRAMMER.md` | [x] глава «Русский и английский синтаксис» |
| `QUICKSTART.md` | [x] EN-вариант быстрого старта |
| `TUTORIAL.md` | [x] EN-колонка в уроках 1–4, REPL `--lang en` |
| `README.md` | [x] ссылка на двуязычность |
| `CONTRIBUTING.md` | [x] при добавлении ключевого слова — **оба** языка в `KEYWORDS` |
| `CHANGELOG.md` | [x] секция 1.1.0 |

### Фаза B9 — Редактор

**Каталог:** `editor/alg/`

- [x] TextMate-грамматика: подсветка EN-ключевых слов
- [x] `editor/alg/README.md` — установка локально + EN-подсветка

### Фаза B10 — Регрессия и релиз

- [x] Полный прогон: `python -m pytest tests/ -q`
- [x] Покрытие ≥ 80% (~87%)
- [x] Версия `1.1.0` в `version.py`, `pyproject.toml`
- [~] Тег `v1.1.0` — **отложено** (git пока не используем)
- [x] Закрыть этот документ; ссылка из `TODO.md` → «выполнено»

---

## Файлы — сводная матрица изменений

| Файл | Изменения |
|------|-----------|
| `lang_tokens.py` | **+EN в KEYWORDS** |
| `lexer.py` | без логики (только тесты) |
| `parser.py` | без изменений (ожидается) |
| `constants.py` | `MAIN_PROGRAM_NAMES` |
| `alg_builtins.py` | алиасы + mode_map EN |
| `interpreter.py` | main names + builtin aliases |
| `semantic_analyzer.py` | main names + builtin arity |
| `c_transpiler.py` | main + builtins + file modes |
| `types_model.py` | builtin aliases |
| `repl.py` | [x] `--lang en` |
| `errors.py` | [x] bilingual hints |
| `suggestions.py` | [x] EN/RU алиасы builtins |
| `types_model.py` | [x] `type_bilingual_label()` |
| `ast_compare.py` | [x] AST shape |
| `tests/test_bilingual_*.py` | **новые** |
| `examples/en/` | **новые** |
| `editor/alg/*.json` | подсветка EN |

---

## Тестовый план (минимум)

| ID | Тест | Описание |
|----|------|----------|
| T-BL-01 | `test_bilingual_lexer.py` | все EN-синонимы → `TokenType` |
| T-BL-02 | `test_bilingual_ast.py` | RU и EN → одинаковая форма AST |
| T-BL-03 | `test_bilingual_mixed.py` | смешанный синтаксис в одном файле |
| T-BL-04 | `test_bilingual_main.py` | `proc mainprogram` запускается |
| T-BL-05 | `test_bilingual_builtins.py` | `open`, `len`, `sqrt`, … |
| T-BL-06 | `test_bilingual_files.py` | режимы `read`/`write`/`append` |
| T-BL-07 | `test_bilingual_parity.py` | RU/EN examples → одинаковый вывод |
| T-BL-08 | `test_bilingual_transpile.py` | EN → валидный C, GCC |

---

## Риски и решения

| Риск | Решение |
|------|---------|
| EN-слова конфликтуют с именами переменных | Только целые слова; документировать зарезервированный список |
| Дублирование в `BUILTINS` и `c_transpiler` | Единый модуль `builtin_names.py` или секция в `lang_tokens.py` |
| Документация раздувается | Таблица RU \| EN + `examples/en/`; канон — RU |
| Путаница `loop`/`eloop` vs `for`/`while` | В PROGRAMMER.md явная схема: `loop for … eloop`, `loop while … eloop` |
| Смешение с ШАЯ | В README: «не ШАЯ; `proc`/`rec`/`tab` — синтаксис .alg» |

---

## Оценка трудозатрат

| Фаза | Оценка |
|------|--------|
| B1–B2 (лексер, парсер-тесты) | 1–2 дня |
| B3–B5 (семантика, интерпретатор, транспилятор) | 2–3 дня |
| B6–B7 (CLI, примеры, parity) | 1–2 дня |
| B8–B9 (документация, редактор) | 2–3 дня |
| B10 (релиз) | 0.5 дня |
| **Итого** | **~7–10 дней** |

MVP (только B1 + B2 + B4 частично): **~2 дня** — ключевые слова и `mainprogram` без полного parity EN examples.

---

## Чеклист code review (двуязычность)

- [x] Каждое новое RU-ключевое слово имеет EN-синоним в `KEYWORDS` (или явное исключение в этом документе).
- [x] Парсер не ветвится по тексту токена — только по `TokenType`.
- [x] Builtin добавлен в RU и EN алиас (`builtin_names.py`).
- [x] Тест RU + тест EN (параметризованные parity / AST / transpile).
- [x] `GRAMMAR.md` обновлён.
- [x] Не добавлен синтаксис классического ШАЯ под видом EN-синонимов.

---

## Связь с основным планом

Основной **TODO.md** (roadmap v1.0.x) **завершён**.  
Двуязычность — **отдельный эпик** → релиз **v1.1.0**.

После выполнения всех фаз B1–B10:

- [x] Перенести статус в `TODO.md` (раздел «v1.1 двуязычность — выполнено»)
- [x] Отметить `[x]` пункты в этом файле (тег git — когда понадобится)

---

*Документ подготовлен для реализации латинского варианта языка .alg по модели 1С. Утверждённые EN-формы: **proc**, **loop**/**eloop**, **res**, **input**/**output**, **import**, **int**/**real**/**bool**/**str**/**tab**/**dict**/**rec**, **true**/**false**.*
