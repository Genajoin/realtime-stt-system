#!/usr/bin/env python3
"""
Модуль для транскрипции аудио файлов (MP3, WAV и др.) через Whisper.
Используется для обработки загруженных файлов через HTTP API.
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
import numpy as np

logger = logging.getLogger('FileTranscriber')

class FileTranscriber:
    """Класс для транскрипции аудио файлов через Whisper."""
    
    def __init__(self, model_name: str = "large", device: str = "cuda", language: Optional[str] = None):
        """
        Инициализация транскрайбера для файлов.
        
        Args:
            model_name: Название модели Whisper (tiny, base, small, medium, large)
            device: Устройство для вычислений (cuda или cpu)
            language: Язык аудио (None для автоопределения)
        """
        self.model_name = model_name
        self.device = device
        self.language = language
        self.model = None
        
        logger.info(f"Инициализация FileTranscriber с моделью {model_name} на {device}")
        self._load_model()
    
    def _load_model(self):
        """Загрузка модели Whisper через faster-whisper."""
        try:
            from faster_whisper import WhisperModel
            
            logger.info(f"Загрузка модели {self.model_name}...")
            
            # Определяем compute_type в зависимости от устройства
            if self.device == "cuda":
                compute_type = "float16"
            else:
                compute_type = "int8"
            
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=compute_type,
                download_root=None  # Использовать стандартный кеш
            )
            
            logger.info(f"Модель {self.model_name} успешно загружена на {self.device}")
            
            # Логирование использования GPU памяти
            if self.device == "cuda":
                self._log_gpu_memory()
                
        except ImportError:
            logger.error("faster-whisper не установлен. Установите: pip install faster-whisper")
            raise
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            raise
    
    def _log_gpu_memory(self):
        """Логирование использования GPU памяти."""
        try:
            import torch
            if torch.cuda.is_available():
                free_memory = torch.cuda.mem_get_info()[0]
                total_memory = torch.cuda.mem_get_info()[1]
                used_memory = total_memory - free_memory
                
                logger.info(f"GPU Memory после загрузки модели файлов:")
                logger.info(f"  Total: {total_memory / (1024**3):.1f} GB")
                logger.info(f"  Used: {used_memory / (1024**3):.1f} GB")
                logger.info(f"  Free: {free_memory / (1024**3):.1f} GB")
        except Exception as e:
            logger.warning(f"Не удалось получить информацию о GPU: {e}")
    
    def convert_audio_to_wav(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Конвертация аудио файла в WAV формат с параметрами для Whisper.
        
        Args:
            input_path: Путь к входному аудио файлу (MP3, WAV, и др.)
            output_path: Путь для выходного WAV файла (опционально)
            
        Returns:
            Путь к конвертированному WAV файлу
        """
        try:
            import librosa
            import soundfile as sf
            
            logger.info(f"Конвертация аудио: {input_path}")
            
            # Загружаем аудио с требуемым sample rate для Whisper (16kHz)
            audio, sr = librosa.load(input_path, sr=16000, mono=True)
            
            # Создаем временный файл если output_path не указан
            if output_path is None:
                temp_fd, output_path = tempfile.mkstemp(suffix='.wav')
                os.close(temp_fd)
            
            # Сохраняем в WAV формат
            sf.write(output_path, audio, 16000, subtype='PCM_16')
            
            duration = len(audio) / 16000
            logger.info(f"Аудио конвертировано: {duration:.2f} сек, sample_rate=16000Hz")
            
            return output_path
            
        except ImportError:
            logger.error("librosa или soundfile не установлены. Установите: pip install librosa soundfile")
            raise
        except Exception as e:
            logger.error(f"Ошибка конвертации аудио: {e}")
            raise
    
    def transcribe_file(
        self, 
        file_path: str,
        beam_size: int = 5,
        vad_filter: bool = False,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """
        Транскрипция аудио файла.
        
        Args:
            file_path: Путь к аудио файлу
            beam_size: Размер beam search (выше = лучше качество, медленнее)
            vad_filter: Использовать VAD фильтр для удаления тишины
            temperature: Температура для сэмплирования (0.0 = детерминированный)
            
        Returns:
            Словарь с результатами транскрипции:
            {
                "text": str,  # Полный текст
                "segments": List[Dict],  # Сегменты с временными метками
                "language": str,  # Определенный язык
                "duration": float  # Длительность аудио
            }
        """
        if not self.model:
            raise RuntimeError("Модель не загружена")
        
        try:
            logger.info(f"Начало транскрипции файла: {file_path}")
            
            # Конвертируем в WAV если это не WAV
            file_ext = Path(file_path).suffix.lower()
            if file_ext != '.wav':
                logger.info(f"Файл формата {file_ext}, требуется конвертация в WAV")
                wav_path = self.convert_audio_to_wav(file_path)
                cleanup_wav = True
            else:
                wav_path = file_path
                cleanup_wav = False
            
            try:
                # Выполняем транскрипцию
                segments, info = self.model.transcribe(
                    wav_path,
                    language=self.language,
                    beam_size=beam_size,
                    vad_filter=vad_filter,
                    temperature=temperature
                )
                
                # Собираем результаты
                full_text = []
                segments_list = []
                
                for segment in segments:
                    full_text.append(segment.text)
                    segments_list.append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text.strip()
                    })
                
                result = {
                    "text": " ".join(full_text).strip(),
                    "segments": segments_list,
                    "language": info.language if hasattr(info, 'language') else self.language,
                    "duration": info.duration if hasattr(info, 'duration') else 0.0
                }
                
                logger.info(f"Транскрипция завершена: {len(segments_list)} сегментов, "
                           f"{result['duration']:.2f} сек, язык: {result['language']}")
                
                return result
                
            finally:
                # Удаляем временный WAV файл если он был создан
                if cleanup_wav and os.path.exists(wav_path):
                    try:
                        os.unlink(wav_path)
                    except Exception as e:
                        logger.warning(f"Не удалось удалить временный файл {wav_path}: {e}")
        
        except Exception as e:
            logger.error(f"Ошибка транскрипции файла: {e}")
            raise
    
    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        file_extension: str = ".mp3",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Транскрипция аудио из байтов.
        
        Args:
            audio_bytes: Байты аудио файла
            file_extension: Расширение файла для определения формата
            **kwargs: Дополнительные параметры для transcribe_file
            
        Returns:
            Результат транскрипции (см. transcribe_file)
        """
        # Создаем временный файл
        temp_fd, temp_path = tempfile.mkstemp(suffix=file_extension)
        
        try:
            # Записываем байты в файл
            with os.fdopen(temp_fd, 'wb') as f:
                f.write(audio_bytes)
            
            # Выполняем транскрипцию
            result = self.transcribe_file(temp_path, **kwargs)
            
            return result
            
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный файл {temp_path}: {e}")
    
    def get_audio_duration(self, file_path: str) -> float:
        """
        Получение длительности аудио файла.
        
        Args:
            file_path: Путь к аудио файлу
            
        Returns:
            Длительность в секундах
        """
        try:
            import librosa
            duration = librosa.get_duration(path=file_path)
            return duration
        except Exception as e:
            logger.error(f"Ошибка получения длительности аудио: {e}")
            raise
    
    def validate_audio_file(
        self,
        file_path: str,
        max_size_mb: int = 500,
        max_duration_sec: int = 7200  # 2 часа
    ) -> Dict[str, Any]:
        """
        Валидация аудио файла перед транскрипцией.
        
        Args:
            file_path: Путь к файлу
            max_size_mb: Максимальный размер в MB
            max_duration_sec: Максимальная длительность в секундах
            
        Returns:
            Словарь с результатами валидации:
            {
                "valid": bool,
                "error": Optional[str],
                "file_size_mb": float,
                "duration_sec": float
            }
        """
        result = {
            "valid": True,
            "error": None,
            "file_size_mb": 0.0,
            "duration_sec": 0.0
        }
        
        try:
            # Проверяем существование файла
            if not os.path.exists(file_path):
                result["valid"] = False
                result["error"] = "Файл не найден"
                return result
            
            # Проверяем размер файла
            file_size_bytes = os.path.getsize(file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            result["file_size_mb"] = file_size_mb
            
            if file_size_mb > max_size_mb:
                result["valid"] = False
                result["error"] = f"Размер файла {file_size_mb:.1f}MB превышает лимит {max_size_mb}MB"
                return result
            
            # Проверяем длительность
            try:
                duration = self.get_audio_duration(file_path)
                result["duration_sec"] = duration
                
                if duration > max_duration_sec:
                    result["valid"] = False
                    result["error"] = f"Длительность {duration:.1f}сек превышает лимит {max_duration_sec}сек"
                    return result
                    
            except Exception as e:
                result["valid"] = False
                result["error"] = f"Не удалось определить длительность аудио: {str(e)}"
                return result
            
            logger.info(f"Валидация пройдена: {file_size_mb:.1f}MB, {duration:.1f}сек")
            return result
            
        except Exception as e:
            result["valid"] = False
            result["error"] = f"Ошибка валидации: {str(e)}"
            return result
