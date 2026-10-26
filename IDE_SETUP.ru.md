# ALG IDE — установка плагина Eclipse

Операционная инструкция. Обзор — **[README.md](README.md)** (EN) / **[README.ru.md](README.ru.md)** (RU); грамматика — **[GRAMMAR.md](GRAMMAR.md)** / **[GRAMMAR.ru.md](GRAMMAR.ru.md)**; Step Debug — **[docs/SHAYDBG.md](docs/SHAYDBG.md)**; план — **[TODO.md](TODO.md)**.  
**English setup:** [IDE_SETUP.md](IDE_SETUP.md).

| | |
|--|--|
| Плагин | `org.myau.shaya.ide` **0.6.11** (`META-INF/MANIFEST.MF`) |
| Исходники | `F:\proj\SCHOOLALGOL\org.myau.shaya.ide` |
| Движок | SCHOOLALGOL **1.2.1** — только `.alg` → `main.py` (RU + EN) |
| Бренд UI | **ALG** (меню, перспектива, Preferences). Java-пакет `org.myau.shaya.ide` не переименовывался |

---

## Состав toolchain в dropins

Типичный путь (подставьте свой Eclipse):

```
…\eclipse\dropins\
  org.myau.shaya.ide_0.6.11.jar
  schoolalgol-shaya\
    tools\shaya-run.bat
    interpreters\SchoolAlgol\main.py   (+ lexer.py, parser.py, …)
    examples\                          (опционально: install_dropins.ps1 -Examples)
    docs\GRAMMAR.md                    (копируется из репозитория)
```

Плагин ищет `schoolalgol-shaya` автоматически. При сбое:

**Window в†' Preferences в†' ALG в†' Toolchain home**  
= полный путь к каталогу `schoolalgol-shaya`

Кнопка **Validate…** должна показать OK для home, bat, `SchoolAlgol/main.py` и Python.

Другие поля Preferences → ALG:

| Поле | Смысл |
|------|--------|
| Extra args | Доп. аргументы в `shaya-run.bat` / запуске |
| Python | Путь к `python.exe`; пусто = PATH / `py -3` |
| Indent width | 2 или 4 |
| Insert spaces for tabs | пробелы вместо таба |
| Check on save | проверка `.alg` при сохранении |

---

## Установка JAR (обычный Eclipse)

Собранный бандл:

`…\eclipse\dropins\org.myau.shaya.ide_0.6.11.jar`

После копирования/обновления JAR **обязательно перезапустите Eclipse** (иначе OSGi может не подхватить бандл).

- **dropins JAR** — повседневный запуск без PDE.
- **PDE «Run As → Eclipse Application»** — разработка из исходников в runtime workbench.

Удаляйте старые `org.myau.shaya.ide_0.6.1.jar` … `0.6.8.jar`, оставляя только **0.6.11**. Если файл занят — **закройте Eclipse** и удалите вручную. `install_dropins.ps1` предупреждает, если в dropins осталось несколько `org.myau.shaya.ide_*.jar`. Строки UI зависят от локали Eclipse (EN + `messages_ru.properties`).

JAR с другим Bundle-SymbolicName (`org.shaya.ide_*.jar`) не конфликтует с `org.myau.shaya.ide` — можно оставить.

---

## Синхронизация toolchain: `install_dropins.ps1`

После правок `*.py` / `tools/shaya-run.bat` в `F:\proj\SCHOOLALGOL`:

```powershell
cd F:\proj\SCHOOLALGOL
.\install_dropins.ps1
```

РЎРєСЂРёРїС':

- ищет `dropins` (параметр `-EclipseDropins` или типичные пути под `%USERPROFILE%\eclipse`);
- копирует `*.py` → `schoolalgol-shaya\interpreters\SchoolAlgol\`;
- копирует `tools\shaya-run.bat` → `schoolalgol-shaya\tools\` (нужен для Run/Check);
- копирует `GRAMMAR.md` → `schoolalgol-shaya\docs\` (меню «Грамматика…»);
- **не** обещает копировать несуществующие docs.

Опции:

```powershell
.\install_dropins.ps1 -PluginJar          # JAR плагина 0.6.11 + удаление старых 0.6.1–0.6.7
.\install_dropins.ps1 -Examples           # examples/ включая track/
.\install_dropins.ps1 -EclipseDropins "D:\path\to\eclipse\dropins"
```

При обновлении только JAR toolchain Python не трогайте (или снова запустите скрипт без `-PluginJar` только для `.py`/bat). Не кладите в toolchain архив `org.myau.shaya.ide.zip`.

Первый запуск: диалог **Welcome** (можно снова включить в Preferences → ALG). Отладка — только **Step Debug**.
---

## Импорт в PDE (разработка)

1. Eclipse IDE for Java с PDE (например `java-2022-12`).
2. **File в†' Import в†' Existing Projects into Workspace** в†' `F:\proj\SCHOOLALGOL\org.myau.shaya.ide`.
3. Target Platform: Eclipse SDK / RCP.
4. ПКМ по проекту → **Run As → Eclipse Application** (или Debug As).
5. Р' РЅРѕРІРѕРј workbench: **Window в†' Perspective в†' Open Perspective в†' ALG**.

---

## Запуск программ .alg

1. **File → New → Project → ALG Project** (создаст Hello RU + EN) или открыть свой `.alg`.
2. **ALG → Run** — Ctrl+Alt+R.
3. **ALG → Check** — Ctrl+Alt+C (`main.py --check`).
4. **ALG → Transpile** — Ctrl+Alt+T (`main.py --transpile`; при успехе открывает соседний `.c`).
5. **ALG → Run Last** — Ctrl+Alt+L.
6. Breakpoint (двойной клик по линейке) → **ALG → Step Debug** — Ctrl+Alt+Shift+D (`main.py --debug-protocol`, SHAYDBG).

Подсветка, Ctrl+Space и автодополнение знают EN-синонимы (`proc`, `begin`, `int`, …) наряду с русскими, а также управление потоком: `выход`/`break`, `продолжить`/`continue`, `возврат`/`return`, `шаг`/`step` и встроенные (`остаток`, `размер`, …). Комментарии строк — `|`.

Консоль: вывод интерпретатора; гиперссылки на `файл:строка` / «(строка N)».

### Полезные команды редактора

| Действие | Обычно |
|----------|--------|
| Toggle Comment | Ctrl+/ |
| Go to Matching Block | Ctrl+Shift+P |
| Quick Outline | Ctrl+O |
| Go to Declaration | F3 |
| Find References | Ctrl+Shift+G |
| Rename… | Alt+Shift+R |
| Reindent | Ctrl+Shift+F |

**Ограничения Rename / Find References:** только целые идентификаторы; **ключевые слова и builtins отклоняются**; текст в комментариях `|` и строках `"…"` / `'…'` пропускается. Это не семантический rename (без анализа областей). Точный список: **ALG → Keyboard Shortcuts…** / About.

---

## РЎРІСЏР·СЊ СЃ CLI РґРІРёР¶РєР°

Плагин вызывает тот же `main.py`, что и командная строка:

- Run → интерпретация;
- Check в†' `--check`;
- Transpile → `--transpile` (пишет `program.c` рядом с `.alg`);
- Step Debug → `--debug-protocol` (+ breakpoints как `--break`); wire-протокол — **[docs/SHAYDBG.md](docs/SHAYDBG.md)**.

Дополнительно с хоста: `--verbose`, `--trace`, `--repl --lang en` — см. README. Устаревший **CLI Debug** убран из плагина (используйте **Step Debug**).
