# Быстрый старт — язык .alg и проект Gemini

За 5 минут: установка, первая программа, транспиляция в C.

## 1. Требования

- **Python 3.7+** (достаточно стандартной библиотеки)
- Опционально: **GCC** — для компиляции сгенерированного C-кода

Проверка:

```bash
python --version
```

## 2. Первая программа

Создайте файл `hello.alg`:

```alg
алг основнаяпрограмма
нач
  вывод "Привет, мир!"
кон
```

**Английский синтаксис (v1.1)** — те же возможности, другие ключевые слова:

```alg
proc mainprogram
begin
  output "Hello, world!"
end
```

Запуск:

```bash
python main.py hello.alg
python main.py examples/en/01_hello.alg
```

Ожидаемый вывод:

```
--- Вывод программы (версия 1.1.0) ---
Привет, мир!
-----------------------
```

Или через пакет:

```bash
python -m gemini hello.alg
```

## 3. Готовые примеры

В каталоге `examples/` — 10 учебных файлов с комментариями `|`:

```bash
python main.py examples/01_hello.alg
python main.py examples/04_loops.alg
python main.py examples/06_files.alg
python main.py examples/en/01_hello.alg
```

Каталог `examples/en/` — зеркала уроков 01–10 на английском синтаксисе.

## 4. Если что-то не работает

**Подробный разбор ошибки** — сообщение на русском с номером строки и указателем `^`:

```bash
python main.py broken.alg
```

**Этапы компиляции** (лексер → парсер → семантика → выполнение) в stderr:

```bash
python main.py hello.alg --verbose
```

**Пошаговая трассировка операторов:**

```bash
python main.py examples/04_loops.alg --trace
```

## 5. Транспиляция в C

```bash
python main.py hello.alg --transpile
```

Создаётся `hello.c`. Компиляция (если установлен GCC):

```bash
gcc hello.c -o hello -lm
./hello          # Linux / macOS
hello.exe        # Windows
```

Полный цикл одной командой:

```bash
python launcher.py examples/01_hello.alg --verbose
```

## 6. Интерактивный режим

```bash
python main.py --repl
```

Введите фрагменты `.alg` построчно; пустая строка — выполнить накопленный блок. Команды: `выход`, `.reset`, `.история`.

## 7. Минимальный синтаксис (шпаргалка)

| Конструкция | Пример |
|-------------|--------|
| Переменные | `цел x`, `вещ y`, `лит s`, `лог флаг` |
| Присваивание | `x := 10` |
| Условие | `если x > 0 то ... иначе ... все` |
| Цикл | `нц для i от 1 до 10` … `кц` / `loop for i from 1 to 10` … `eloop` |
| Массив | `таб цел a[1:5]` / `tab int a[1:5]` |
| Процедура | `алг имя` … `нач` … `кон` / `proc name` … `begin` … `end` |
| Функция | `алг имя(арг цел a; рез цел r)` … |
| Модуль | `использовать "lib.alg"` / `import "lib.alg"` |

Точка входа — **`алг основнаяпрограмма`** или **`proc mainprogram`**. Полная таблица синонимов: [GRAMMAR.md](GRAMMAR.md).

## 8. Куда дальше

| Документ | Для кого |
|----------|----------|
| **[PROGRAMMER.md](PROGRAMMER.md)** | Полное руководство программиста |
| **[TUTORIAL.md](TUTORIAL.md)** | Краткий курс из 7 уроков (школа) |
| **[GRAMMAR.md](GRAMMAR.md)** | Грамматика и семантика |
| **[EXERCISES.md](EXERCISES.md)** | Задачи для самостоятельной работы |
| **[README.md](README.md)** | Обзор проекта и инфраструктуры |
