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

def main_client(args):
    """Точка входа для stt-client команды"""
    # Загружаем .env файл из корня проекта
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_env_file(env_file)
    
    # Устанавливаем переменные окружения из аргументов
    os.environ['SERVER_HOST'] = args.server
    os.environ['CONTROL_PORT'] = str(args.control_port)
    os.environ['DATA_PORT'] = str(args.data_port)
    
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