# Расширение подсветки .alg для VS Code / Cursor

1. Откройте палитру команд → **Extensions: Install from VSIX...**  
   или **Developer: Install Extension from Location...**
2. Укажите каталог `editor/alg` этого репозитория.
3. Файлы `*.alg` получат подсветку ключевых слов, строк, комментариев `|`.

Альтернатива без установки: в `settings.json` проекта:

```json
{
  "files.associations": {
    "*.alg": "alg"
  }
}
```

и скопируйте `syntaxes/alg.tmLanguage.json` в пользовательские snippets/grammar (см. документацию редактора).

Грамматика: TextMate scope `source.alg`.

С **v1.1** подсвечиваются и **английские** ключевые слова (`proc`, `begin`, `int`, `if`, `loop`, `open`, …) наравне с русскими.
