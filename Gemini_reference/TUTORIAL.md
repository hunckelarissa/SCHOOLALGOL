# Краткий учебник по языку .alg

Учебные материалы для 7–11 класса. Язык **.alg** — самостоятельный (не классический ШАЯ). Примеры лежат в каталоге `examples/`; английский синтаксис — в `examples/en/` (с **v1.1**).

> **Полное руководство программиста:** [PROGRAMMER.md](PROGRAMMER.md)  
> **Быстрый старт за 5 минут:** [QUICKSTART.md](QUICKSTART.md)  
> **Двуязычность:** русские и английские ключевые слова — синонимы ([GRAMMAR.md](GRAMMAR.md))

## Урок 1. Первая программа

Каждая программа начинается с процедуры **основнаяпрограмма** (или **mainprogram**):

| RU | EN |
|----|-----|
| `алг основнаяпрограмма` | `proc mainprogram` |
| `нач` … `кон` | `begin` … `end` |
| `вывод "…"` | `output "…"` |

```alg
алг основнаяпрограмма
нач
  вывод "Привет, мир!"
кон
```

```alg
proc mainprogram
begin
  output "Hello, world!"
end
```

Запуск:

```bash
python main.py examples/01_hello.alg
python main.py examples/en/01_hello.alg
```

Ключевые слова **алг/proc**, **нач/begin**, **кон/end** обрамляют тело программы. **вывод/output** печатает значения в консоль.

## Урок 2. Переменные и типы

| Тип   | RU        | EN        | Пример RU   | Пример EN  |
|-------|-----------|-----------|-------------|------------|
| целое | **цел**   | **int**   | `цел n`     | `int n`    |
| дробное | **вещ** | **real**  | `вещ x`     | `real x`   |
| строка | **лит**  | **str**   | `лит s`     | `str s`    |
| логическое | **лог** | **bool** | `лог флаг`  | `bool flag` |

Присваивание: `:=`

```bash
python main.py examples/02_variables.alg
python main.py examples/en/02_variables.alg
```

## Урок 3. Условия

```alg
если условие то
  ...
иначе
  ...
все
```

```alg
if condition then
  ...
else
  ...
endif
```

Операторы сравнения: `=`, `<>` (не равно), `>`, `<`, `>=`, `<=`.

```bash
python main.py examples/03_conditions.alg
python main.py examples/en/03_conditions.alg
```

## Урок 4. Циклы

**нц для** / **loop for** — счётчик от начала до конца включительно:

```alg
нц для i от 1 до 10
  вывод i
кц
```

```alg
loop for i from 1 to 10
  output i
eloop
```

**нц пока** / **loop while** — пока условие истинно:

```alg
нц пока x > 0
  x := x - 1
кц
```

```alg
loop while x > 0
  x := x - 1
eloop
```

Если переменная цикла не объявлена, интерпретатор создаст **цел/int** автоматически (с предупреждением).

```bash
python main.py examples/04_loops.alg
python main.py examples/en/04_loops.alg
```

## Урок 5. Массивы

```alg
таб цел a[1:5]    | индексы от 1 до 5
a[3] := 42
```

Можно задать другой начальный индекс: `таб цел b[0:2]`.

```bash
python main.py examples/05_arrays.alg
```

## Урок 6. Работа с файлами

```alg
файл f
открыть(f, "data.txt", "запись")
вывод f, "текст"
закрыть(f)
```

**Важно:** путь к файлу не ограничен каталогом проекта. Программа может читать и писать **любые** файлы, к которым у пользователя есть права в ОС (в том числе `C:\Windows\System32\drivers\etc\hosts` или `/etc/hosts`). Ответственность за выбор пути — на авторе программы.

```bash
python main.py examples/06_files.alg
```

## Урок 7. Строки и escape

В строках в кавычках работают escape-последовательности:

- `\n` — новая строка
- `\t` — табуляция
- `\"` — кавычка
- `\\` — обратный слэш

Строки склеиваются оператором `+`: `вывод "Hello" + " " + "World"`.

```bash
python main.py examples/07_strings.alg
```

## Отладка

| Флаг | Назначение |
|------|------------|
| `--verbose` | Этапы лексера, парсера, интерпретатора в stderr |
| `--trace` | Каждый оператор перед выполнением |
| `--transpile` | Сгенерировать C вместо запуска |

Пример:

```bash
python main.py examples/04_loops.alg --verbose --trace
```

## Путь к языку C

Транспилятор создаёт файл `.c`, который можно скомпилировать GCC:

```bash
python main.py examples/01_hello.alg --transpile
gcc 01_hello.c -o hello -lm
```

Полный цикл (интерпретация → C → GCC → exe):

```bash
python launcher.py examples/01_hello.alg --verbose
```

Над сгенерированными функциями в C стоят комментарии `// alg: ИмяПроцедуры` — так проще сопоставить код с исходником `.alg`.

### Пример: `.alg` рядом с `.c`

Исходник:

```alg
алг основнаяпрограмма
нач
  цел i
  нц для i от 1 до 3
    вывод i
  кц
кон
```

Фрагмент сгенерированного C (сокращённо):

```c
// alg: основнаяпрограмма
int main() {
    int i = 0;
    for (i = (int)1; i <= (int)3; i++) {
        printf("%g", (double)i);
        printf("\n");
    }
    return 0;
}
```

Сопоставление:
- `нц для` → `for` с инкрементом;
- `вывод` → `printf` + перевод строки;
- `цел` → `int` в объявлении.

```bash
python main.py examples/07_strings.alg
python main.py examples/08_hosts.alg
```

## REPL

```bash
python main.py --repl
python main.py --repl --lang en
```

Команды внутри REPL: `выход`/`exit`, `.reset`, `.история`. Пустая строка выполняет накопленный фрагмент. С `--lang en` обёртка — `proc mainprogram` / `begin` / `end`.

## Дальше

- **Руководство программиста:** [PROGRAMMER.md](PROGRAMMER.md)
- **Быстрый старт:** [QUICKSTART.md](QUICKSTART.md)
- Полная грамматика: [GRAMMAR.md](GRAMMAR.md)
- Задачи: [EXERCISES.md](EXERCISES.md)
- Демонстрация всех возможностей: **program.alg** + **utils.alg**
- Набор регрессионных программ: **tests/programs/**
- Обзор проекта: [README.md](README.md)
