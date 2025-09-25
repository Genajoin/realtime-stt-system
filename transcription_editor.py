#!/usr/bin/env python3
"""
GUI редактор для транскрибированного текста
Автоматически подключается к серверу и начинает запись
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import asyncio
import websockets
import json
import threading
import pyperclip
import os
import struct
import time
import pyaudio
import numpy as np
from typing import Optional
import logging

def load_env_file():
    """Загрузка переменных окружения из .env файла"""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

# Загружаем .env файл при импорте модуля
load_env_file()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptionEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Редактор транскрипции")
        self.root.geometry("800x600")
        
        # Загрузка конфигурации
        self.load_config()
        
        # WebSocket соединение
        self.control_ws = None
        self.data_ws = None
        self.is_connected = False
        
        # Аудио параметры
        self.sample_rate = 16000
        self.channels = 1
        self.audio_format = pyaudio.paInt16
        self.chunk_size = 1024
        self.audio_stream = None
        self.pyaudio_instance = None
        self.is_recording = False
        
        # Настройка интерфейса
        self.setup_ui()
        
        # Асинхронный цикл для WebSocket
        self.loop = None
        self.thread = None
        self.audio_thread = None
        
        # Автоматическое подключение при запуске
        self.root.after(1000, self.auto_connect)
    
    def load_config(self):
        """Загрузка конфигурации из переменных окружения"""
        self.server_host = os.getenv("SERVER_HOST", "localhost")
        self.control_port = int(os.getenv("CONTROL_PORT", "8011"))
        self.data_port = int(os.getenv("DATA_PORT", "8012"))
        
        logger.info(f"Конфигурация GUI: {self.server_host}:{self.control_port}/{self.data_port}")
        
    def setup_ui(self):
        """Создание пользовательского интерфейса"""
        # Главный контейнер
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Заголовок
        title_frame = tk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            title_frame, 
            text="Редактор транскрипции", 
            font=("Arial", 16, "bold")
        ).pack(side=tk.LEFT)
        
        # Статус подключения
        self.status_label = tk.Label(
            title_frame, 
            text="Подключается...", 
            font=("Arial", 12),
            fg="orange"
        )
        self.status_label.pack(side=tk.RIGHT)
        
        # Информация о сервере
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        server_info = f"Сервер: {self.server_host}:{self.control_port}/{self.data_port}"
        tk.Label(
            info_frame, 
            text=server_info, 
            font=("Arial", 10), 
            fg="gray"
        ).pack(side=tk.LEFT)
        
        # Кнопки управления
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.clear_btn = tk.Button(
            control_frame, 
            text="Очистить", 
            command=self.clear_text,
            bg="#f44336",
            fg="white",
            font=("Arial", 12, "bold"),
            width=12,
            height=2
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.copy_btn = tk.Button(
            control_frame, 
            text="Копировать в буфер", 
            command=self.copy_to_clipboard,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            width=20,
            height=2
        )
        self.copy_btn.pack(side=tk.LEFT)
        
        # Статусная панель для realtime текста
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            status_frame, 
            text="Статус распознавания:", 
            font=("Arial", 11, "bold")
        ).pack(anchor=tk.W, pady=(0, 2))
        
        self.status_text = tk.Text(
            status_frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            height=3,
            bg="#ffffcc",  # Желтый фон для промежуточного текста
            fg="#555555",
            relief="solid",
            borderwidth=1,
            state=tk.DISABLED  # Только для чтения
        )
        self.status_text.pack(fill=tk.X, pady=(0, 5))
        
        # Основное текстовое поле
        text_frame = tk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            text_frame, 
            text="Финальный текст (редактируемый):", 
            font=("Arial", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Arial", 12),
            height=15,  # Уменьшили высоту для статусной панели
            bg="#f8f9fa",
            relief="solid",
            borderwidth=1,
            undo=True  # Включаем функцию отмены
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Настраиваем горячие клавиши для основного текста
        self.text_area.bind('<Control-z>', lambda e: self.text_area.edit_undo())
        self.text_area.bind('<Control-y>', lambda e: self.text_area.edit_redo())
        self.text_area.bind('<Control-Z>', lambda e: self.text_area.edit_redo())  # Shift+Ctrl+Z
        
        # Подсказка
        tip_frame = tk.Frame(main_frame)
        tip_frame.pack(fill=tk.X, pady=(10, 0))
        
        tip_text = ("💡 Инструкция: Приложение автоматически подключится к серверу и начнет запись.\n"
                   "Желтая панель показывает процесс распознавания в реальном времени.\n"
                   "Финальный текст добавляется в основное поле и доступен для редактирования.\n"
                   "Горячие клавиши: Ctrl+Z - отмена, Ctrl+Y - повтор")
        
        tk.Label(
            tip_frame, 
            text=tip_text,
            font=("Arial", 9),
            fg="gray",
            wraplength=750,
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
    def auto_connect(self):
        """Автоматическое подключение к серверу при запуске"""
        logger.info("Автоматическое подключение к серверу...")
        self.connect_to_server()
    
    def connect_to_server(self):
        """Подключение к серверу WebSocket"""
        try:
            # Запуск асинхронного цикла в отдельном потоке
            self.thread = threading.Thread(target=self.start_async_loop, daemon=True)
            self.thread.start()
            
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")
            self.status_label.config(text=f"Ошибка: {e}", fg="red")
    
    def start_async_loop(self):
        """Запуск асинхронного цикла"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.websocket_handler())
    
    async def websocket_handler(self):
        """Обработчик WebSocket соединения"""
        control_uri = f"ws://{self.server_host}:{self.control_port}"
        data_uri = f"ws://{self.server_host}:{self.data_port}"
        
        logger.info(f"Подключение к: {control_uri} и {data_uri}")
        
        try:
            # Подключение к управляющему WebSocket
            self.control_ws = await websockets.connect(control_uri)
            self.is_connected = True
            
            # Обновление статуса в главном потоке
            self.root.after(0, lambda: self.status_label.config(
                text="Готов - запустите rich клиент", fg="green"
            ))
            
            # Подключение к потоку данных
            self.data_ws = await websockets.connect(data_uri)
            
            # Настройка и запуск аудио записи
            if self.setup_audio():
                self.start_audio_recording()
                logger.info("Аудио запись началась - можете говорить")
            else:
                logger.error("Не удалось настроить аудио")
            
            # Запуск обработчика данных
            await asyncio.gather(
                self.handle_control_messages(),
                self.handle_data_messages()
            )
            
        except Exception as e:
            logger.error(f"Ошибка WebSocket: {e}")
            self.root.after(0, lambda: self.status_label.config(
                text=f"Ошибка подключения: {e}", fg="red"
            ))
    
    async def handle_control_messages(self):
        """Обработка управляющих сообщений"""
        try:
            if self.control_ws:
                async for message in self.control_ws:
                    data = json.loads(message)
                    logger.info(f"Control message: {data}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Control connection closed")
            self.root.after(0, lambda: self.status_label.config(
                text="Соединение закрыто", fg="red"
            ))
    
    async def handle_data_messages(self):
        """Обработка сообщений с транскрибированным текстом"""
        try:
            if self.data_ws:
                async for message in self.data_ws:
                    try:
                        data = json.loads(message)
                        msg_type = data.get('type')
                        
                        if msg_type == 'realtime':
                            # Промежуточный текст - обновляем текущую строку
                            text = data.get('text', '').strip()
                            if text:
                                self.root.after(0, lambda t=text: self.update_realtime_text(t))
                                
                        elif msg_type == 'fullSentence':
                            # Финальное предложение - добавляем к тексту
                            text = data.get('text', '').strip()
                            if text:
                                self.root.after(0, lambda t=text: self.append_sentence(t))
                                
                        elif msg_type == 'transcription' and 'text' in data:
                            # Обратная совместимость
                            text = data['text'].strip()
                            if text:
                                self.root.after(0, lambda t=text: self.append_text(t))
                                
                    except json.JSONDecodeError:
                        logger.warning(f"Не удалось декодировать JSON: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Data connection closed")
    
    def append_text(self, text: str):
        """Добавление текста в текстовое поле (обратная совместимость)"""
        self.append_sentence(text)
    
    def update_realtime_text(self, text: str):
        """Обновление промежуточного (realtime) текста в статусной панели"""
        if text and text.strip():
            # Включаем редактирование, обновляем текст, отключаем
            self.status_text.config(state=tk.NORMAL)
            self.status_text.delete("1.0", tk.END)
            self.status_text.insert("1.0", f"🎤 Распознается: {text.strip()}")
            self.status_text.config(state=tk.DISABLED)
        else:
            # Очищаем статусную панель если нет текста
            self.status_text.config(state=tk.NORMAL)
            self.status_text.delete("1.0", tk.END)
            self.status_text.insert("1.0", "🔄 Ожидание речи...")
            self.status_text.config(state=tk.DISABLED)
    
    def append_sentence(self, text: str):
        """Добавление финального предложения с сохранением позиции курсора"""
        if not text.strip():
            return
            
        # Сохраняем текущую позицию курсора
        try:
            cursor_pos = self.text_area.index(tk.INSERT)
        except tk.TclError:
            cursor_pos = "1.0"
        
        # Получаем текущий текст
        current_text = self.text_area.get("1.0", tk.END).strip()
        
        # Добавляем новое предложение
        if current_text:
            # Вставляем в конец с пробелом
            self.text_area.insert(tk.END, " " + text.strip())
        else:
            # Первое предложение
            self.text_area.insert(tk.END, text.strip())
        
        # Восстанавливаем позицию курсора если она была в пределах старого текста
        try:
            self.text_area.mark_set(tk.INSERT, cursor_pos)
        except tk.TclError:
            # Если позиция стала невалидной, ставим в конец
            self.text_area.mark_set(tk.INSERT, tk.END)
        
        # Показываем место вставки
        self.text_area.see(tk.END)
        
        # Очищаем статусную панель
        self.update_realtime_text("")
        
        logger.info(f"Добавлено предложение: {text.strip()}")
    
    def copy_to_clipboard(self):
        """Копирование текста в буфер обмена"""
        text = self.text_area.get("1.0", tk.END).strip()
        if text:
            pyperclip.copy(text)
            # Временное изменение текста кнопки для обратной связи
            original_text = self.copy_btn.config('text')[-1]
            self.copy_btn.config(text="Скопировано!", bg="#2E7D32")
            self.root.after(1500, lambda: self.copy_btn.config(
                text=original_text, bg="#4CAF50"
            ))
        else:
            messagebox.showwarning("Предупреждение", "Нет текста для копирования")
    
    def clear_text(self):
        """Очистка текстового поля"""
        result = messagebox.askyesno(
            "Подтверждение", 
            "Вы уверены, что хотите очистить весь текст?\n\nЭто начнет новый разговор."
        )
        if result:
            self.text_area.delete("1.0", tk.END)
            logger.info("Текст очищен - начинается новый разговор")
    
    def setup_audio(self):
        """Настройка аудио захвата с автоподбором параметров"""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # Поиск подходящего аудио устройства
            info = self.pyaudio_instance.get_host_api_info_by_index(0)
            num_devices = info.get('deviceCount', 0)
            
            input_device = None
            device_info = None
            for i in range(int(num_devices)):
                device_info = self.pyaudio_instance.get_device_info_by_host_api_device_index(0, i)
                max_input_channels = device_info.get('maxInputChannels', 0)
                if isinstance(max_input_channels, (int, float)) and max_input_channels > 0:
                    input_device = i
                    device_name = device_info.get('name', 'Unknown')
                    logger.info(f"Используется аудио устройство: {device_name}")
                    break
            
            if input_device is None:
                raise Exception("Не найдено подходящее аудио устройство")
            
            # Автоподбор sample rate
            sample_rates = [16000, 44100, 48000, 22050, 8000]
            
            for rate in sample_rates:
                try:
                    # Проверяем поддержку sample rate для устройства
                    if self.pyaudio_instance.is_format_supported(
                        rate=rate,
                        input_device=input_device,
                        input_channels=self.channels,
                        input_format=self.audio_format
                    ):
                        self.sample_rate = rate
                        logger.info(f"Используется sample rate: {rate} Hz")
                        break
                except:
                    continue
            else:
                # Если не удалось найти поддерживаемый rate, используем default
                if device_info:
                    default_rate = device_info.get('defaultSampleRate', 16000)
                    self.sample_rate = int(default_rate)
                else:
                    self.sample_rate = 16000
                logger.info(f"Используется default sample rate: {self.sample_rate} Hz")
            
            # Создание аудио потока
            self.audio_stream = self.pyaudio_instance.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=input_device,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info(f"Аудио настроено: {self.sample_rate} Hz, {self.channels} каналов")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка настройки аудио: {e}")
            return False
    
    def start_audio_recording(self):
        """Запуск аудио записи в отдельном потоке"""
        if not self.audio_stream:
            return
        
        self.is_recording = True
        self.audio_thread = threading.Thread(target=self.audio_recording_loop, daemon=True)
        self.audio_thread.start()
        
        # Обновление статуса
        self.root.after(0, lambda: self.status_label.config(
            text="Записываю - говорите", fg="green"
        ))
    
    def audio_recording_loop(self):
        """Цикл записи аудио и отправки на сервер"""
        retry_count = 0
        max_retries = 3
        
        while self.is_recording and self.audio_stream and self.data_ws and retry_count < max_retries:
            try:
                # Чтение аудио данных с обработкой переполнения
                audio_data = self.audio_stream.read(
                    self.chunk_size, 
                    exception_on_overflow=False
                )
                
                # Отправка на сервер через asyncio
                if self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.send_audio_chunk(audio_data), 
                        self.loop
                    )
                
                # Сброс счетчика при успешной записи
                retry_count = 0
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"Ошибка записи аудио (попытка {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    logger.error("Превышено максимальное количество попыток записи")
                    # Обновление статуса в GUI
                    self.root.after(0, lambda: self.status_label.config(
                        text="Ошибка записи аудио", fg="red"
                    ))
                    break
                else:
                    # Небольшая пауза перед повторной попыткой
                    import time
                    time.sleep(0.1)
    
    async def send_audio_chunk(self, audio_data):
        """Отправка аудио чанка на сервер"""
        if not self.data_ws:
            return
        
        # Подготовка метаданных
        metadata = {
            'sampleRate': self.sample_rate,
            'timestamp': time.time()
        }
        metadata_json = json.dumps(metadata).encode('utf-8')
        metadata_length = len(metadata_json)
        
        # Формирование сообщения: длина метаданных + метаданные + аудио
        message = struct.pack('<I', metadata_length) + metadata_json + audio_data
        
        try:
            await self.data_ws.send(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Соединение закрыто во время отправки аудио")
    
    def close_audio(self):
        """Закрытие аудио потока"""
        self.is_recording = False
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        logger.info("Закрытие приложения...")
        
        # Остановка аудио записи
        self.close_audio()
        
        # Отключение от сервера
        if self.is_connected:
            logger.info("Отключение от сервера...")
            try:
                if self.control_ws and self.loop:
                    asyncio.run_coroutine_threadsafe(self.control_ws.close(), self.loop)
                if self.data_ws and self.loop:
                    asyncio.run_coroutine_threadsafe(self.data_ws.close(), self.loop)
            except:
                pass
        
        self.root.destroy()

def main():
    root = tk.Tk()
    app = TranscriptionEditor(root)
    
    # Обработка закрытия окна
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()