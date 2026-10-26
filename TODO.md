# SCHOOLALGOL — active roadmap

**Status:** Epics A–G done (baseline engine **1.2.1**, plugin **0.6.11**). Roadmap complete unless new work is requested.  
**Baseline:** engine **1.2.1**, Eclipse plugin **0.6.11**  
**Previous (closed):** [TODO_2026.md](TODO_2026.md)  
**Docs policy:** git-facing docs default to **English**; Russian mirrors use `*.ru.md` (or `docs/ru/`). Language `.alg` stays fully bilingual (RU ↔ EN synonyms).  
**License:** [LICENSE](LICENSE) (MIT). Version bumps: [VERSIONING.md](VERSIONING.md).

---

## Goal

Make SCHOOLALGOL usable end-to-end in **Russian and English**: language, CLI messages, Eclipse UI, documentation, examples, and diagnostics — without breaking existing RU programs.

---

## Priority legend

| Tag | Meaning |
|-----|---------|
| **P0** | Blocks bilingual / school use or leaves broken dropins |
| **P1** | Parity / quality for teaching |
| **P2** | IDE & debugger depth |
| **P3** | Nice-to-have / polish |

Acceptance for each item: checkbox + tests and/or doc update listed in the item.

---

## Epic A — Bilingualism (language + product) **P0**

### A1. Documentation pair (EN default)

- [x] **A1.1** Root [README.md](README.md) is **English** (git default). *(done 2026-10-24)*
- [x] **A1.2** Russian mirror [README.ru.md](README.ru.md) kept in sync (same sections/versions). *(done 2026-10-24)*
- [x] **A1.3** [GRAMMAR.md](GRAMMAR.md) в†' English canonical; add [GRAMMAR.ru.md](GRAMMAR.ru.md).
- [x] **A1.4** [IDE_SETUP.md](IDE_SETUP.md) в†' English; add `IDE_SETUP.ru.md`.
- [x] **A1.5** [docs/SHAYDBG.md](docs/SHAYDBG.md) в†' English; add `docs/SHAYDBG.ru.md`.
- [x] **A1.6** [examples/track/README.md](examples/track/README.md) + [README.ru.md](examples/track/README.ru.md).
- [x] **A1.7** Cross-links EN↔RU on main docs; [TODO_2026.md](TODO_2026.md) / [AUDIT.md](AUDIT.md) point to [TODO.md](TODO.md).
- [x] **A1.8** `install_dropins.ps1` copies `GRAMMAR.md` + `GRAMMAR.ru.md` into toolchain `docs/`.

**Done when:** a new contributor opens only `README.md` and can install/run in English; a RU teacher uses `README.ru.md` / `GRAMMAR.ru.md` without English.

### A2. Language surface completeness

Already strong (keywords + builtins RU/EN). Close gaps:

- [x] **A2.1** Audit `lang_tokens.py` / `builtin_names.py`: RU canonical builtins (incl. `СЃРёРЅ`/`РєРѕСЃ`); aliases resolve; covered in `test_i18n_2026.py`.
- [x] **A2.2** New keywords from 1.2.x covered in `test_bilingual.py`: `break`/`continue`/`return`/`step` (+ examples `08_control_flow`).
- [x] **A2.3** Bool I/O: print **да/нет**; input accepts `да`/`нет`/`true`/`false`/… (interpreter + GRAMMAR).
- [x] **A2.4** File modes `чтение|запись|дозапись` ↔ `read|write|append` — tests both sides.
- [x] **A2.5** Mixing RU/EN in one file allowed — documented in GRAMMAR EN+RU.

### A3. Engine diagnostics (CLI / errors / warnings)

Today messages are largely Russian (`errors.py`, `semantic_analyzer.py`, warnings).

- [x] **A3.1** Message catalog in `i18n.py` (`t(key)` + RU/EN tables).
- [x] **A3.2** CLI `--lang ru|en` + env `ALG_LANG` / `LANG` detect; **default `ru`** (compat); documented in README/GRAMMAR.
- [x] **A3.3** Error wrappers + high-frequency semantic bodies via `sem()` / `sem_*` keys (analyzer + interpreter + `alg_builtins`: undefined, redeclare, div-zero, index/dict, arity, file open, num-only, …).
- [x] **A3.4** `--help` / usage language-selected.
- [x] **A3.5** REPL prompts already respect `--lang` (pre-existing).
- [x] **A3.6** Tests in `test_i18n_2026.py` (help EN/RU, Semantic error prefix EN).

