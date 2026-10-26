# Grammar and semantics of `.alg`

Description of **School Algol** (`.alg` files) for SCHOOLALGOL engine **1.2.1**.  
Overview: [README.md](README.md) (EN) / [README.ru.md](README.ru.md) (RU).  
**Russian grammar:** [GRAMMAR.ru.md](GRAMMAR.ru.md).

The language is standalone (not classical ШАЯ): `таб`/`tab`, `использовать`/`import`, `словарь`/`dict`, `запись`/`rec`, `переч`/`enum`, operators `<>` / `>=` / `<=` are part of the `.alg` dialect.

## Pipeline and diagnostics

Semantic analysis runs before execution and transpilation.

| Flag | Effect |
|------|--------|
| `--verbose` | stderr: stages (lexer → parser → semantics → …) and RU/EN token labels |
| `--trace` | Statement-by-statement tracing |
| `--warnings-as-errors` | Warnings → exit code 3 |
| `--dump-ast` / `--dump-ast-format text\|json` | Parse tree |
| `--repl` / `--repl --lang en` | Interactive mode (buffer accumulates; each line re-runs the buffer) |
| `--repl-persist` | REPL with **persistent bindings**: after a successful fragment, the buffer clears but variables in `main` remain (`.vars`, `.reset` clears session) |
| `--lang ru\|en` | UI language for help/error wrappers (also `ALG_LANG`); default `ru` |
| `--run` | Explicit run (default mode) |
| `--transpile` + `--keep-cyrillic` / `--permissive` | C generation |
| `--debug-protocol` / `--break N` | SHAYDBG for Eclipse Step Debug |

## Entry point

- Parameterless procedure named **основнаяпрограмма** or **mainprogram**.
- Names are case-insensitive (`MainProgram` = `mainprogram`).

## Bilingual keywords (RU + EN)

Russian and English forms are **synonyms of one token**. The parser matches `TokenType`, not “file language”. Mixing in one file is allowed (`if` + `то` + `endif`).

| RU | EN | RU | EN |
|----|-----|----|-----|
| алг | proc | цел | int |
| нач | begin | вещ | real |
| кон | end | лог | bool |
| арг | arg | лит | str |
| рез | res | таб | tab |
| конст | const | файл | file |
| использовать | import | словарь | dict |
| ввод | input | запись | rec |
| вывод | output | переч | enum |
| если | if | да | true |
| то | then | нет | false |
| иначе | else | и | and |
| все | endif | или | or |
| нц | loop | не | not |
| кц | eloop | | |
| для | for | | |
| пока | while | | |
| от | from | | |
| до | to | | |
| выход | break | | |
| продолжить | continue | | |
| возврат | return | | |
| шаг | step | | |

Example (EN):

```alg
proc mainprogram
begin
  int x
  x := 1
  if x > 0 then
    output "ok"
  endif
end
```

See `examples/en/`.

## Modules

- **использовать** / **import** `"file.alg"` — path relative to the current file’s directory.
- `..` and absolute paths are allowed; **no sandbox**.
- Cyclic import → error with the file chain.

## Declarations

- **конст** / **const** *name* = *expression*.
- Variable types: **цел**/**вещ**/**лит**/**лог**/**файл**/**словарь** (and EN synonyms), user record/enum types.
- Array: **таб** *type* *name*[*lo*:*hi*] — **one-dimensional only**; arbitrary lower bound; C uses an offset.
  - **Not supported:** `таб цел a[1:n, 1:m]` or `a[1:n][1:m]` — parser error. Use a flat 1D array or a record of arrays.
- **алг** / **proc** *name* [ ( **арг** … ; **рез** … ) ] [ decls ] **нач** body **кон** — procedure or function (with **рез**). Before **нач** — declarations only (Pascal-style); after **нач**, decls and statements may interleave.
- **запись** / **rec** *name* **нач** fields **кон**.
- **переч** / **enum** *name* ( *member1* , … ).

## Statements

- *lvalue* **:=** *expression* — assignment (variable, array element, record field, dict key).
- **вывод** / **output** [ *file* , ] *expression* … [ : *width* [ : *precision* ] ].
  - Ambiguity: `output id, …` looks like file I/O; if `id` is not type **файл**/**file**, it is treated as the first console expression (so `вывод i, "*", j` prints three values).
