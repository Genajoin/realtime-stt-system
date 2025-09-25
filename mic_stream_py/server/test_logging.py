#!/usr/bin/env python3
"""
Тест системы логирования без запуска полного сервера.
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from env_config import env_config
    import logging
    
    # Настройка логирования как в сервере
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    logger = logging.getLogger('STTServer')
    
    def log_configuration():
        """Тест логирования конфигурации."""
        logger.info("STT SERVER CONFIGURATION")
        logger.info("=" * 50)
        
        # Основные параметры модели
        logger.info("MODEL SETTINGS:")
        logger.info(f"  Whisper Model: {env_config.get('model')}")
        logger.info(f"  Language: {env_config.get('language')}")
        logger.info(f"  Real-time Model: {env_config.get('realtime_model_type')}")
        logger.info(f"  Device: {env_config.get('device')}")
        
        # Сетевые параметры
        logger.info("NETWORK SETTINGS:")
        logger.info(f"  Control Port: {env_config.get('control_port')}")
        logger.info(f"  Data Port: {env_config.get('data_port')}")
        
        # Настройки транскрипции
        logger.info("TRANSCRIPTION SETTINGS:")
        realtime_status = "Enabled" if env_config.get('enable_realtime_transcription') else "Disabled"
        logger.info(f"  Real-time Transcription: {realtime_status}")
        onnx_status = "Enabled" if env_config.get('silero_use_onnx') else "Disabled"
        logger.info(f"  Silero ONNX: {onnx_status}")
        logger.info(f"  Real-time Pause: {env_config.get('realtime_processing_pause')}s")
        
        # Настройки VAD
        logger.info("VAD SETTINGS:")
        logger.info(f"  Silero Sensitivity: {env_config.get('silero_sensitivity')}")
        logger.info(f"  WebRTC Sensitivity: {env_config.get('webrtc_sensitivity')}")
        logger.info(f"  Post Speech Silence: {env_config.get('post_speech_silence_duration')}s")
        logger.info(f"  Min Recording Length: {env_config.get('min_length_of_recording')}s")
        
        # Настройки качества
        logger.info("QUALITY SETTINGS:")
        logger.info(f"  Beam Size: {env_config.get('beam_size')}")
        logger.info(f"  Beam Size (Real-time): {env_config.get('beam_size_realtime')}")
        initial_prompt = env_config.get('initial_prompt')
        prompt_preview = initial_prompt[:40] + "..." if len(initial_prompt) > 40 else initial_prompt
        logger.info(f"  Initial Prompt: {prompt_preview}")
        
        logger.info("=" * 50)
    
    if __name__ == '__main__':
        logger.info("Testing STT Server logging system...")
        log_configuration()
        logger.info("STT Server logging test completed successfully!")
        
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)