### A4. Eclipse ALG UI localization **P0/P1**

Eclipse NLS + `plugin.properties` (locale-aware UI).

- [x] **A4.1** Eclipse NLS: `messages.properties` (EN default) + `messages_ru.properties` + `Messages.java`.
- [x] **A4.2** Externalized: Welcome, About, Shortcuts, Grammar/Track, markers tips, toolchain, refuse-CLI-Debug.
- [x] **A4.3** Preferences → ALG: NLS labels; Validate treats `ERROR` / `ОШИБКА`.
- [x] **A4.4** `plugin.properties` / `plugin_ru.properties` + `%keys` in `plugin.xml`; `Bundle-Localization: plugin`.
- [x] **A4.5** Open Grammar / Track by workbench locale (`GRAMMAR.ru.md` / `README.ru.md` with fallback) — `ShayaDocs.java`.
- [x] **A4.6** Plugin **0.6.9** built; `install_dropins.ps1` `$PluginVer` updated.

**Done when:** Eclipse UI in `en_US` shows English; in `ru` shows Russian; no hardcoded-only RU tips in Problems.

### A5. Examples & teaching track

- [x] **A5.1** Control-flow lesson twins: `08_control_flow.alg` + `en/08_control_flow.alg` (audit remaining examples as needed).
- [x] **A5.2** Lessons (RU+EN): `step` / `break` / `continue` / `return` — `08_control_flow.alg`.
- [x] **A5.3** Track README lists lesson 8; Import Track picks up files via `-Examples`.
- [x] **A5.4** `ShayaKeywords` includes `continue`/`step`/`break`/`return` (+ RU).

---

## Epic B — Interpreter ↔ C parity **P1**

- [x] **B1** String heap: `alg_str_concat_owned` for nested `+`; `alg_strlen_free` for `длина`/`размер` heap args; remaining leaks documented in GRAMMAR.
- [x] **B2** `alg_dict_free` in C runtime + auto free at proc/func/main exit (and before early `return`); values remain `double` only.
- [x] **B3** Record array fields: allocate in `RecordInstance`; C `T field[N]` + offsets via `rec.field` key.
- [x] **B4** `лит` assign to `record.field` in C: `strdup`/`free` like plain `Var` (tests in `test_backlog_2026.py`).
- [x] **B5** `длина(число)` / `len(number)` → semantic + runtime error in both (needs string / array / dict).
- [x] **B6** `случ` / `случцел`: documented as **permanent** interpreter↔C non-parity (no shared seed).
- [x] **B7** Tests: GCC parity for B3–B5 in `test_backlog_2026.py`.

---

## Epic C — Language / runtime gaps **P1–P2**

- [x] **C1** Multi-dimensional arrays — explicitly rejected in parser + GRAMMAR (use 1D or record-of-arrays).
- [x] **C2** REPL: `--repl-persist` keeps main locals across fragments (`.vars` / `.reset`); default REPL still accumulates buffer.
- [x] **C3** Nested `break`/`continue`: nearest loop only — examples `08_control_flow` + tests.
- [x] **C4** Dropins hygiene: document "close Eclipse → remove old JARs"; `install_dropins.ps1` warns if multiple `org.myau.shaya.ide_*.jar` remain.

---

## Epic D — IDE features **P2**

- [x] **D1** **ALG → Transpile** (`main.py --transpile`, reveal `.c` / console; Ctrl+Alt+T) — plugin **0.6.11**.
- [x] **D2** Rename / Find References: identifiers only (skip keywords/strings); limits in IDE_SETUP.
- [x] **D3** Dead **CLI Debug** command/handler removed (use Step Debug).

---

## Epic E — SHAYDBG **P2**

- [x] **E1** `arrays` / `records` filled in `stopped` (and `vars`); scalars stay in `globals`/`locals`.
- [x] **E2** `eval`: parser `logical_or_expr` (binops, member, index) — limits in SHAYDBG.md.
- [x] **E3** Breakpoint `enabled: false` honored (`extract_break_lines` / pause handler); condition/hitCount still non-goal.
- [x] **E4** Stdin `vars` в†' `shay=vars` snapshot while paused.

