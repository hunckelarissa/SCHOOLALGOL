# SCHOOLALGOL — School Algol (`.alg`)

Educational programming language **School Algol** (`.alg`) and its runtime: Python interpreter, semantic analysis, C transpilation, SHAYDBG step debugging, and the Eclipse **ALG** plug-in.

| Component | Version | Source |
|-----------|---------|--------|
| Engine (interpreter / transpiler) | **1.2.1** | `version.py` |
| Eclipse plug-in `org.myau.shaya.ide` | **0.6.11** | `META-INF/MANIFEST.MF` |

**Language:** [Русский README](README.ru.md)

| Document | Contents |
|----------|----------|
| **[GRAMMAR.md](GRAMMAR.md)** / [GRAMMAR.ru.md](GRAMMAR.ru.md) | Grammar, semantics, RU/EN keywords, C limits |
| **[IDE_SETUP.md](IDE_SETUP.md)** / [IDE_SETUP.ru.md](IDE_SETUP.ru.md) | Eclipse ALG install & toolchain |
| **[docs/SHAYDBG.md](docs/SHAYDBG.md)** / [docs/SHAYDBG.ru.md](docs/SHAYDBG.ru.md) | Step Debug wire protocol (SHAYDBG) |
| **[TODO.md](TODO.md)** | **Active roadmap** (bilingualism, C parity, IDE) |
| **[TODO_2026.md](TODO_2026.md)** | Closed 2026 audit backlog |
| **[AUDIT.md](AUDIT.md)** | Historical prototype audit (closed) |
| **[LICENSE](LICENSE)** | **MIT** (SPDX) |
| **[VERSIONING.md](VERSIONING.md)** | Engine + plug-in bump checklist |

`Gemini_reference/` is a reference snapshot of a related project — not SCHOOLALGOL / ALG branding.

---

## What this project is

**SCHOOLALGOL** is the pipeline `Lexer → Parser → AST → SemanticAnalyzer → Interpreter | CTranspiler` for `.alg` files.

The language is an educational algorithmic dialect with **Russian and English** keyword synonyms (same `TokenType`; mix allowed in one file). Syntax is **not** classical ШАЯ (`таб`, `использовать`, `словарь`, `<>`, `нц для` / `loop for`, …).

The Eclipse plug-in `org.myau.shaya.ide` ships as **ALG**: `.alg` editor, Run / Check / Transpile / Step Debug, templates, perspective, toolchain preferences.

---

## Repository layout

| Path | Role |
|------|------|
| `main.py` | CLI: run, `--transpile`, `--check`, REPL, AST dump, SHAYDBG |
| `version.py` | Single engine version |
| `lexer.py`, `parser.py`, `ast_nodes.py` | Lex / parse / AST |
| `semantic_analyzer.py`, `types_model.py` | Static checks |
| `interpreter.py`, `alg_builtins.py` | Runtime & builtins |
| `c_transpiler.py` | C code generation |
| `builtin_names.py` | Builtin RU ↔ EN aliases |
| `module_loader.py` | `использовать` / `import` |
| `repl.py`, `ast_dump.py` | REPL and `--dump-ast` |
| `shay_debug_protocol.py` | SHAYDBG (`--debug-protocol`) |
| `launcher.py` | Full cycle for `program.alg` (interpret → C → GCC → exe) |
| `test_*.py`, `pytest.ini` | Tests (`Gemini_reference/` excluded) |
| `examples/`, `examples/en/` | Lessons (RU and EN) |
| `org.myau.shaya.ide/` | Eclipse ALG sources |
| `install_dropins.ps1` | Sync engine + optional JAR/examples into Eclipse dropins |

---

## Language (engine 1.2.1)

Details: **[GRAMMAR.md](GRAMMAR.md)** (EN) / **[GRAMMAR.ru.md](GRAMMAR.ru.md)** (RU).

### Overview

- **Entry point:** parameterless procedure `основнаяпрограмма` or `mainprogram` (case-insensitive).
- **Comments:** lines starting with `|`.
- **Bilingual keywords/builtins:** one token type, two spellings — see GRAMMAR tables.
- **Modules:** `использовать "file.alg"` / `import "…"`. Path relative to the current file; no sandbox; cyclic import errors include the chain.
- **Semantics:** `SemanticAnalyzer` before run/transpile. Warnings (`AssignTypeWarning`, …); `--warnings-as-errors` → exit code 3.

### Types

| Type | Meaning | Notes |
|------|---------|--------|
| `цел` / `int` | integer | interpreter arithmetic via float; fractional assign warns |
| `вещ` / `real` | real | |
| `лит` / `str` | string | escapes: `\n` `\t` `\r` `\"` `\\` |
| `лог` / `bool` | boolean | `да`/`нет`, `true`/`false` |
| `таб` / `tab` | array `name[lo:hi]` | arbitrary lower bound; C uses offset |
| `файл` / `file` | file | `открыть`/`open`, … |
| `словарь` / `dict` | string → number | C values are `double` only |
| `запись` / `rec` | record | fields via `.` |
| `переч` / `enum` | enumeration | |

### Control flow

- Assignment `:=`; `вывод`/`output`, `ввод`/`input` (incl. files); format `output x:width:prec`.
- `если`… / `if`…; `нц пока`… / `loop while`…; `нц для`…`[шаг]` / `loop for`…`[step]` (auto ±1 if step omitted).
- `выход`/`break`, `продолжить`/`continue` (loops only); `возврат`/`return` [expr].
- `алг`/`proc` with `арг`/`arg`, `рез`/`res`.

