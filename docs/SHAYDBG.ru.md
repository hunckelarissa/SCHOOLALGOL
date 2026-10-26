# SHAYDBG — протокол Step Debug

Краткая спецификация wire-протокола между интерпретатором SCHOOLALGOL и Eclipse ALG (**Step Debug**). Реализация: `shay_debug_protocol.py`, пауза/команды в `interpreter.py`; клиент: `org.myau.shaya.ide.debug` (`ShayaDebugTarget`, `ShayaDebugEvent`).  
**English:** [SHAYDBG.md](SHAYDBG.md).

## Назначение

Пошаговая отладка `.alg` без отдельного debug-сервера: IDE управляет процессом через **stdin** (JSON-команды); интерпретатор публикует состояние строками **`SHAYDBG ` + JSON** (события). Не путать с Run / Check и устаревшим CLI `--debug` (убран из плагина).

## Включение

| Как | Детали |
|-----|--------|
| CLI | `python main.py program.alg --debug-protocol` |
| Breakpoints при старте | `--break N` (можно повторять; также `--break=N`) |
| Eclipse | Breakpoint на линейке → **ALG → Step Debug** (Ctrl+Alt+Shift+D) |

Запуск из IDE: `main.py <file> --debug-protocol` + `--break` для **включённых** маркеров (`ShayaStepDebugLaunch`). Несовместимо с `--check`, `--transpile`, `--dump-ast`, `--repl`. В режиме протокола `--verbose`/`--trace` подавляются.

## Транспорт

| Направление | Формат |
|-------------|--------|
| IDE → интерпретатор | одна JSON-строка в stdin, поле `cmd` или `command` |
| Интерпретатор → IDE | stderr: `SHAYDBG ` + компактный JSON, `flush` |

Префикс: `SHAYDBG ` (`PROTOCOL_PREFIX`). Eclipse Step Debug сливает stderr в stdout (`redirectErrorStream`); парсер отбрасывает строки без префикса. Человеческие баннеры (`[ШАЯ][отладка]…`) — не протокол.

**Stdin общий** с `ввод`: отладочные команды обрабатываются **только на паузе**. Во время `ввод` JSON из `_DEBUG_STDIN_CMDS` игнорируется (не считается вводом).

## События (→ IDE)

Поле-дискриминатор: `shay`.

| `shay` | Поля | Смысл |
|--------|------|--------|
| `stopped` | `line`, `source`, `reason`, `path`, `globals`, `locals`, `stack`, `arrays`, `records` | Пауза перед оператором |
| `terminated` | `exit` | Конец сессии (код выхода) |
| `eval` | `expr`, `value`, `ok`, `error` | Ответ на `eval`/`watch` |
| `set` | `name`, `value`, `ok`, `error` | Ответ на `set`/`assign` |
| `vars` | `globals`, `locals`, `arrays`, `records` | Ответ на `vars` (снимок; остаёмся на паузе) |

**`reason`** (нормализованный): `breakpoint` \| `step` \| `step_into` \| `step_out`.

**`stack`**: кадры `{name, line, source, path}` (IDE: innermost-first после разбора).

**`globals`/`locals`**: скаляры (и словари). **`arrays`**: имя → `{offset, values[]}` для `таб`. **`records`**: имя → карта полей экземпляра `запись`. Большие map/list обрезаются до 80 в `_jsonable`.

## Команды (stdin ← IDE)

| `cmd` (алиасы) | Поля | Действие |
|----------------|------|----------|
| `step` / `step_over` / `s` / `n` / `next` | — | Step Over: пауза на следующем операторе при глубине стека **≤** текущей (`reason=step`) — внутрь вызова не заходит |
| `step_into` / `into` | — | Step Into: пауза на **любом** следующем операторе, включая вход в вызов (`reason=step_into`) |
| `step_out` / `out` | — | Step Out: пауза, когда глубина стека **меньше** текущей (`reason=step_out`) |
| `continue` / `c` / `cont` | — | Режим «только breakpoints» |
| `quit` / `q` / `exit` | — | `SystemExit(0)` |
| `breakpoints` / `set_breakpoints` / `bps` | `items[]` | Перезаписать BP: `{line, enabled?, path?}`. **`enabled: false` учитывается**. `condition` / `hitCount` / `logMessage` / `suspend` — **движок не исполняет** |
| `eval` / `watch` / `evaluate` | `expr` / `expression` | Оценка; ответ `shay=eval` |
| `set` / `assign` | `name`, `value` | `value` — как у eval; ответ `shay=set` |
| `vars` | — | Событие `shay=vars`; остаёмся на паузе |

Пример: `{"cmd":"eval","expr":"x + 1"}`.

## Breakpoints и пауза

1. Старт: `--break` → множество строк файла запуска (`path` пустой = файл запуска / любой при совпадении номера).
2. Режим `_protocol_auto=True` (после start/`continue`): пауза только на BP.
3. После `step*`: `_protocol_auto=False`; пауза по правилу `_step_depth` или на breakpoint.
4. На каждом `stopped` IDE шлёт `breakpoints` с `path`; отключённые маркеры не включаются / идут с `enabled: false`.
5. Совпадение BP: номер строки оператора + опциональный нормализованный `path` (`_bp_items`).

## Переменные / стек / eval / set

| Возможность | Статус |
|-------------|--------|
| Variables view | `globals`/`locals` + `arrays`/`records` последнего `stopped` |
| Stack frames | Из `stack` + `path` для source locator |
| Expressions / Watch | `eval` только пока suspended |
| Изменение переменной | `set` / UI Variables → `set`; константы запрещены |
| Обновить снимок | `vars` → `shay=vars` без шага |
| Подмножество eval | Парсер `logical_or_expr`: имена, литералы, `a.b`, `a[i]`, унарные/бинарные (`+ - * /`, сравнения, `и`/`или`). **Не:** операторы, `:=`, многострочность, полный I/O |

## Ограничения / non-goals

- Не DAP, не сокет, не multi-thread, не remote attach.
- Нет условных BP / hit count / logpoint на движке (`enabled` **поддерживается**).
- `step_over` / `step_into` / `step_out` учитывают `len(call_stack)` (`_step_depth`).
- Нет отдельного события `ready`.
- Транспиляция C и `--check` через SHAYDBG не отлаживаются.
- Один процесс / один поток интерпретатора.

## Источники

| Сторона | Файлы |
|---------|--------|
| Движок | `shay_debug_protocol.py`, `interpreter.py` (`_protocol_pause`), `main.py` |
| IDE | `ShayaDebugEvent`, `ShayaDebugTarget`, `ShayaStepDebugLaunch`, `ShayaBreakpoints` |

Установка IDE: [IDE_SETUP.ru.md](../IDE_SETUP.ru.md). Обзор: [README.ru.md](../README.ru.md).
