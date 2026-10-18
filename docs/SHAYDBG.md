# SHAYDBG — протокол Step Debug

Краткая спецификация wire-протокола между интерпретатором SCHOOLALGOL и Eclipse ALG (**Step Debug**). Реализация: `shay_debug_protocol.py`, пауза/команды в `interpreter.py`; клиент: `org.myau.shaya.ide.debug` (`ShayaDebugTarget`, `ShayaDebugEvent`).

## Назначение

Пошаговая отладка `.alg` без отдельного debug-сервера: IDE управляет процессом через **stdin** (JSON-команды), интерпретатор публикует состояние строками **`SHAYDBG ` + JSON** (события). Не путать с Run / Check и с устаревшим CLI `--debug` (в SCHOOLALGOL не используется).

## Включение

| Способ | Как |
|--------|-----|
| CLI | `python main.py программа.alg --debug-protocol` |
| Точки останова при старте | `--break N` (повторять; также `--break=N`) |
| Eclipse | Breakpoint на линейке → **ALG → Step Debug** (Ctrl+Alt+Shift+D) |

Launch IDE: `main.py <файл> --debug-protocol` + `--break` по enabled-маркерам (`ShayaStepDebugLaunch`). Несовместимо с `--check`, `--transpile`, `--dump-ast`, `--repl`. В режиме протокола `--verbose`/`--trace` глушатся.

## Транспорт

| Направление | Формат |
|-------------|--------|
| IDE → интерпретатор | одна JSON-строка на stdin, поле `cmd` или `command` |
| Интерпретатор → IDE | stderr: `SHAYDBG ` + компактный JSON (без пробелов вокруг `:`/`,`), `flush` |

Префикс: `SHAYDBG ` (`PROTOCOL_PREFIX`). Eclipse при Step Debug сливает stderr в stdout (`redirectErrorStream`); парсер отбрасывает строки без префикса. Человеческие баннеры (`[ШАЯ][отладка]…`, `[ШАЯ][ввод]…`) — не протокол.

**Stdin общий** с оператором `ввод`: команды отладки обрабатываются **только на паузе**. Во время `ввод` JSON-команды из `_DEBUG_STDIN_CMDS` игнорируются (не считаются вводом).

## События (stdout/stderr → IDE)

Поле-дискриминатор: `shay`.

| `shay` | Поля | Смысл |
|--------|------|--------|
| `stopped` | `line`, `source`, `reason`, `path`, `globals`, `locals`, `stack`, `arrays`, `records` | Пауза перед оператором |
| `terminated` | `exit` | Конец сессии (код выхода) |
| `eval` | `expr`, `value`, `ok`, `error` | Ответ на `eval`/`watch` |
| `set` | `name`, `value`, `ok`, `error` | Ответ на `set`/`assign` |

**`reason`** (нормализованный): `breakpoint` \| `step` \| `step_into` \| `step_out`.

**`stack`**: массив кадров `{name, line, source, path}` (IDE: innermost-first после разбора). **`globals`/`locals`**: плоские карты имя→JSON-значение (скаляры; сложные → `str`, усечение больших dict/list до 80 элементов в `_jsonable`). **`arrays`/`records`**: зарезервированы в схеме; текущий интерпретатор обычно шлёт `{}` (структуры могут попадать в `globals`/`locals` как есть).

## Команды (stdin ← IDE)

| `cmd` (алиасы) | Поля | Действие |
|----------------|------|----------|
| `step` / `step_over` / `s` / `n` / `next` | — | Step Over: пауза на следующем операторе при глубине стека **≤** текущей (`reason=step`) — внутрь вызова не заходит |
| `step_into` / `into` | — | Step Into: пауза на **любом** следующем операторе, включая вход в вызов (`reason=step_into`) |
| `step_out` / `out` | — | Step Out: пауза, когда глубина стека **меньше** текущей (`reason=step_out`) |
| `continue` / `c` / `cont` | — | Режим «только breakpoints» |
| `quit` / `q` / `exit` | — | `SystemExit(0)` |
| `breakpoints` / `set_breakpoints` / `bps` | `items[]` | Перезаписать BP: `{line, enabled?, path?}` (+ IDE может слать `condition`/`hitCount`/`logMessage`/`suspend` — **движок их не исполняет**) |
| `eval` / `watch` / `evaluate` | `expr` / `expression` | Оценка; ответ `shay=eval` |
| `set` / `assign` | `name`, `value` | `value` — выражение как у eval; ответ `shay=set` |
| `vars` | — | В whitelist stdin (фильтр при `ввод`); **обработчика на паузе нет** |

Пример: `{"cmd":"eval","expr":"x"}`.

## Breakpoints и пауза

1. Старт: `--break` → множество строк файла запуска (`path` пустой = файл запуска / любой при совпадении номера).
2. Режим `_protocol_auto=True` (после start/`continue`): пауза только на BP.
3. После `step*` : `_protocol_auto=False`; пауза по правилу `_step_depth` (см. таблицу команд) или на breakpoint.
4. На каждом `stopped` IDE шлёт `breakpoints` с `path` (ресинк без гонки со `ввод` на старте).
5. Совпадение BP: номер строки оператора + опциональный нормализованный `path` (`_bp_items`).

## Переменные / стек / eval / set

| Возможность | Статус |
|-------------|--------|
| Variables view | Из `globals`/`locals` последнего `stopped` |
| Stack frames | Из `stack` + `path` для source locator |
| Expressions / Watch | `eval` только пока suspended |
| Изменение переменной | `set` / UI Variables → `set`; константы запрещены |
| Eval | Имя переменной (поиск по стеку), литералы `"…"`, `да`/`нет`/`истина`/`ложь`, int/float; **не** произвольные выражения Алгола |

## Ограничения / non-goals

- Не DAP, не сокет, не multi-thread, не remote attach.
- Нет условных BP / hit count / logpoint на стороне движка (поля в sync — для IDE).
- `step_over` / `step_into` / `step_out` учитывают `len(call_stack)` (`_step_depth` в интерпретаторе).
- Нет отдельного события `ready`; `vars` не реализован как запрос снимка.
- Транспиляция в C и `--check` не отлаживаются через SHAYDBG.
- Протокол рассчитан на один процесс / один поток исполнения интерпретатора.

## Исходники

| Сторона | Файлы |
|---------|--------|
| Движок | `shay_debug_protocol.py`, `interpreter.py` (`_protocol_pause`), `main.py` |
| IDE | `ShayaDebugEvent`, `ShayaDebugTarget`, `ShayaStepDebugLaunch`, `ShayaBreakpoints` |

Установка IDE: [IDE_SETUP.md](../IDE_SETUP.md). Обзор проекта: [README.md](../README.md).
