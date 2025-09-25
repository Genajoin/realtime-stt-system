#!/usr/bin/env python3
"""
Запускает GUI редактор транскрипции с загрузкой конфигурации
"""

import subprocess
import sys
import os

def load_env_file(env_file):
    """Загрузка переменных окружения из файла"""
    if os.path.exists(env_file):
        print(f"Загрузка конфигурации из: {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                        print(f"  {key.strip()}={value.strip()}")
    else:
        print(f"Файл конфигурации не найден: {env_file}")
        print("Используются значения по умолчанию")

def main():
    print("=== GUI Редактор Транскрипции ===")
    
    # Загрузка конфигурации из .env файла
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    load_env_file(env_file)
    
    # Путь к GUI редактору
    editor_path = os.path.join(os.path.dirname(__file__), "transcription_editor.py")
    
    try:
        print(f"\nЗапуск редактора: {editor_path}")
        # Запуск GUI редактора
        subprocess.run([sys.executable, editor_path], check=True)
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
    except Exception as e:
        print(f"Ошибка запуска GUI редактора: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())