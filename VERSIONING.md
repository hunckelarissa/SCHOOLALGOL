# Version bump policy

Keep **engine**, **plug-in**, and **docs** in sync on the same change day when either product version moves.

| Artifact | Canonical field | Also update |
|----------|-----------------|-------------|
| Engine | `version.py` → `__version__` | `README.md` / `README.ru.md` version table; mention in `GRAMMAR.md` header if the release notes a language change |
| Eclipse ALG plug-in | `org.myau.shaya.ide/build_plugin.ps1` → `$Ver` | `META-INF/MANIFEST.MF` `Bundle-Version` (script rewrites it), `install_dropins.ps1` → `$PluginVer`, README tables (EN+RU), `IDE_SETUP.md` / `IDE_SETUP.ru.md` JAR names, old-JAR purge list in `install_dropins.ps1` |

## Rules

1. **Same day:** if you bump engine or plug-in, update both language READMEs and IDE_SETUP pairs before merging.
2. **Plug-in build:** run `.\org.myau.shaya.ide\build_plugin.ps1` — do not hand-edit `build/**` (ignored; regenerated).
3. **Dropins:** `.\install_dropins.ps1 -PluginJar` after build; close Eclipse if an old JAR is locked (**F5**).
4. **SPDX license:** root [`LICENSE`](LICENSE) is **MIT**; do not change SPDX without an explicit project decision.
5. **Engine vs plug-in:** versions are independent (`1.2.x` engine, `0.6.x` plug-in). Bump plug-in for IDE-only changes; bump engine for language/runtime/CLI changes.

## Quick checklist

- [ ] `version.py` and/or `build_plugin.ps1` `$Ver`
- [ ] `install_dropins.ps1` `$PluginVer` (+ old JAR names if plug-in)
- [ ] README.md + README.ru.md tables
- [ ] IDE_SETUP.md + IDE_SETUP.ru.md JAR / version strings
- [ ] Build JAR + optional `-PluginJar`
