#!/usr/bin/env python3
"""
CLI интерфейс для Mic Stream Py

Модуль предоставляет точки входа для командной строки:
- mic-stream: основной CLI интерфейс
- stt-client: терминальный клиент
"""

import argparse
import sys
import os
from pathlib import Path

# Добавляем корень проекта в путь для импортов
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Импортируем функции из клиентских модулей
try:
    from mic_stream_py.client.minimal_editor import main as minimal_editor_main
except ImportError:
    minimal_editor_main = None


def create_parser() -> argparse.ArgumentParser:
    """Создает парсер аргументов командной строки"""
    parser = argparse.ArgumentParser(
        prog="mic-stream",
        description="Real-time Speech-to-Text Client CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  mic-stream                          # Запуск терминального клиента
  mic-stream --server 192.168.1.100   # Подключение к конкретному серверу
        """
    )
    
    parser.add_argument(
        '--server',
        default='localhost',
        help='Хост сервера (по умолчанию: localhost)'
    )
    parser.add_argument(
        '--control-port',
        type=int,
        default=8011,
        help='Порт для управления (по умолчанию: 8011)'
    )
    parser.add_argument(
        '--data-port',
        type=int,
        default=8012,
        help='Порт для данных (по умолчанию: 8012)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Тестовый режим'
    )
    
    return parser


def main():
    """Основная точка входа для mic-stream команды"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Запускаем клиент с переданными аргументами
    main_client(args)


def find_env_file():
    """Поиск .env файла в стандартных местах"""
    # Места поиска по приоритету
    search_paths = [
        # 1. Текущая рабочая директория
        os.path.join(os.getcwd(), '.env'),
        # 2. Домашний каталог пользователя
        os.path.expanduser('~/.env'),
        # 3. Домашний каталог с именем mic-stream.env
        os.path.expanduser('~/mic-stream.env'),
        # 4. XDG config directory
        os.path.expanduser('~/.config/mic-stream/.env'),
        # 5. XDG data directory
        os.path.expanduser('~/.local/share/mic-stream/.env'),
        # 6. Запасной вариант - исходный проект (для development)
        os.path.join(os.path.dirname(__file__), "..", ".env"),
    ]

    for env_file in search_paths:
        if os.path.exists(env_file):
            return env_file
    return None

def load_env_file(env_file=None):
    """Загрузка переменных окружения из файла"""
    if env_file is None:
        env_file = find_env_file()

    if env_file and os.path.exists(env_file):
        print(f"Загрузка конфигурации из: {env_file}")
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                            print(f"  {key.strip()}={value.strip()}")
        except Exception as e:
            print(f"⚠️ Ошибка чтения файла конфигурации: {e}")
    else:
        print("ℹ️ Файл конфигурации .env не найден")
        print("Используются значения по умолчанию")
        print("💡 Для настройки создайте .env файл в текущей директории или домашней папке")

def main_client(args):
    """Точка входа для stt-client команды"""
    # Ищем и загружаем .env файл в стандартных местах
    load_env_file()
    
    # Строим полные URL для подключения к серверу
    control_url = f"ws://{args.server}:{args.control_port}"
    data_url = f"ws://{args.server}:{args.data_port}"
    
    # Устанавливаем переменные окружения с правильными URL
    os.environ['CONTROL_URL'] = control_url
    os.environ['DATA_URL'] = data_url
    
    print(f"🎤 Запуск STT клиента для {args.server}:{args.control_port}")
    
    # Подготавливаем аргументы для оригинальной функции (только --test)
    original_args = []
    if args.test:
        original_args.append('--test')
    
    # Заменяем sys.argv для оригинальной функции
    sys.argv = ['stt-client'] + original_args
    
    if minimal_editor_main is None:
        print("❌ Модуль клиента не найден")
        print("💡 Установите зависимости: pip install -e .")
        sys.exit(1)
    
    # Вызываем оригинальную main функцию (асинхронную)
    import asyncio
    asyncio.run(minimal_editor_main())


# Функция main_gui удалена, так как GUI клиента нет в проекте


# Функция main_server удалена, так как запуск сервера через CLI не поддерживается


if __name__ == '__main__':
    main()