#!/usr/bin/env python3
"""
CLI интерфейс для Mic Stream Py

Модуль предоставляет точки входа для командной строки:
- mic-stream: основной CLI интерфейс
- mic-stream daemon: фоновый сервис голосового ввода
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
        description="Speech-to-Text Client for Parakeet API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  mic-stream                          # Запуск терминального клиента
  mic-stream --api-url http://localhost:5092/v1  # Указать API URL
  mic-stream --test                   # Тестовый режим
  mic-stream daemon                   # Запустить фоновый сервис голосового ввода
  mic-stream trigger                  # Отправить триггер на демон
        """
    )

    # Глобальные аргументы
    parser.add_argument(
        '--api-url',
        default='http://localhost:5092/v1',
        help='URL Parakeet API (по умолчанию: http://localhost:5092/v1)'
    )
    parser.add_argument(
        '--model',
        default='parakeet-tdt-0.6b-v3',
        help='Модель для транскрипции (по умолчанию: parakeet-tdt-0.6b-v3)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Тестовый режим'
    )

    # Подкоманды
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')

    # Команда daemon
    daemon_parser = subparsers.add_parser(
        'daemon',
        help='Запустить фоновый сервис голосового ввода',
        description='Фоновый сервис для голосового ввода через Unix сокет'
    )
    daemon_parser.add_argument(
        '--api-url',
        default='http://localhost:5092/v1',
        help='URL Parakeet API'
    )
    daemon_parser.add_argument(
        '--model',
        default='parakeet-tdt-0.6b-v3',
        help='Модель для транскрипции'
    )
    daemon_parser.add_argument(
        '--socket-path',
        default=None,
        help='Путь к Unix сокету (по умолчанию: ~/.cache/voice-input.sock)'
    )

    # Команда trigger
    trigger_parser = subparsers.add_parser(
        'trigger',
        help='Отправить триггер на демон',
        description='Отправить сигнал записи/остановки на запущенный демон'
    )
    trigger_parser.add_argument(
        '--socket-path',
        default=None,
        help='Путь к Unix сокету демона'
    )

    return parser


def main():
    """Основная точка входа для mic-stream команды"""
    parser = create_parser()
    args = parser.parse_args()

    # Обработка подкоманд
    if args.command == 'daemon':
        main_daemon(args)
    elif args.command == 'trigger':
        main_trigger(args)
    else:
        # Запускаем клиент с переданными аргументами
        main_client(args)


def find_env_file():
    """Поиск .env файла в стандартных местах"""
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
        except Exception as e:
            print(f"⚠️ Ошибка чтения файла конфигурации: {e}")
    else:
        print("ℹ️ Файл конфигурации .env не найден")
        print("Используются значения по умолчанию")
        print("💡 Для настройки создайте .env файл в текущей директории или домашней папке")


def main_client(args):
    """Точка входа для клиента"""
    # Ищем и загружаем .env файл
    load_env_file()

    # Устанавливаем переменные окружения из аргументов (если указаны)
    if args.api_url:
        os.environ['PARAKEET_API_URL'] = args.api_url
    if args.model:
        os.environ['PARAKEET_MODEL'] = args.model

    print(f"🎤 Запуск STT клиента")
    print(f"   API: {args.api_url}")
    print(f"   Модель: {args.model}")

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


def main_daemon(args):
    """Точка входа для демона голосового ввода"""
    # Ищем и загружаем .env файл
    load_env_file()

    # Устанавливаем переменные окружения из аргументов (если указаны)
    if hasattr(args, 'api_url') and args.api_url:
        os.environ['PARAKEET_API_URL'] = args.api_url
    if hasattr(args, 'model') and args.model:
        os.environ['PARAKEET_MODEL'] = args.model

    print("Voice Input Daemon")
    print(f"   API: {args.api_url}")
    print(f"   Model: {args.model}")
    print(f"   Socket: {args.socket_path or '~/.cache/voice-input.sock'}")

    # Импортируем и запускаем демон
    try:
        from pathlib import Path
        from mic_stream_py.client.voice_daemon import VoiceInputDaemon
        daemon = VoiceInputDaemon(
            api_url=args.api_url,
            model=args.model,
            socket_path=Path(args.socket_path) if args.socket_path else None
        )
        daemon.run()
    except ImportError as e:
        print(f"Error: Failed to import voice_daemon module: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install pyperclip requests")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nDaemon stopped.")


def main_trigger(args):
    """Точка входа для отправки триггера на демон"""
    from pathlib import Path
    from mic_stream_py.client.voice_daemon import send_trigger

    socket_path = Path(args.socket_path) if args.socket_path else None
    if send_trigger(socket_path):
        print("Trigger sent successfully")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
