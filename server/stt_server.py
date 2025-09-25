#!/usr/bin/env python3
"""
Адаптированный STT сервер для Docker контейнера.
Основан на оригинальном коде из RealtimeSTT/RealtimeSTT_server/stt_server.py
с упрощениями и адаптацией для контейнерной среды.
"""

import os
import sys
import json
import time
import wave
import asyncio
import logging
import threading
from datetime import datetime
from collections import deque
import base64
from env_config import env_config

# Настройка логирования для Docker
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger('STTServer')

# Проверяем наличие зависимостей
try:
    import numpy as np
    import websockets
    from colorama import init, Fore, Style
    from RealtimeSTT import AudioToTextRecorder
    from scipy.signal import resample
    import pyaudio
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    sys.exit(1)

# Инициализация colorama
init()

# Глобальные переменные
FORMAT = pyaudio.paInt16
CHANNELS = 1

# Цвета для вывода
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m' 
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class STTServer:
    def __init__(self, args):
        self.args = args
        self.recorder = None
        self.recorder_ready = threading.Event()
        self.stop_recorder = False
        self.prev_text = ""
        
        # WebSocket соединения
        self.control_connections = set()
        self.data_connections = set()
        self.audio_queue = asyncio.Queue()
        
        # Разрешенные методы и параметры для безопасности
        self.allowed_methods = [
            'set_microphone', 'abort', 'stop', 'clear_audio_queue', 
            'wakeup', 'shutdown', 'text'
        ]
        self.allowed_parameters = [
            'language', 'silero_sensitivity', 'post_speech_silence_duration',
            'is_recording', 'use_wake_words'
        ]
        
        logger.info("Инициализация STT сервера...")
        self.log_configuration()
        
    def log_configuration(self):
        """Подробное логирование конфигурации сервера."""
        logger.info("STT SERVER CONFIGURATION")
        logger.info("=" * 50)
        
        # Проверка реального состояния GPU
        self.log_gpu_status()
        
        # Основные параметры модели
        logger.info("MODEL SETTINGS:")
        logger.info(f"  Whisper Model: {env_config.get('model')}")
        logger.info(f"  Language: {env_config.get('language')}")
        logger.info(f"  Real-time Model: {env_config.get('realtime_model_type')}")
        configured_device = env_config.get('device')
        actual_device = self.get_actual_device()
        logger.info(f"  Configured Device: {configured_device}")
        logger.info(f"  Actual Device: {actual_device}")
        if configured_device != actual_device:
            logger.warning(f"  WARNING: Device fallback from {configured_device} to {actual_device}")
        
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
    
    def log_gpu_status(self):
        """Проверка и логирование реального состояния GPU."""
        logger.info("GPU STATUS:")
        
        try:
            import torch
            
            # Проверка доступности CUDA
            cuda_available = torch.cuda.is_available()
            logger.info(f"  CUDA Available: {cuda_available}")
            
            if cuda_available:
                # Информация о GPU устройствах
                device_count = torch.cuda.device_count()
                logger.info(f"  GPU Devices Count: {device_count}")
                
                for i in range(device_count):
                    gpu_name = torch.cuda.get_device_name(i)
                    gpu_memory = torch.cuda.get_device_properties(i).total_memory
                    gpu_memory_gb = gpu_memory / (1024**3)
                    logger.info(f"  GPU {i}: {gpu_name} ({gpu_memory_gb:.1f} GB)")
                
                # Проверка текущего GPU устройства
                if device_count > 0:
                    current_device = torch.cuda.current_device()
                    logger.info(f"  Current GPU Device: {current_device}")
                    
                    # Проверка свободной памяти
                    try:
                        free_memory = torch.cuda.mem_get_info()[0]
                        total_memory = torch.cuda.mem_get_info()[1]
                        used_memory = total_memory - free_memory
                        
                        logger.info(f"  GPU Memory - Total: {total_memory / (1024**3):.1f} GB")
                        logger.info(f"  GPU Memory - Used: {used_memory / (1024**3):.1f} GB")
                        logger.info(f"  GPU Memory - Free: {free_memory / (1024**3):.1f} GB")
                    except Exception as e:
                        logger.warning(f"  Could not get GPU memory info: {e}")
            else:
                logger.warning("  CUDA not available - will use CPU")
                
        except ImportError:
            logger.error("  PyTorch not available - cannot check GPU status")
        except Exception as e:
            logger.error(f"  Error checking GPU status: {e}")
        
        logger.info("-" * 30)
    
    def get_actual_device(self):
        """Определение реального устройства, которое будет использоваться."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        except ImportError:
            return "cpu"
        
    def log_recorder_config(self, config):
        """Логирование конфигурации recorder'а."""
        logger.info("AUDIORECORDER CONFIG:")
        logger.info(f"  Model: {config['model']}")
        logger.info(f"  Language: {config['language']}")
        logger.info(f"  Real-time Model: {config['realtime_model_type']}")
        logger.info(f"  Requested Device: {config['device']}")
        actual_device = self.get_actual_device()
        logger.info(f"  Actual Device: {actual_device}")
        if config['device'] != actual_device:
            logger.warning(f"  DEVICE FALLBACK: {config['device']} -> {actual_device}")
        logger.info(f"  Compute Type: {config['compute_type']}")
        logger.info(f"  Real-time Transcription: {config['enable_realtime_transcription']}")
        logger.info(f"  Silero ONNX: {config['silero_use_onnx']}")
        logger.info(f"  Silero Sensitivity: {config['silero_sensitivity']}")
        logger.info(f"  WebRTC Sensitivity: {config['webrtc_sensitivity']}")
        logger.info(f"  Beam Size: {config['beam_size']}")
        logger.info(f"  Beam Size (Real-time): {config['beam_size_realtime']}")
        logger.info("-" * 40)
    
    def log_final_gpu_status(self):
        """Финальная проверка GPU после загрузки модели."""
        logger.info("POST-INITIALIZATION GPU STATUS:")
        
        try:
            import torch
            
            if torch.cuda.is_available():
                # Проверка памяти после загрузки модели
                free_memory = torch.cuda.mem_get_info()[0]
                total_memory = torch.cuda.mem_get_info()[1]
                used_memory = total_memory - free_memory
                
                logger.info(f"  GPU Memory After Model Load:")
                logger.info(f"    Total: {total_memory / (1024**3):.1f} GB")
                logger.info(f"    Used: {used_memory / (1024**3):.1f} GB")
                logger.info(f"    Free: {free_memory / (1024**3):.1f} GB")
                logger.info(f"  Model successfully loaded on GPU!")
            else:
                logger.warning("  Model loaded on CPU (CUDA not available)")
                
        except Exception as e:
            logger.error(f"  Error checking final GPU status: {e}")
        
        logger.info("=" * 50)
        
    def preprocess_text(self, text):
        """Предобработка текста."""
        text = text.lstrip()
        if text.startswith("..."):
            text = text[3:]
        text = text.lstrip()
        if text:
            text = text[0].upper() + text[1:]
        return text
    
    def text_detected(self, text, loop):
        """Обработка real-time текста."""
        text = self.preprocess_text(text)
        self.prev_text = text
        
        # Отправляем в очередь для WebSocket клиентов
        message = json.dumps({
            'type': 'realtime',
            'text': text
        })
        asyncio.run_coroutine_threadsafe(self.audio_queue.put(message), loop)
        
        # Выводим в консоль сервера
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"\r[{timestamp}] {Colors.CYAN}{text}{Colors.ENDC}", flush=True, end='')
    
    def process_final_text(self, text, loop):
        """Обработка финального текста."""
        text = self.preprocess_text(text)
        if not text.strip():
            return
            
        message = json.dumps({
            'type': 'fullSentence', 
            'text': text
        })
        asyncio.run_coroutine_threadsafe(self.audio_queue.put(message), loop)
        
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"\r[{timestamp}] {Colors.BOLD}Предложение:{Colors.ENDC} {Colors.GREEN}{text}{Colors.ENDC}\n")
        
    def create_recorder_config(self, loop):
        """Создание конфигурации для recorder."""
        return {
            'model': env_config.get('model'),
            'language': env_config.get('language'),
            'realtime_model_type': env_config.get('realtime_model_type'),
            'device': env_config.get('device'),
            'compute_type': 'default',
            
            # Real-time настройки
            'enable_realtime_transcription': env_config.get('enable_realtime_transcription'),
            'realtime_processing_pause': env_config.get('realtime_processing_pause'),
            'on_realtime_transcription_update': lambda text: self.text_detected(text, loop),
            
            # VAD настройки
            'silero_sensitivity': env_config.get('silero_sensitivity'),
            'silero_use_onnx': env_config.get('silero_use_onnx'),
            'webrtc_sensitivity': env_config.get('webrtc_sensitivity'),
            'post_speech_silence_duration': env_config.get('post_speech_silence_duration'),
            'min_length_of_recording': env_config.get('min_length_of_recording'),
            'silero_deactivity_detection': True,
            
            # Качество
            'beam_size': env_config.get('beam_size'),
            'beam_size_realtime': env_config.get('beam_size_realtime'),
            'initial_prompt': env_config.get('initial_prompt'),
            
            # Настройки для контейнера
            'use_microphone': False,
            'spinner': False,
            'no_log_file': True,
            'level': logging.WARNING
        }
    
    def recorder_thread(self, loop):
        """Поток для recorder."""
        try:
            config = self.create_recorder_config(loop)
            self.log_recorder_config(config)
            logger.info("Creating AudioToTextRecorder...")
            self.recorder = AudioToTextRecorder(**config)
            logger.info("Recorder initialized successfully")
            
            # Финальная проверка GPU использования после инициализации модели
            self.log_final_gpu_status()
            self.recorder_ready.set()
            
            def process_text_wrapper(text):
                self.process_final_text(text, loop)
            
            # Основной цикл обработки
            while not self.stop_recorder:
                self.recorder.text(process_text_wrapper)
                
        except Exception as e:
            logger.error(f"Error in recorder thread: {e}")
        finally:
            logger.info("Recorder thread finished")
    
    async def control_handler(self, websocket):
        """Обработчик control WebSocket соединений."""
        logger.info("Control client connected")
        self.control_connections.add(websocket)
        
        try:
            async for message in websocket:
                if not self.recorder_ready.is_set():
                    await websocket.send(json.dumps({
                        "status": "error", 
                        "message": "Recorder не готов"
                    }))
                    continue
                    
                try:
                    command_data = json.loads(message)
                    command = command_data.get("command")
                    
                    if command == "set_parameter":
                        parameter = command_data.get("parameter")
                        value = command_data.get("value")
                        
                        if parameter in self.allowed_parameters and hasattr(self.recorder, parameter):
                            setattr(self.recorder, parameter, value)
                            await websocket.send(json.dumps({
                                "status": "success", 
                                "message": f"Параметр {parameter} установлен в {value}"
                            }))
                        else:
                            await websocket.send(json.dumps({
                                "status": "error",
                                "message": f"Параметр {parameter} недоступен"
                            }))
                            
                    elif command == "get_parameter":
                        parameter = command_data.get("parameter")
                        if parameter in self.allowed_parameters and hasattr(self.recorder, parameter):
                            value = getattr(self.recorder, parameter)
                            await websocket.send(json.dumps({
                                "status": "success",
                                "parameter": parameter,
                                "value": value
                            }))
                        else:
                            await websocket.send(json.dumps({
                                "status": "error",
                                "message": f"Параметр {parameter} недоступен"
                            }))
                            
                    else:
                        await websocket.send(json.dumps({
                            "status": "error",
                            "message": f"Неизвестная команда: {command}"
                        }))
                        
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": "Неверный JSON"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Control client disconnected")
        finally:
            self.control_connections.remove(websocket)
    
    async def data_handler(self, websocket):
        """Обработчик data WebSocket соединений."""
        logger.info("Data client connected")
        self.data_connections.add(websocket)
        
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    # Парсим метаданные
                    metadata_length = int.from_bytes(message[:4], byteorder='little')
                    metadata_json = message[4:4+metadata_length].decode('utf-8')
                    metadata = json.loads(metadata_json)
                    sample_rate = metadata['sampleRate']
                    
                    # Извлекаем аудио данные
                    chunk = message[4+metadata_length:]
                    
                    # Ресамплинг если нужно
                    if sample_rate != 16000:
                        chunk = self.decode_and_resample(chunk, sample_rate, 16000)
                    
                    # Отправляем в recorder
                    if self.recorder and self.recorder_ready.is_set():
                        self.recorder.feed_audio(chunk)
                        
        except websockets.exceptions.ConnectionClosed:
            logger.info("Data client disconnected")
        finally:
            self.data_connections.remove(websocket)
            if self.recorder:
                self.recorder.clear_audio_queue()
    
    def decode_and_resample(self, audio_data, original_sample_rate, target_sample_rate):
        """Ресамплинг аудио."""
        if original_sample_rate == target_sample_rate:
            return audio_data
            
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        num_original_samples = len(audio_np)
        num_target_samples = int(num_original_samples * target_sample_rate / original_sample_rate)
        resampled_audio = resample(audio_np, num_target_samples)
        return np.array(resampled_audio, dtype=np.int16).tobytes()
    
    async def broadcast_audio_messages(self):
        """Трансляция сообщений всем data клиентам."""
        while True:
            try:
                message = await self.audio_queue.get()
                if not self.data_connections:
                    continue
                    
                for conn in list(self.data_connections):
                    try:
                        await conn.send(message)
                    except websockets.exceptions.ConnectionClosed:
                        self.data_connections.discard(conn)
            except Exception as e:
                logger.error(f"Error in broadcast: {e}")
    
    async def run(self):
        """Запуск сервера."""
        try:
            # Получаем event loop
            loop = asyncio.get_event_loop()
            
            # Запускаем WebSocket серверы
            control_server = await websockets.serve(
                self.control_handler, "0.0.0.0", env_config.get('control_port')
            )
            data_server = await websockets.serve(
                self.data_handler, "0.0.0.0", env_config.get('data_port')
            )
            
            logger.info(f"Control WebSocket server started on port {env_config.get('control_port')}")
            logger.info(f"Data WebSocket server started on port {env_config.get('data_port')}")
            
            # Запускаем broadcast задачу
            broadcast_task = asyncio.create_task(self.broadcast_audio_messages())
            
            # Запускаем recorder в отдельном потоке
            recorder_thread = threading.Thread(target=self.recorder_thread, args=(loop,))
            recorder_thread.start()
            
            # Ждем готовности recorder
            self.recorder_ready.wait()
            logger.info("STT Server is ready for connections!")
            
            # Ждем завершения
            await asyncio.gather(
                control_server.wait_closed(),
                data_server.wait_closed(), 
                broadcast_task
            )
            
        except KeyboardInterrupt:
            print(f"{Colors.YELLOW}Остановка сервера...{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}Ошибка сервера: {e}{Colors.ENDC}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Корректное завершение работы."""
        self.stop_recorder = True
        if self.recorder:
            self.recorder.abort()
            self.recorder.stop()
            self.recorder.shutdown()
        print(f"{Colors.GREEN}Сервер остановлен{Colors.ENDC}")

def parse_arguments():
    """Парсинг аргументов командной строки."""
    import argparse
    parser = argparse.ArgumentParser(description='STT Server для Docker')
    
    # Аргументы командной строки имеют приоритет над переменными окружения
    parser.add_argument('-m', '--model', type=str,
                       help='Модель Whisper (default: из .env)')
    parser.add_argument('-l', '--language', type=str,
                       help='Язык (default: из .env)')
    parser.add_argument('-r', '--realtime_model_type', type=str,
                       help='Модель для real-time (default: из .env)')
    parser.add_argument('-c', '--control_port', type=int,
                       help='Порт для control WebSocket (default: из .env)')
    parser.add_argument('-d', '--data_port', type=int,
                       help='Порт для data WebSocket (default: из .env)')
    parser.add_argument('--device', type=str,
                       help='Устройство: cuda или cpu (default: из .env)')
    parser.add_argument('--enable_realtime_transcription', action='store_true',
                       help='Включить real-time транскрипцию')
    parser.add_argument('--silero_use_onnx', action='store_true',
                       help='Использовать ONNX версию Silero')
    
    args = parser.parse_args()
    
    # Если аргументы не указаны, используем значения из .env
    if args.model is None:
        args.model = env_config.get('model')
    if args.language is None:
        args.language = env_config.get('language')
    if args.realtime_model_type is None:
        args.realtime_model_type = env_config.get('realtime_model_type')
    if args.control_port is None:
        args.control_port = env_config.get('control_port')
    if args.data_port is None:
        args.data_port = env_config.get('data_port')
    if args.device is None:
        args.device = env_config.get('device')
    if args.enable_realtime_transcription is None:
        args.enable_realtime_transcription = env_config.get('enable_realtime_transcription')
    if args.silero_use_onnx is None:
        args.silero_use_onnx = env_config.get('silero_use_onnx')
    
    return args

async def main():
    """Главная функция."""
    args = parse_arguments()
    server = STTServer(args)
    await server.run()

if __name__ == '__main__':
    asyncio.run(main())