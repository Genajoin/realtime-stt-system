#!/usr/bin/env python3
"""
Тест значений по умолчанию без .env файла.
Убеждается, что сервер может запуститься без конфигурации.
"""

import os
import sys
from env_config import EnvConfig

# Убираем все переменные окружения связанные с конфигурацией
env_vars_to_remove = [
    'WHISPER_MODEL', 'LANGUAGE', 'REALTIME_MODEL_TYPE', 'DEVICE',
    'ENABLE_REALTIME_TRANSCRIPTION', 'SILERO_USE_ONNX',
    'SILERO_SENSITIVITY', 'WEBRTC_SENSITIVITY', 
    'POST_SPEECH_SILENCE_DURATION', 'MIN_LENGTH_OF_RECORDING',
    'BEAM_SIZE', 'BEAM_SIZE_REALTIME', 'REALTIME_PROCESSING_PAUSE',
    'INITIAL_PROMPT', 'CONTROL_PORT', 'DATA_PORT'
]

for var in env_vars_to_remove:
    if var in os.environ:
        del os.environ[var]

# Теперь импортируем и тестируем

def test_defaults():
    """Тест значений по умолчанию."""
    print("=== Тест значений по умолчанию (без .env файла) ===\n")
    
    config = EnvConfig()
    
    expected_defaults = {
        'model': 'medium',
        'language': 'ru', 
        'realtime_model_type': 'tiny',
        'device': 'cuda',
        'enable_realtime_transcription': True,
        'silero_use_onnx': True,
        'silero_sensitivity': 0.05,
        'webrtc_sensitivity': 3,
        'post_speech_silence_duration': 0.7,
        'min_length_of_recording': 1.1,
        'beam_size': 5,
        'beam_size_realtime': 3,
        'realtime_processing_pause': 0.02,
        'control_port': 8011,
        'data_port': 8012
    }
    
    all_passed = True
    
    for key, expected_value in expected_defaults.items():
        actual_value = config.get(key)
        status = "✅" if actual_value == expected_value else "❌"
        print(f"{status} {key}: {actual_value} (ожидалось: {expected_value})")
        
        if actual_value != expected_value:
            all_passed = False
    
    print(f"\nПромпт: {config.get('initial_prompt')[:50]}...")
    
    if all_passed:
        print("\n✅ Все значения по умолчанию корректны!")
        print("📦 Сервер может работать без .env файла")
        return True
    else:
        print("\n❌ Найдены несоответствия в значениях по умолчанию")
        return False

if __name__ == '__main__':
    success = test_defaults()
    sys.exit(0 if success else 1)