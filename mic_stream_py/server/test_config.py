#!/usr/bin/env python3
"""
Тестовый скрипт для проверки загрузки конфигурации из переменных окружения.
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).parent))

try:
    from env_config import env_config
    
    print("=== Тестирование конфигурации из переменных окружения ===")
    print()
    
    # Выводим все параметры конфигурации
    config_dict = env_config.to_dict()
    for key, value in sorted(config_dict.items()):
        print(f"{key}: {value} ({type(value).__name__})")
    
    print()
    print("=== Тестирование отдельных методов ===")
    
    # Тестирование получения значений
    print(f"Модель: {env_config.get('model')}")
    print(f"Язык: {env_config.get('language')}")
    print(f"Устройство: {env_config.get('device')}")
    print(f"Порт control: {env_config.get('control_port')}")
    print(f"Порт data: {env_config.get('data_port')}")
    print(f"Real-time транскрипция: {env_config.get('enable_realtime_transcription')}")
    print(f"Чувствительность Silero: {env_config.get('silero_sensitivity')}")
    
    print()
    print("=== Тестирование обновления параметров ===")
    
    # Тестирование обновления
    env_config.update('test_param', 'test_value')
    print(f"Тестовый параметр: {env_config.get('test_param')}")
    
    print()
    print("✅ Конфигурация загружена успешно!")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Ошибка: {e}")
    sys.exit(1)