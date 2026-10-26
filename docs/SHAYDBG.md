# SHAYDBG — Step Debug protocol

Short wire-protocol spec between the SCHOOLALGOL interpreter and Eclipse ALG (**Step Debug**). Implementation: `shay_debug_protocol.py`, pause/commands in `interpreter.py`; client: `org.myau.shaya.ide.debug` (`ShayaDebugTarget`, `ShayaDebugEvent`).  
**Russian:** [SHAYDBG.ru.md](SHAYDBG.ru.md).

## Purpose

Step-debug `.alg` without a separate debug server: the IDE drives the process via **stdin** (JSON commands); the interpreter publishes state as **`SHAYDBG ` + JSON** lines (events). Do not confuse with Run / Check or the obsolete CLI `--debug` (removed from the plug-in).

## Enabling

| How | Details |
|-----|---------|
| CLI | `python main.py program.alg --debug-protocol` |
| Breakpoints at start | `--break N` (repeatable; also `--break=N`) |
| Eclipse | Ruler breakpoint → **ALG → Step Debug** (Ctrl+Alt+Shift+D) |

IDE launch: `main.py <file> --debug-protocol` + `--break` for **enabled** markers (`ShayaStepDebugLaunch`). Incompatible with `--check`, `--transpile`, `--dump-ast`, `--repl`. In protocol mode `--verbose`/`--trace` are suppressed.

## Transport

| Direction | Format |
|-----------|--------|
| IDE → interpreter | one JSON line on stdin, field `cmd` or `command` |
| Interpreter → IDE | stderr: `SHAYDBG ` + compact JSON (no spaces around `:`/`,`), `flush` |

Prefix: `SHAYDBG ` (`PROTOCOL_PREFIX`). Eclipse Step Debug merges stderr into stdout (`redirectErrorStream`); the parser drops lines without the prefix. Human banners (`[ШАЯ][отладка]…`, …) are not protocol.

**Stdin is shared** with `input`: debug commands are handled **only while paused**. During `input`, JSON commands from `_DEBUG_STDIN_CMDS` are ignored (not treated as input).

## Events (→ IDE)

Discriminator field: `shay`.

| `shay` | Fields | Meaning |
|--------|--------|---------|
| `stopped` | `line`, `source`, `reason`, `path`, `globals`, `locals`, `stack`, `arrays`, `records` | Pause before a statement |
| `terminated` | `exit` | Session end (exit code) |
| `eval` | `expr`, `value`, `ok`, `error` | Reply to `eval`/`watch` |
| `set` | `name`, `value`, `ok`, `error` | Reply to `set`/`assign` |
| `vars` | `globals`, `locals`, `arrays`, `records` | Reply to `vars` (snapshot; stay paused) |

**`reason`** (normalized): `breakpoint` \| `step` \| `step_into` \| `step_out`.

**`stack`**: frames `{name, line, source, path}` (IDE: innermost-first after parse).

**`globals`/`locals`**: scalar (and dict) name→JSON maps. **`arrays`**: name → `{offset, values[]}` for `таб`. **`records`**: name → field map for `запись` instances. Large maps/lists truncated to 80 entries in `_jsonable`.

## Commands (stdin ← IDE)

| `cmd` (aliases) | Fields | Action |
|-----------------|--------|--------|
| `step` / `step_over` / `s` / `n` / `next` | — | Step Over: pause at next statement when stack depth **≤** current (`reason=step`) — does not enter calls |
| `step_into` / `into` | — | Step Into: pause at **any** next statement, including into a call (`reason=step_into`) |
| `step_out` / `out` | — | Step Out: pause when stack depth is **less** than current (`reason=step_out`) |
| `continue` / `c` / `cont` | — | Breakpoints-only mode |
| `quit` / `q` / `exit` | — | `SystemExit(0)` |
| `breakpoints` / `set_breakpoints` / `bps` | `items[]` | Replace BPs: `{line, enabled?, path?}`. **`enabled: false` is honored** (line omitted). `condition` / `hitCount` / `logMessage` / `suspend` — **ignored by the engine** |
| `eval` / `watch` / `evaluate` | `expr` / `expression` | Evaluate; reply `shay=eval` |
| `set` / `assign` | `name`, `value` | `value` like eval; reply `shay=set` |
| `vars` | — | Emit `shay=vars` snapshot; remain paused |

Example: `{"cmd":"eval","expr":"x + 1"}`.

## Breakpoints and pause

1. Start: `--break` → line set for the launch file (empty `path` = launch file / any matching line).
2. `_protocol_auto=True` (after start/`continue`): pause only on BP.
3. After `step*`: `_protocol_auto=False`; pause by `_step_depth` (see command table) or on breakpoint.
4. On each `stopped` the IDE sends `breakpoints` with `path` (resync without racing `input` at start); disabled markers are not included / sent with `enabled: false`.
5. BP match: statement line number + optional normalized `path` (`_bp_items`).

## Variables / stack / eval / set

| Capability | Status |
|------------|--------|
| Variables view | `globals`/`locals` + `arrays`/`records` of last `stopped` |
| Stack frames | From `stack` + `path` for source locator |
| Expressions / Watch | `eval` only while suspended |
| Change variable | `set` / UI Variables → `set`; constants forbidden |
| Refresh snapshot | `vars` → `shay=vars` without stepping |
| Eval subset | Parser `logical_or_expr`: names, literals, `a.b`, `a[i]`, unary/binary (`+ - * /`, comparisons, `и`/`или`). **Not:** statements, `:=`, multi-stmt, full I/O |

## Limits / non-goals

- Not DAP, not socket, not multi-thread, not remote attach.
- No conditional BP / hit count / logpoint on the engine (`enabled` **is** supported).
- `step_over` / `step_into` / `step_out` use `len(call_stack)` (`_step_depth` in the interpreter).
- No separate `ready` event.
- C transpile and `--check` are not debugged via SHAYDBG.
- One process / one interpreter thread.

## Sources

| Side | Files |
|------|--------|
| Engine | `shay_debug_protocol.py`, `interpreter.py` (`_protocol_pause`), `main.py` |
| IDE | `ShayaDebugEvent`, `ShayaDebugTarget`, `ShayaStepDebugLaunch`, `ShayaBreakpoints` |

IDE setup: [IDE_SETUP.md](../IDE_SETUP.md). Project overview: [README.md](../README.md).
