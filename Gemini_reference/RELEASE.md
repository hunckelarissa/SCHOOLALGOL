# Версионирование релизов Gemini

Проект следует [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

## Перед релизом

1. Обновить `version.py` и `pyproject.toml` (`[project].version`).
2. Добавить секцию в `CHANGELOG.md` с датой.
3. Убедиться, что тесты проходят:
   ```bash
   python -m pytest tests/ -q
   python -m pytest tests/ -m "not slow" -q
   python -m pytest tests/ --cov=. --cov-fail-under=80 -q
   ```
4. При существенном изменении покрытия обновить бейдж в `README.md` (строка `coverage-XX%`).
5. Создать аннотированный тег (когда репозиторий готов к публикации):
   ```bash
   git tag -a v1.0.8 -m "Release 1.0.8"
   git push origin v1.0.8
   ```

## Соглашения

| Изменение | Версия |
|-----------|--------|
| Ломающие изменения языка/API | MAJOR |
| Новые возможности `.alg` / CLI | MINOR |
| Исправления, тесты, документация | PATCH |

## Текущая версия

См. `version.py` — единый источник истины для `main.py --version` и пакета `gemini`.

## Отложено

- **P6-06** — публикация расширения подсветки в VS Code Marketplace (грамматика уже в `editor/alg/`).