### Builtins (RU / EN)

`открыть`/`open`, `закрыть`/`close`, `конецфайла`/`eof`, `корень`/`sqrt`, `модуль`/`abs`, `случ`/`rand`, `случцел`/`randint`, `длина`/`len`, `подстрока`/`substr`, `вверх`/`upper`, `вниз`/`lower`, `вцел`/`toint`, `ввещ`/`toreal`, `встроку`/`tostr`, `остаток`/`mod`, `целдел`/`div`, `степень`/`pow`, `мин`/`min`, `макс`/`max`, `округление`/`round`, `знак`/`sign`, `син`/`sin`, `кос`/`cos`, `найти`/`find`, `размер`/`size`.

File modes: `чтение`/`read`, `запись`/`write`, `дозапись`/`append`.

### Interpreter and C

| Mode | Command | Result |
|------|---------|--------|
| Run | `python main.py file.alg` or `--run` | execute in Python |
| Transpile | `python main.py file.alg --transpile` | write `file.c` |
| Check | `python main.py file.alg --check` | lex + parse + semantics |

C backend: `FILE*`, records/enums, dicts, forward prototypes, array params `(T*, len, offset)`, `--keep-cyrillic`, `--permissive`.

Output: integers without `.0`; booleans as **да** / **нет** (including `лог` function results).

**Known interpreter ↔ C gaps:** PRNGs (`случ`/`случцел`) differ (no shared seed); dict values are `double` only in C. `длина(number)` / `len(number)` is an error in both. See GRAMMAR / [TODO.md](TODO.md) epic B.

### CLI flags

| Flag | Purpose |
|------|---------|
| `--run` | Explicit run (default) |
| `--verbose` / `--trace` | Pipeline / statement tracing |
| `--dump-ast` [`--dump-ast-format text\|json`] | AST dump |
| `--repl` [`--lang ru\|en`] | REPL |
| `--repl-persist` | REPL with persistent variables across fragments |
| `--lang ru\|en` | UI language (help, error wrappers; also env `ALG_LANG`); default `ru` |
| `--debug-protocol` / `--break N` | SHAYDBG ([spec](docs/SHAYDBG.md)) |
| `--warnings-as-errors` | Warnings → exit 3 |
| `--keep-cyrillic` / `--permissive` | With `--transpile` |
| `--version` / `--help` | Version / help |

---

## Eclipse ALG plug-in

Plug-in **`org.myau.shaya.ide` 0.6.11** — IDE for `.alg` on the SCHOOLALGOL engine. UI brand **ALG** (Java package name unchanged). Bilingual UI via Eclipse NLS (`messages.properties` / `messages_ru.properties`).

Full install: **[IDE_SETUP.md](IDE_SETUP.md)**.

### Features

- Editor: highlighting, content assist, templates (RU + EN).
- **ALG → Run** (Ctrl+Alt+R), **Check** (Ctrl+Alt+C), **Transpile** (Ctrl+Alt+T), **Step Debug** (Ctrl+Alt+Shift+D), **Run Last** (Ctrl+Alt+L).
- ALG Project / Hello wizards (`Hello.alg` + `Hello_en.alg`).
- Perspective **ALG**, Problems markers, console hyperlinks.
- Welcome; Track / Grammar actions; Preferences → ALG (toolchain, Python, Validate…).

### Install (short)

```powershell
cd F:\proj\SCHOOLALGOL
.\install_dropins.ps1
.\install_dropins.ps1 -PluginJar
.\install_dropins.ps1 -Examples
```

Restart Eclipse. Keep only `org.myau.shaya.ide_0.6.11.jar` in dropins (remove older jars after closing Eclipse if locked).

---

## Quick start

```bash
python main.py examples/en/01_hello.alg
python main.py program.alg --check
python main.py program.alg --transpile
python main.py --repl --lang en
python main.py --repl-persist --lang en
python main.py --version
python launcher.py   # program.alg → interpret + C + gcc + exe
```

Requires **Python 3.7+** (stdlib only). Optional **GCC** for `.c` builds.

---

## Examples

| Path | Topic |
|------|--------|
| `examples/01_hello.alg` … `08_control_flow.alg` … | RU lessons |
| `examples/en/*.alg` | Same topics, English keywords |
| `examples/track/README.md` / `README.ru.md` | Teaching track index |
| `program.alg` + `utils.alg` | Demo + module |

---

## Testing

```bash
pip install -r requirements-dev.txt   # pytest
python -m pytest -q
```

GCC-backed cases skip when `gcc` is missing. CI: [`.github/workflows/ci.yml`](.github/workflows/ci.yml) (Windows + Ubuntu).

| File | Focus |
|------|--------|
| `test_basic.py` | core + GCC |
| `test_bilingual.py` | RU/EN synonyms |
| `test_audit_2026.py` / `test_backlog_2026.py` / `test_modules_arrays_2026.py` | 2026 audit & backlog |

---

## License

**MIT** — see [LICENSE](LICENSE). Version bumps: [VERSIONING.md](VERSIONING.md).

---

## Notes

- Paths in `открыть` / `использовать` are **not** sandboxed.
- Active work: **[TODO.md](TODO.md)**. Closed audit: [TODO_2026.md](TODO_2026.md).
- After updating the plug-in JAR: close Eclipse, then remove locked old `org.myau.shaya.ide_*.jar` from dropins (or re-run `install_dropins.ps1 -PluginJar`).
