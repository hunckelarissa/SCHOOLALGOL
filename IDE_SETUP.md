# ALG IDE — установка плагина Eclipse

Операционная инструкция. Обзор возможностей плагина и языка — в **[README.md](README.md)**; грамматика — в **[GRAMMAR.md](GRAMMAR.md)**.

| | |
|--|--|
| Плагин | `org.myau.shaya.ide` **0.6.4** (`META-INF/MANIFEST.MF`) |
| Исходники | `F:\proj\SCHOOLALGOL\org.myau.shaya.ide` |
| Движок | SCHOOLALGOL **1.2.0** — только `.alg` → `main.py` (RU + EN) |
| Бренд UI | **ALG** (меню, перспектива, Preferences). Java-пакет `org.myau.shaya.ide` не переименовывался |

---

## Состав toolchain в dropins

Типичный путь (подставьте свой Eclipse):

```
…\eclipse\dropins\
  org.myau.shaya.ide_0.6.4.jar
  schoolalgol-shaya\
    tools\shaya-run.bat
    interpreters\SchoolAlgol\main.py   (+ lexer.py, parser.py, …)
```

Плагин ищет `schoolalgol-shaya` автоматически. При сбое:

**Window → Preferences → ALG → Toolchain home**  
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

`…\eclipse\dropins\org.myau.shaya.ide_0.6.4.jar`

После копирования/обновления JAR **обязательно перезапустите Eclipse** (иначе OSGi может не подхватить бандл).

- **dropins JAR** — повседневный запуск без PDE.
- **PDE «Run As → Eclipse Application»** — разработка из исходников в runtime workbench.

Удаляйте старые `org.myau.shaya.ide_0.6.1.jar` … `0.6.3.jar`, оставляя только **0.6.4**.

JAR с другим Bundle-SymbolicName (`org.shaya.ide_*.jar`) не конфликтует с `org.myau.shaya.ide` — можно оставить.

---

## Синхронизация Python: `install_dropins.ps1`

После правок `*.py` в корне `F:\proj\SCHOOLALGOL`:

```powershell
cd F:\proj\SCHOOLALGOL
.\install_dropins.ps1
```

Скопировать и JAR плагина (если собран):

```powershell
.\install_dropins.ps1 -PluginJar
```

Другой Eclipse:

```powershell
.\install_dropins.ps1 -EclipseDropins "D:\path\to\eclipse\dropins"
```

Скрипт копирует все `*.py` из корня репозитория в:

`dropins\schoolalgol-shaya\interpreters\SchoolAlgol\`

По умолчанию dropins: `C:\Users\User\eclipse\java-2022-12\eclipse\dropins`.

При обновлении только JAR toolchain Python не трогайте (или снова запустите скрипт без `-PluginJar` только для `.py`). Не кладите в toolchain архив `org.myau.shaya.ide.zip`.

---

## Импорт в PDE (разработка)

1. Eclipse IDE for Java с PDE (например `java-2022-12`).
2. **File → Import → Existing Projects into Workspace** → `F:\proj\SCHOOLALGOL\org.myau.shaya.ide`.
3. Target Platform: Eclipse SDK / RCP.
4. ПКМ по проекту → **Run As → Eclipse Application** (или Debug As).
5. В новом workbench: **Window → Perspective → Open Perspective → ALG**.

---

## Запуск программ .alg

1. **File → New → Project → ALG Project** (создаст Hello RU + EN) или открыть свой `.alg`.
2. **ALG → Run** — Ctrl+Alt+R.
3. **ALG → Check** — Ctrl+Alt+C (`main.py --check`).
4. **ALG → Run Last** — Ctrl+Alt+L.
5. Breakpoint (двойной клик по линейке) → **ALG → Step Debug** — Ctrl+Alt+Shift+D (`main.py --debug-protocol`, SHAYDBG).

Подсветка, Ctrl+Space и автодополнение знают EN-синонимы (`proc`, `begin`, `int`, …) наряду с русскими. Комментарии строк — `|`.

Консоль: вывод интерпретатора; гиперссылки на `файл:строка` / «(строка N)».

### Полезные команды редактора

| Действие | Обычно |
|----------|--------|
| Toggle Comment | Ctrl+/ |
| Go to Matching Block | Ctrl+Shift+P |
| Quick Outline | Ctrl+O |
| Go to Declaration | F3 |
| Find References | Ctrl+Shift+G |
| Reindent | Ctrl+Shift+F |

Точный список: **ALG → Keyboard Shortcuts…** / About.

---

## Связь с CLI движка

Плагин вызывает тот же `main.py`, что и командная строка:

- Run → интерпретация;
- Check → `--check`;
- Step Debug → `--debug-protocol` (+ breakpoints как `--break`).

Дополнительно с хоста: `--verbose`, `--trace`, `--repl --lang en` — см. README. Отдельный пункт меню «CLI Debug» для SCHOOLALGOL не используется (сообщение отсылает к Run / Check / Step Debug).
