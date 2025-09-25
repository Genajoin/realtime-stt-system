#!/usr/bin/env python3
"""
Загрузчик конфигурации для STT сервера из переменных окружения.
"""

import os
from typing import Dict, Any, Union

class EnvConfig:
    """Класс для загрузки конфигурации из переменных окружения."""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из переменных окружения."""
        return {
            # Модель и язык
            "model": self._get_env("WHISPER_MODEL", "small"),
            "language": self._get_env("LANGUAGE", "ru"),
            "realtime_model_type": self._get_env("REALTIME_MODEL_TYPE", "tiny"),
            "device": self._get_env("DEVICE", "cuda"),
            
            # Настройки транскрипции
            "enable_realtime_transcription": self._get_env_bool("ENABLE_REALTIME_TRANSCRIPTION", True),
            "silero_use_onnx": self._get_env_bool("SILERO_USE_ONNX", True),
            
            # VAD настройки
            "silero_sensitivity": self._get_env_float("SILERO_SENSITIVITY", 0.05),
            "webrtc_sensitivity": self._get_env_int("WEBRTC_SENSITIVITY", 3),
            "post_speech_silence_duration": self._get_env_float("POST_SPEECH_SILENCE_DURATION", 0.7),
            "min_length_of_recording": self._get_env_float("MIN_LENGTH_OF_RECORDING", 1.1),
            
            # Beam search настройки
            "beam_size": self._get_env_int("BEAM_SIZE", 5),
            "beam_size_realtime": self._get_env_int("BEAM_SIZE_REALTIME", 3),
            "realtime_processing_pause": self._get_env_float("REALTIME_PROCESSING_PAUSE", 0.02),
            
            # Промпт
            "initial_prompt": self._get_env("INITIAL_PROMPT", 
                "Незаконченные мысли должны заканчиваться '...'. "
                "Примеры законченных: 'Небо голубое.' 'Она пошла домой.' "
                "Примеры незаконченных: 'Когда небо...' 'Потому что он...'"
            ),
            
            # Порты
            "control_port": self._get_env_int("CONTROL_PORT", 8011),
            "data_port": self._get_env_int("DATA_PORT", 8012),
        }
    
    def _get_env(self, key: str, default: str) -> str:
        """Получение строкового значения из переменной окружения."""
        return os.getenv(key, default)
    
    def _get_env_int(self, key: str, default: int) -> int:
        """Получение целочисленного значения из переменной окружения."""
        try:
            value = os.getenv(key)
            if value is None:
                return default
            return int(value)
        except ValueError:
            print(f"Предупреждение: Неверное значение для {key}, используется значение по умолчанию: {default}")
            return default
    
    def _get_env_float(self, key: str, default: float) -> float:
        """Получение вещественного значения из переменной окружения."""
        try:
            value = os.getenv(key)
            if value is None:
                return default
            return float(value)
        except ValueError:
            print(f"Предупреждение: Неверное значение для {key}, используется значение по умолчанию: {default}")
            return default
    
    def _get_env_bool(self, key: str, default: bool) -> bool:
        """Получение булевого значения из переменной окружения."""
        value = os.getenv(key)
        if value is None:
            return default
        
        value_lower = value.lower()
        if value_lower in ('true', '1', 'yes', 'on'):
            return True
        elif value_lower in ('false', '0', 'no', 'off'):
            return False
        else:
            print(f"Предупреждение: Неверное значение для {key}, используется значение по умолчанию: {default}")
            return default
    
    def get(self, key: str, default=None):
        """Получение значения параметра."""
        return self.config.get(key, default)
    
    def update(self, key: str, value: Any):
        """Обновление значения параметра."""
        self.config[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Получение всей конфигурации как словаря."""
        return self.config.copy()

# Глобальный экземпляр загрузчика конфигурации
env_config = EnvConfig()