- **ввод** / **input** [ *file* , ] *variable* ….
  - For **лог** / **bool**: accepts `да`/`нет`/`true`/`false`/`истина`/`ложь`/`1`/`0` (prints as **да**/**нет**).
  - On file EOF: numeric → `0.0`, **лог** → `нет`, **лит** → `""` (language contract).
  - Prefer `конецфайла(f)` / `eof(f)` before reading.
- **если** … **то** … [ **иначе** … ] **все** / **if** … **then** … [ **else** … ] **endif**.
- **нц пока** … **кц** / **loop while** … **eloop**.
- **нц для** *var* **от** *a* **до** *b* [ **шаг** *s* ] … **кц** / **loop for** … **from** … **to** … [ **step** *s* ] **eloop** (inclusive). Without **step**: direction `+1` or `−1` is chosen automatically (`from 5 to 1` goes down). Step `0` is an error.
- **выход** / **break** — leave the **nearest** enclosing loop only (no labeled break). Outside a loop — semantic error. C → `break;`. Nested example: `examples/08_control_flow.alg`.
- **продолжить** / **continue** — next iteration of the **nearest** enclosing loop only. Outside a loop — semantic error. C → `continue;`.
- **возврат** / **return** [ *expression* ] — leave a procedure/function. With an expression — only in a function (`алг … рез`); value is stored in the result variable. C → `return`.
- Call: *name* ( *args* ). A procedure (no **рез**) cannot appear in an expression — `--check` error.

### `for` loop and implicit declaration

If the loop variable is undeclared, the interpreter may create it as **цел** and emit `ImplicitDeclareWarning`. Prefer an explicit `цел i` / `int i`.

## Expressions

- Literals: numbers, strings `"…"`, **да**/**нет** (**true**/**false**).
- Access: *expr*.*field*, *expr*[*index*].
- Unary: **не** / **not**, `-`, `+`.
- Binary (left-associative within a group):
  - arithmetic: `+` `-` `*` `/`
  - comparison: `=` `<>` `>` `<` `>=` `<=`
  - logic: **и**/**или** (**and**/**or**)
- String concatenation via `+` (C — `str_concat`).

### String escapes

| Sequence | Character |
|----------|-----------|
| `\n` | newline |
| `\t` | tab |
| `\r` | carriage return |
| `\"` | quote |
| `\\` | backslash |

### Comparisons → C

| `.alg` | C |
|--------|---|
| `=` | `==` |
| `<>` | `!=` |
| `>` `<` `>=` `<=` | same |

## Builtins

| RU | EN | Purpose |
|----|-----|---------|
| открыть | open | open file (path, mode) |
| закрыть | close | close |
| конецфайла | eof | end of file? |
| корень | sqrt | √ |
| модуль | abs | \|x\| |
| случ | rand | random [0,1) |
| случцел | randint | random integer in range |
| длина | len | length |
| подстрока | substr | substring |
| вверх / вниз | upper / lower | case |
| вцел / ввещ / встроку | toint / toreal / tostr | conversions |
| остаток | mod | remainder `mod(a, b)` |
| целдел | div | integer division |
| степень | pow | `pow(a, b)` = aᵇ |
| мин / макс | min / max | min / max of two numbers |
| округление | round | round to integer |
| знак | sign | −1, 0, or 1 |
| син | sin | trigonometry (radians) |
| кос | cos | trigonometry (radians) |
| найти | find | substring position (1-based), 0 if missing |
| размер | size | array element count (string → length); for `arg tab …` in C, pointer, length, and offset are passed |

**File modes:** `чтение`/`read` → `r`, `запись`/`write` → `w`, `дозапись`/`append` → `a`.

Paths in `open` go to the OS **as-is** (no whitelist).

All listed builtins transpile to C (see limits below).

### C generation (parity 1.2.1)

- **Forward prototypes** (`/* Forward declarations */`) before bodies — mutual recursion and call-before-declare compile with GCC.
- Strings: compare with `strcmp`; `лит` assign uses `strdup` / `free`.
- Undeclared `for` loop variable becomes `int` in C when needed.
- Array parameters: `(T* a, int a_len, int a_off)`; `size(a)` uses `a_len`.
- Boolean output — strings «да»/«нет» (including `рез лог` function results).
- `лит` fields of records: assign uses `strdup` / `free` like plain string variables.
- Record **array** fields (`таб` inside `запись`): fixed literal bounds → C `T field[N]` with correct index offset; interpreter allocates the array on record create.
- Nested string `+` uses `alg_str_concat_owned` so intermediate heap values are freed; `длина`/`len` on a heap string frees the argument (`alg_strlen_free`). Remaining `MemoryLeakWarning` cases: const init, dict values, some call args (`подстрока`/`вверх`/…).
- Local `словарь` / `dict` variables get `alg_dict_free` at C scope exit (main / procedure / function) and before early `return`.

## Types (summary)

| `.alg` | Semantics | In C |
|--------|-----------|------|
| цел | integer | `int` |
| вещ | real | `double` |
| лит | string | `char*` (heap) |
| лог | boolean | `bool` |
| таб *type*[lo:hi] | array | array + offset |
| файл | handle | `FILE*` |
| словарь | string key → number | `AlgDict` (values `double`; runtime has `alg_dict_free`) |
| запись / переч | user types | `struct` / `enum` + MemberAccess |

### Numeric model (interpreter)

- Arithmetic via Python `float`.
- Division `/` is always real (`5 / 2` → `2.5`).
- Assigning a fraction to `цел` without `вцел` → `AssignTypeWarning`.
- Integers print without a fractional part (`6`, not `6.0`) — same as C (`num_to_str`); applies to `output`, string `+`, and `tostr`.
- Booleans print as **да** / **нет** (interpreter and C; including `лог` function results).
- Windows CRLF sources parse like LF.
- String `input` (`лит`) reads a full line (C — `fgets`, not `scanf %s`).

## File I/O in C

`файл` → `FILE*`; `open`/`close` → `fopen`/`fclose`; output/input — `fprintf` / `fscanf` / `fgets`. Mode strings as above. Paths are not filtered.

## Interpreter vs C (limits 1.2.1)

| Topic | Interpreter | C |
|-------|-------------|---|
| `длина(number)` / `len(number)` | **error** (needs string / array / dict) | **error** (same; C expects a string) |
| String `=` `<>` `<` `>` | by value | `strcmp` |
| `случ` / `случцел` | Python PRNG | different C `rand` — **permanent non-parity** (no shared seed API) |
| dict | Python numbers | `double` only |
| `--keep-cyrillic` | — | Cyrillic in C identifiers |
| `--permissive` | — | unknown nodes → warning, not hard error |
| String/heap leaks | Python GC | possible `MemoryLeakWarning` |

Network / host-API / VS Code packaging from `Gemini_reference` are not part of SCHOOLALGOL.

## Comments

Line comment: **`|`** to end of line. ALG plug-in Toggle Comment uses this style.

## Differences from classical ШАЯ (intentional)

| Topic | Typical ШАЯ | School Algol `.alg` |
|-------|-------------|---------------------|
| Array | often `мас` | `таб type name[lo:hi]` |
| Loops | various `для`/`пока` | `нц … кц` / `loop … eloop` |
| Modules | varies | `использовать` / `import` |
| Dict | usually none | `словарь` / `dict` |
| Inequality | various | `<>` |
| Comparisons | not always `>=`/`<=` | part of the language |
| Files | educational APIs | full OS path |
| Environment | — | interpreter + C + Eclipse ALG |

*Matches engine 1.2.1. When extending the language, update this file, [GRAMMAR.ru.md](GRAMMAR.ru.md), and version tables in README.*
