#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import runpy
import traceback
import subprocess

# Получаем директорию, где находится этот скрипт
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

print(f"Рабочая директория: {os.getcwd()}")
print(f"Проверка файлов:")
print(f"  main.py: {os.path.exists('main.py')}")
print(f"  program.alg: {os.path.exists('program.alg')}")

if not os.path.exists('main.py'):
    print("ОШИБКА: main.py не найден!")
    sys.exit(1)

if not os.path.exists('program.alg'):
    print("ОШИБКА: program.alg не найден!")
    sys.exit(1)

def run_step(args, title):
    """
    Запускает main.py с указанными аргументами.
    Возвращает True, если выполнение прошло успешно (код 0 или без ошибок).
    """
    print("\n" + "="*60)
    print(f"ЗАПУСК: {title}")
    print("="*60 + "\n")
    
    # Подменяем sys.argv
    sys.argv = ['main.py'] + args
    
    try:
        # Используем runpy для запуска модуля в текущем процессе
        runpy.run_path('main.py', run_name='__main__')
        return True
    except SystemExit as e:
        # Перехватываем sys.exit()
        if e.code == 0 or e.code is None:
            return True
        print(f"\n>>> {title} завершилась с кодом возврата: {e.code}")
        return False
    except Exception as e:
        print(f"\n>>> КРИТИЧЕСКАЯ ОШИБКА при выполнении {title}: {e}")
        traceback.print_exc()
        return False

# --- Шаг 1: Интерпретация ---
if not run_step(['program.alg'], "ИНТЕРПРЕТАТОР"):
    print("\n!!! ОСТАНОВКА: Ошибка на этапе интерпретации.")
    sys.exit(1)

# --- Шаг 2: Транспиляция ---
if not run_step(['program.alg', '--transpile'], "ТРАНСПИЛЯТОР (в C)"):
    print("\n!!! ОСТАНОВКА: Ошибка на этапе транспиляции.")
    sys.exit(1)

# --- Шаг 3: Компиляция (GCC) ---
c_file = 'program.c'
exe_file = 'program.exe' if os.name == 'nt' else 'program'

print("\n" + "="*60)
print("ЗАПУСК: КОМПИЛЯЦИЯ (GCC)")
print("="*60 + "\n")

if not os.path.exists(c_file):
    print(f"ОШИБКА: Файл {c_file} не найден!")
    sys.exit(1)

compile_cmd = ['gcc', c_file, '-o', exe_file]
print(f"Выполняется: {' '.join(compile_cmd)}")

try:
    result = subprocess.run(compile_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ОШИБКА КОМПИЛЯЦИИ:")
        print(result.stderr)
        sys.exit(1)
    else:
        print("Компиляция прошла успешно.")
except FileNotFoundError:
    print("ОШИБКА: GCC не найден. Убедитесь, что он установлен и добавлен в PATH.")
    sys.exit(1)
except Exception as e:
    print(f"Ошибка при запуске GCC: {e}")
    sys.exit(1)

# --- Шаг 4: Запуск EXE ---
print("\n" + "="*60)
print("ЗАПУСК: ВЫПОЛНЕНИЕ EXE")
print("="*60 + "\n")

if not os.path.exists(exe_file):
     print(f"ОШИБКА: Файл {exe_file} не создан!")
     sys.exit(1)

try:
    # Запускаем exe
    # .\\program.exe для Windows, ./program для *nix
    cmd = f".{os.sep}{exe_file}"
    print(f"Запуск: {cmd}")
    subprocess.run([cmd], check=True)
except Exception as e:
    print(f"Ошибка при выполнении программы: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("УСПЕХ: Все этапы пройдены!")
print("="*60 + "\n")