---

## Epic F — Infrastructure **P2–P3**

- [x] **F1** Root `LICENSE` — **MIT**; linked from README EN/RU.
- [x] **F2** `build_plugin.ps1` wipes `org.myau.shaya.ide/build/**` and removes stale `org.myau.shaya.ide_*.jar`; `.gitignore` ignores build outputs.
- [x] **F3** CI: `.github/workflows/ci.yml` — pytest on Windows/Ubuntu; GCC installed on Linux so parity tests can run.
- [x] **F4** Version bump policy: [VERSIONING.md](VERSIONING.md) (engine + plug-in + bilingual READMEs / IDE_SETUP).
- [x] **F5** Documented operator step: close Eclipse в†' remove locked old dropins JARs / re-run `install_dropins.ps1 -PluginJar` (README + install script warn).

---

## Epic G — Polish after A–F **P3**

- [x] **G1** Remaining interpreter / `alg_builtins` `SemanticError` bodies via `sem_*` (void operands, file I/O, for-step 0, convert/pow/eof, …).
- [x] **G2** `вывод id, …` / `output id, …`: if `id` is not **файл**, demote to multi-value console print (semantic analyzer); documented in GRAMMAR.
- [x] **G3** README EN/RU: refresh interpreter↔C gap list (`длина(number)` is error in both).

---

## Explicit non-goals (do not schedule unless requested)

- Port VS Code / network / host-API from `Gemini_reference/`
- Classical ШАЯ compatibility (`мас` instead of `таб`, etc.)
- DAP / remote / multi-thread debug
- Path sandbox for `открыть` / `import` (trust model stays teacher-responsible)
- Debugging transpiled C via SHAYDBG

---

## Suggested implementation order

1. **A1.1–A1.2** — EN `README.md` + `README.ru.md` (unblocks git-facing bilingual policy).  
2. **A1.3–A1.8** — grammar/setup/SHAYDBG pairs + dropins copy.  
3. **A2** + **A5** — language/tests/examples (fast teaching value).  
4. **A3** — engine `--lang` / message catalog.  
5. **A4** — Eclipse NLS + plugin bump.  
6. **B*** — C parity.  
7. **D/E/F** — IDE, debugger, infra.

---

## Progress log

| Date | Note |
|------|------|
| 2026-10-24 | Roadmap created from post-1.2.1 gap analysis; bilingual epic mandatory; README EN-default policy set. |
| 2026-10-24 | A1.1–A1.2: `README.md` (EN) + `README.ru.md` (RU). |
| 2026-10-24 | A1.3–A1.8 docs pairs + dropins grammar sync; A2.2/A5 control-flow examples + bilingual tests. |
| 2026-10-24 | A2.1–A2.5 + A3.1/2/4/5/6: `i18n.py`, bool input, file modes, sin/cos RU-canonical. |
| 2026-10-24 | A3.3 `sem_*` bodies; A4.1/2/5/6 Eclipse NLS + plugin **0.6.8**. |
| 2026-10-24 | A4.3–A4.4 prefs + plugin.xml NLS; plugin **0.6.9**; B2/B4 C parity (`alg_dict_free`, lit record fields). |
| 2026-10-24 | B1/B3/B5/B7 + C4: owned string concat, record array fields, `длина(число)` error, dropins multi-JAR warn. |
| 2026-10-24 | B6 + C1–C3: multi-dim reject, `--repl-persist`, nested break/continue docs/tests. |
| 2026-10-24 | D1–D3: ALG Transpile, rename/refs docs, remove CLI Debug; plugin **0.6.11**. |
| 2026-10-24 | E1–E4: SHAYDBG arrays/records, eval subset, enabled BP, `vars` event. |
| 2026-10-24 | F1–F5: MIT LICENSE, build cleanup, CI, VERSIONING.md, dropins JAR hygiene docs. |
| 2026-10-24 | A3.3/B2 leftovers: interp+builtins `sem_*`; C auto `alg_dict_free` at scope exit. |
| 2026-10-24 | Epic G: full interp/builtins `sem_*`; print/file demote; README gap list. |
| 2026-10-24 | Plugin **0.6.11**: redraw toolbar icons; distinct `transpile.png` (was same as Check). |
