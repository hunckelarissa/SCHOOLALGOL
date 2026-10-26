# ALG IDE — Eclipse plug-in setup

Operational guide. Overview: **[README.md](README.md)** (EN) / **[README.ru.md](README.ru.md)** (RU); grammar: **[GRAMMAR.md](GRAMMAR.md)** / **[GRAMMAR.ru.md](GRAMMAR.ru.md)**; Step Debug: **[docs/SHAYDBG.md](docs/SHAYDBG.md)**; roadmap: **[TODO.md](TODO.md)**.  
**Russian setup guide:** [IDE_SETUP.ru.md](IDE_SETUP.ru.md).

| | |
|--|--|
| Plug-in | `org.myau.shaya.ide` **0.6.11** (`META-INF/MANIFEST.MF`) |
| Sources | `org.myau.shaya.ide/` in the repo |
| Engine | SCHOOLALGOL **1.2.1** — `.alg` → `main.py` (RU + EN) |
| UI brand | **ALG** (menu, perspective, Preferences). Java package `org.myau.shaya.ide` unchanged |

---

## Toolchain layout in dropins

Typical path (adjust for your Eclipse):

```
…\eclipse\dropins\
  org.myau.shaya.ide_0.6.11.jar
  schoolalgol-shaya\
    tools\shaya-run.bat
    interpreters\SchoolAlgol\main.py   (+ lexer.py, parser.py, …)
    examples\                          (optional: install_dropins.ps1 -Examples)
    docs\GRAMMAR.md                    (EN; synced from repo)
    docs\GRAMMAR.ru.md                 (RU; synced if present)
```

The plug-in auto-discovers `schoolalgol-shaya`. If not:

**Window → Preferences → ALG → Toolchain home**  
= full path to the `schoolalgol-shaya` folder

**Validate…** should report OK for home, bat, `SchoolAlgol/main.py`, and Python.

Other Preferences → ALG fields:

| Field | Meaning |
|-------|---------|
| Extra args | Extra args for `shaya-run.bat` / launch |
| Python | Path to `python.exe`; empty = PATH / `py -3` |
| Indent width | 2 or 4 |
| Insert spaces for tabs | spaces instead of tab |
| Check on save | validate `.alg` on save |

---

## Installing the JAR (normal Eclipse)

Built bundle:

`…\eclipse\dropins\org.myau.shaya.ide_0.6.11.jar`

After copying/updating the JAR **restart Eclipse** (otherwise OSGi may keep the old bundle).

- **dropins JAR** — daily use without PDE.
- **PDE "Run As → Eclipse Application"** — develop from sources in a runtime workbench.

Remove old `org.myau.shaya.ide_0.6.1.jar` … `0.6.8.jar`, keep only **0.6.11**. If a file is locked, **close Eclipse** and delete it manually. `install_dropins.ps1` warns if several `org.myau.shaya.ide_*.jar` remain in dropins. UI strings follow the workbench locale (EN default + `messages_ru.properties` / `plugin_ru.properties`).

A JAR with another Bundle-SymbolicName (`org.shaya.ide_*.jar`) does not conflict with `org.myau.shaya.ide`.

---

## Syncing the toolchain: `install_dropins.ps1`

After changing `*.py` / `tools/shaya-run.bat` in the repo:

```powershell
cd F:\proj\SCHOOLALGOL
.\install_dropins.ps1
```

The script:

- finds `dropins` (`-EclipseDropins` or common paths under `%USERPROFILE%\eclipse`);
- copies `*.py` → `schoolalgol-shaya\interpreters\SchoolAlgol\`;
- copies `tools\shaya-run.bat` → `schoolalgol-shaya\tools\`;
- copies `GRAMMAR.md` and `GRAMMAR.ru.md` (if present) → `schoolalgol-shaya\docs\`.

Options:

```powershell
.\install_dropins.ps1 -PluginJar          # plug-in JAR 0.6.11 + remove older 0.6.1–0.6.8
.\install_dropins.ps1 -Examples           # examples/ including track/
.\install_dropins.ps1 -EclipseDropins "D:\path\to\eclipse\dropins"
```

When updating only the JAR, you can skip re-syncing Python (or run without `-PluginJar` for `.py`/bat only). Do not put `org.myau.shaya.ide.zip` into the toolchain.

First run: **Welcome** dialog (re-enable in Preferences → ALG). Debugging is **Step Debug** only.

---

## PDE import (development)

1. Eclipse IDE for Java with PDE (e.g. `java-2022-12`).
2. **File → Import → Existing Projects into Workspace** → `org.myau.shaya.ide`.
3. Target Platform: Eclipse SDK / RCP.
4. Right-click project → **Run As → Eclipse Application** (or Debug As).
5. In the new workbench: **Window → Perspective → Open Perspective → ALG**.

---

## Running `.alg` programs

1. **File → New → Project → ALG Project** (Hello RU + EN) or open your `.alg`.
2. **ALG → Run** — Ctrl+Alt+R.
3. **ALG → Check** — Ctrl+Alt+C (`main.py --check`).
4. **ALG → Transpile** — Ctrl+Alt+T (`main.py --transpile`; opens sibling `.c` in the editor when possible).
5. **ALG → Run Last** — Ctrl+Alt+L.
6. Breakpoint (double-click ruler) → **ALG → Step Debug** — Ctrl+Alt+Shift+D (`main.py --debug-protocol`, SHAYDBG).

Highlighting and Ctrl+Space know EN synonyms (`proc`, `begin`, `int`, …) plus flow keywords (`break`/`continue`/`return`/`step`) and builtins. Line comments use `|`.

Console: interpreter output; hyperlinks to `file:line` / "(line N)".

### Useful editor commands

| Action | Typical binding |
|--------|-----------------|
| Toggle Comment | Ctrl+/ |
| Go to Matching Block | Ctrl+Shift+P |
| Quick Outline | Ctrl+O |
| Go to Declaration | F3 |
| Find References | Ctrl+Shift+G |
| Rename… | Alt+Shift+R |
| Reindent | Ctrl+Shift+F |

**Rename / Find References limits:** whole-word identifiers only; **keywords and builtins are refused**; text inside `|` comments and `"…"` / `'…'` strings is skipped. Not a full semantic rename (no scope analysis). Exact list: **ALG → Keyboard Shortcuts…** / About.

---

## Relation to the engine CLI

The plug-in calls the same `main.py` as the command line:

- Run → interpret;
- Check → `--check`;
- Transpile → `--transpile` (writes `program.c` next to the `.alg`);
- Step Debug → `--debug-protocol` (+ breakpoints as `--break`); wire protocol — **[docs/SHAYDBG.md](docs/SHAYDBG.md)**.

From a host shell: `--verbose`, `--trace`, `--repl --lang en` — see README. Legacy **CLI Debug** was removed from the plug-in (use **Step Debug**).
