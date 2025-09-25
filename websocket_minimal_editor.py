#!/usr/bin/env python3
"""
Минималистичный терминальный STT редактор.

Легковесное приложение для работы с распознаванием речи в минимальных окнах терминала.
Создано на основе prompt_toolkit без лишних элементов интерфейса.

Особенности:
- БЕЗ БОРДЮРОВ для чистого копирования
- Поддержка мыши для выделения и позиционирования
- Автоматическое копирование в буфер обмена
- WebSocket интеграция с STT сервером
- Оптимизировано для маленьких терминальных окон
"""

import asyncio
import json
import os
import sys
import time
import struct
import contextlib
from typing import Optional, Callable, List, Tuple
from datetime import datetime

# Основные зависимости
try:
    import pyperclip
    import websockets
    import pyaudio
    import struct
except ImportError as e:
    print(f"Ошибка импорта зависимостей: {e}")
    print("Установите зависимости: pip install pyperclip websockets pyaudio")
    sys.exit(1)

# prompt_toolkit компоненты
try:
    from prompt_toolkit import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import HSplit, VSplit, Window, Float, ConditionalContainer
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.styles import Style
    from prompt_toolkit.formatted_text import FormattedText
    from prompt_toolkit.application import get_app
    from prompt_toolkit.clipboard import ClipboardData
    from prompt_toolkit.widgets import Box, Label
    from prompt_toolkit.filters import Condition
except ImportError as e:
    print(f"Ошибка импорта prompt_toolkit: {e}")
    print("Установите prompt_toolkit: pip install prompt_toolkit")
    sys.exit(1)


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


# Загружаем переменные окружения
load_env_file()


class ClipboardManager:
    """Менеджер для работы с системным буфером обмена"""

    @staticmethod
    def copy_text(text: str) -> bool:
        """Копирование текста в системный буфер обмена"""
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            print(f"Ошибка копирования в буфер: {e}")
            return False

    @staticmethod
    def get_text() -> str:
        """Получение текста из буфера обмена"""
        try:
            return pyperclip.paste()
        except Exception:
            return ""


class StatusBar:
    """Минимальная статус строка"""

    def __init__(self, editor):
        self.editor = editor
        self.last_copy_time = 0

    def get_left_status(self) -> FormattedText:
        """Левая часть статус бара: индикатор + F1:Help"""
        items = []

        # Индикатор состояния STT
        stt_client = getattr(self.editor, 'stt_client', None)
        if stt_client and stt_client.is_connected:
            if getattr(self.editor, 'current_text', '') and self.editor.current_text.strip():
                # Красный: идет активное распознавание
                items.append(('class:status-recording', '[●] '))
            elif getattr(stt_client, 'is_paused', False):
                # Оранжевый: на паузе
                items.append(('class:status-paused', '[●] '))
            elif stt_client.is_recording:
                # Зеленый: мониторит голос
                items.append(('class:status-monitoring', '[●] '))
            else:
                # Серый: подключен, но не записывает
                items.append(('class:status-idle', '[●] '))
        else:
            # Серый: не подключен
            items.append(('class:status-idle', '[●] '))

        # F1:Help + индикатор копирования
        items.append(('', 'F1:Help'))

        # Индикатор копирования
        current_time = time.time()
        if current_time - self.last_copy_time < 1.5:
            items.append(('class:status-success', ' ✓'))

        return FormattedText(items)

    def get_right_status(self) -> FormattedText:
        """Правая часть статус бара: состояние STT"""
        items = []

        stt_client = getattr(self.editor, 'stt_client', None)
        if stt_client and stt_client.is_connected:
            if getattr(self.editor, 'current_text', '') and self.editor.current_text.strip():
                items.append(('class:status-recording', 'Recognizing'))
            elif getattr(stt_client, 'is_paused', False):
                items.append(('class:status-paused', 'Paused'))
            elif stt_client.is_recording:
                items.append(('class:status-connected', 'Listening'))
            else:
                items.append(('class:status-connected', 'Ready'))
        else:
            items.append(('class:status-disconnected', 'Offline'))

        return FormattedText(items)

    def show_copy_indicator(self):
        """Показать индикатор копирования"""
        self.last_copy_time = time.time()


class WebSocketSTTClient:
    """Асинхронный WebSocket клиент для STT сервера"""

    def __init__(self, editor):
        self.editor = editor
        self.control_url = os.getenv('CONTROL_URL', 'ws://genaminipc.awg:8011')
        self.data_url = os.getenv('DATA_URL', 'ws://genaminipc.awg:8012')

        # WebSocket соединения
        self.control_ws = None
        self.data_ws = None
        self.is_connected = False

        # Аудио настройки
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.audio_stream = None
        self.pyaudio_instance = None

        # Состояние
        self.is_recording = False
        self.is_paused = False  # Состояние паузы записи
        self.should_exit = False

    @contextlib.contextmanager
    def suppress_alsa_warnings(self):
        """Подавление ALSA warnings"""
        try:
            # Подавляем ALSA error output
            with open(os.devnull, 'w') as devnull:
                old_stderr = os.dup(2)
                os.dup2(devnull.fileno(), 2)
                try:
                    yield
                finally:
                    os.dup2(old_stderr, 2)
                    os.close(old_stderr)
        except Exception:
            yield

    async def connect(self):
        """Подключение к WebSocket серверам"""
        try:
            # Подключение к control каналу
            self.control_ws = await websockets.connect(
                self.control_url,
                ping_interval=None,
                close_timeout=1
            )

            # Подключение к data каналу
            self.data_ws = await websockets.connect(
                self.data_url,
                ping_interval=None,
                close_timeout=1
            )

            self.is_connected = True

            # Запуск обработчика сообщений
            asyncio.create_task(self.message_handler())

            # Автоматический старт записи после подключения
            await self.start_recording()

        except Exception as e:
            self.is_connected = False
            raise e

    async def disconnect(self):
        """Отключение от WebSocket серверов"""
        self.should_exit = True
        self.is_connected = False

        if self.control_ws:
            await self.control_ws.close()
        if self.data_ws:
            await self.data_ws.close()

        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()

    async def start_recording(self):
        """Начало записи аудио"""
        if not self.is_connected:
            return

        try:
            # Инициализация PyAudio с подавлением ALSA warnings
            with self.suppress_alsa_warnings():
                self.pyaudio_instance = pyaudio.PyAudio()
                self.audio_stream = self.pyaudio_instance.open(
                    format=self.audio_format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=self.chunk_size
                )

            self.is_recording = True

            # Отправка команды начала записи
            await self.control_ws.send(json.dumps({
                "action": "start_recording",
                "config": {
                    "sample_rate": self.sample_rate,
                    "channels": self.channels
                }
            }))

            # Запуск захвата аудио
            asyncio.create_task(self.audio_capture_task())

        except Exception as e:
            self.is_recording = False

    async def stop_recording(self):
        """Остановка записи аудио"""
        if not self.is_recording:
            return

        self.is_recording = False

        try:
            # Остановка аудио потока с подавлением ALSA warnings
            with self.suppress_alsa_warnings():
                if self.audio_stream:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                    self.audio_stream = None

                if self.pyaudio_instance:
                    self.pyaudio_instance.terminate()
                    self.pyaudio_instance = None

            # Отправка команды остановки
            if self.control_ws:
                await self.control_ws.send(json.dumps({
                    "action": "stop_recording"
                }))

        except Exception:
            pass

    async def pause_recording(self):
        """Пауза записи аудио"""
        if not self.is_recording or self.is_paused:
            return

        self.is_paused = True
        try:
            # Отправка команды паузы
            if self.control_ws:
                await self.control_ws.send(json.dumps({
                    "action": "pause_recording"
                }))
        except Exception:
            pass

    async def resume_recording(self):
        """Возобновление записи аудио"""
        if not self.is_recording or not self.is_paused:
            return

        self.is_paused = False
        try:
            # Отправка команды возобновления
            if self.control_ws:
                await self.control_ws.send(json.dumps({
                    "action": "resume_recording"
                }))
        except Exception:
            pass

    async def audio_capture_task(self):
        """Задача захвата аудио данных"""
        while self.is_recording and self.audio_stream:
            try:
                # Чтение аудио данных
                audio_data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)

                # Отправка на сервер только если не на паузе
                if not self.is_paused:
                    await self.send_audio_chunk(audio_data)

                await asyncio.sleep(0.01)  # Небольшая пауза

            except Exception as e:
                print(f"Ошибка захвата аудио: {e}")
                break

    async def send_audio_chunk(self, audio_data):
        """Отправка аудио чанка на сервер с метаданными."""
        if not self.data_ws:
            return

        try:
            # Подготовка метаданных
            metadata = {
                'sampleRate': self.sample_rate,
                'timestamp': time.time()
            }
            metadata_json = json.dumps(metadata).encode('utf-8')
            metadata_length = len(metadata_json)

            # Создание сообщения: [length][metadata][audio_data]
            message = struct.pack('<I', metadata_length) + metadata_json + audio_data

            # Отправка на сервер
            await self.data_ws.send(message)

        except Exception:
            pass

    async def message_handler(self):
        """Обработчик сообщений от STT сервера"""
        try:
            async for message in self.data_ws:
                if isinstance(message, str):
                    try:
                        data = json.loads(message)
                        msg_type = data.get('type')

                        if msg_type == 'realtime':
                            # Real-time предварительный текст
                            realtime_text = data.get('text', '')
                            await self.editor.on_realtime_text_received(realtime_text)

                        elif msg_type == 'fullSentence':
                            # Финальное предложение
                            text = data.get('text', '')
                            if text.strip():
                                # Передача финального текста в редактор
                                await self.editor.on_stt_text_received(text, is_final=True)
                            else:
                                # Очищаем realtime текст даже если финальный пустой
                                await self.editor.on_realtime_text_received("")

                        elif msg_type == 'recording_start':
                            self.is_recording = True

                        elif msg_type == 'recording_stop':
                            self.is_recording = False

                    except json.JSONDecodeError:
                        pass

        except Exception:
            pass


class MinimalSTTEditor:
    """Основной класс минималистичного STT редактора"""

    def __init__(self):
        # Основной текстовый буфер
        self.buffer = Buffer(multiline=True)

        # Отслеживание предыдущего состояния выделения для автокопирования
        self.last_selection_hash = None

        # Менеджеры
        self.clipboard_manager = ClipboardManager()
        self.status_bar = StatusBar(self)
        self.stt_client = WebSocketSTTClient(self)

        # Состояние сейчас хранится только в stt_client
        # Промежуточные данные для отображения realtime текста
        self.current_text = ""  # Промежуточный текст от STT
        self.realtime_start_pos = None  # Позиция начала realtime текста в буфере

        # Состояние справки
        self.show_help = False

        # UI компоненты
        self.buffer_control = BufferControl(
            buffer=self.buffer,
            focusable=True,
            include_default_input_processors=True
        )

        # Главное окно редактора БЕЗ РАМОК
        self.editor_window = Window(
            content=self.buffer_control,
            wrap_lines=True,
            dont_extend_width=False,
            dont_extend_height=False
        )

        # Статус бар с разделением на левую и правую части
        self.status_window = VSplit([
            # Левая часть: индикатор + F1:Help
            Window(
                content=FormattedTextControl(
                    lambda: self.status_bar.get_left_status()
                ),
                dont_extend_width=True
            ),
            # Центр: пустое пространство (расширяется)
            Window(char=' '),
            # Правая часть: статус STT
            Window(
                content=FormattedTextControl(
                    lambda: self.status_bar.get_right_status()
                ),
                dont_extend_width=True
            ),
        ], height=1)

        # Layout: редактор + статус бар (пока без справки)
        self.layout = Layout(
            HSplit([
                # Окно справки (сверху если показана)
                ConditionalContainer(
                    content=self.create_help_window(),
                    filter=Condition(lambda: self.show_help)
                ),
                # Главная область (расширяется)
                self.editor_window,
                # Статус бар (1 строка)
                self.status_window
            ])
        )

        # Стили
        self.style = Style.from_dict({
            # Статус бар
            'status-recording': '#ff0000 bold',             # Красный: голос обнаружен, STT работает
            'status-monitoring': '#00ff00 bold',            # Зеленый: мониторинг голоса
            'status-paused': '#ffaa00 bold',                # Оранжевый: на паузе
            'status-idle': '#666666',                       # Серый: неактивен
            'status-connected': 'bg:#008800 #ffffff',       # Зеленый фон при подключении
            'status-disconnected': 'bg:#880000 #ffffff',    # Красный фон при отключении
            'status-success': 'bg:#008800 #ffffff bold',    # Зеленый для success
            # Справка
            'help-box': 'bg:#ffffff #000000',               # Белый фон для справки
            'help-title': '#0066cc bold',                   # Синий заголовок
            'help-section': '#006600 bold',                 # Зеленый заголовок секции
            'help-key': '#cc6600 bold',                     # Оранжевые клавиши
        })

        # Приложение
        self.app = Application(
            layout=self.layout,
            key_bindings=self.create_key_bindings(),
            style=self.style,
            full_screen=True,
            mouse_support=True,  # Поддержка мыши
            refresh_interval=0.1,  # Увеличили частоту для лучшего отслеживания выделения
            on_invalidate=self.on_app_invalidate  # Обработчик обновлений
        )

    def create_key_bindings(self) -> KeyBindings:
        """Создание клавиатурных привязок"""
        kb = KeyBindings()

        # F1 - Показать/скрыть справку
        @kb.add('f1')
        def toggle_help(event):
            self.show_help = not self.show_help
            event.app.invalidate()

        # ESC - Скрыть справку
        @kb.add('escape')
        def hide_help(event):
            if self.show_help:
                self.show_help = False
                event.app.invalidate()

        # F5 - Переключить паузу/возобновление STT
        @kb.add('f5')
        def toggle_pause(event):
            asyncio.create_task(self.toggle_recording_pause())

        # F3 - Копировать весь текст
        @kb.add('f3')
        def copy_all_text(event):
            text = self.buffer.text
            if text.strip():
                if self.clipboard_manager.copy_text(text):
                    self.status_bar.show_copy_indicator()

        # F8 - Очистить весь текст
        @kb.add('f8')
        def clear_all_text(event):
            self.buffer.text = ''

        # Ctrl+C - Выход из приложения
        @kb.add('c-c')
        def exit_editor_ctrl_c(event):
            event.app.exit()

        # Ctrl+A - Выделить все
        @kb.add('c-a')
        def select_all(event):
            self.buffer.select_all()

        # Ctrl+Q - Выход
        @kb.add('c-q')
        def exit_editor(event):
            event.app.exit()


        return kb

    def create_help_window(self):
        """Создание окна справки"""
        help_text = FormattedText([
            ('class:help-title', '╔═══════════════════════════════════\n'),
            ('class:help-title', '║    STT Минимальный Редактор    ║\n'),
            ('class:help-title', '╚═══════════════════════════════════\n\n'),
            ('class:help-section', 'Индикаторы состояния:\n'),
            ('class:status-monitoring', '  ● Зеленый'),
            ('', ' - мониторинг голоса\n'),
            ('class:status-recording', '  ● Красный'),
            ('', ' - активное распознавание\n'),
            ('class:status-paused', '  ● Оранжевый'),
            ('', ' - пауза\n'),
            ('class:status-idle', '  ● Серый'),
            ('', ' - отключен/неактивен\n\n'),
            ('class:help-section', 'Горячие клавиши:\n'),
            ('class:help-key', '  F1'),
            ('', ' - показать/скрыть справку\n'),
            ('class:help-key', '  F5'),
            ('', ' - пауза/возобновление STT\n'),
            ('class:help-key', '  F3'),
            ('', ' - копировать весь текст\n'),
            ('class:help-key', '  F8'),
            ('', ' - очистить все\n'),
            ('class:help-key', '  Ctrl+A'),
            ('', ' - выделить все\n'),
            ('class:help-key', '  ESC'),
            ('', ' - закрыть справку\n\n'),
            ('class:help-section', 'Особенности:\n'),
            ('', '  • Автоматический старт записи\n'),
            ('', '  • Автокопирование текста\n'),
            ('', '  • Поддержка мыши\n'),
            ('', '  • Real-time превью')
        ])

        return Window(
            content=FormattedTextControl(lambda: help_text),
            width=40,
            height=20,
            style='class:help-box'
        )

    def on_app_invalidate(self, sender=None):
        """Обработчик обновления приложения - проверяем изменения в выделении"""
        self.check_selection_change()

    def check_selection_change(self):
        """Проверка изменений в выделении и автокопирование"""
        if self.buffer.selection_state:
            # Есть выделение
            selected_text = self.buffer.copy_selection()
            if selected_text and selected_text.text.strip():
                # Вычисляем хеш выделенного текста
                selection_hash = hash(selected_text.text.strip())

                # Если выделение изменилось, копируем в буфер
                if self.last_selection_hash != selection_hash:
                    if self.clipboard_manager.copy_text(selected_text.text):
                        self.status_bar.show_copy_indicator()
                    self.last_selection_hash = selection_hash
        else:
            # Нет выделения - сбрасываем хеш
            self.last_selection_hash = None

    async def toggle_recording_pause(self):
        """Переключение паузы/возобновления STT записи"""
        try:
            if not self.stt_client.is_recording:
                # Если запись вообще не начата, начинаем
                await self.stt_client.start_recording()
            elif self.stt_client.is_paused:
                # Возобновляем запись
                await self.stt_client.resume_recording()
            else:
                # Ставим на паузу
                await self.stt_client.pause_recording()
        except Exception:
            pass

    async def on_realtime_text_received(self, text: str):
        """Обработка промежуточного realtime текста"""
        if text != self.current_text:
            # Убираем старый realtime текст если есть
            self.remove_realtime_text()

            # Обновляем текущий текст
            self.current_text = text.strip()

            # Добавляем новый realtime текст если он не пустой
            if self.current_text:
                self.add_realtime_text(self.current_text)

            # Обновляем интерфейс
            self.app.invalidate()

    async def on_stt_text_received(self, text: str, is_final: bool):
        """Обработка текста от STT сервера"""
        if is_final and text.strip():
            # Убираем realtime текст перед вставкой финального
            self.remove_realtime_text()
            self.current_text = ""

            # Вставка финального текста в позицию курсора
            self.insert_text_at_cursor(text)

            # Автоматическое копирование в буфер обмена
            if self.clipboard_manager.copy_text(text):
                self.status_bar.show_copy_indicator()

            # Принудительная перерисовка буфера
            self.app.invalidate()

    def add_realtime_text(self, text: str):
        """Добавление промежуточного текста"""
        if text.strip():
            # Запоминаем позицию начала realtime текста
            self.realtime_start_pos = self.buffer.cursor_position

            # Добавляем пробел перед текстом если нужно
            current_line = self.buffer.document.current_line_before_cursor
            if current_line and not current_line.endswith(' '):
                text = ' ' + text

            # Вставляем текст
            self.buffer.insert_text(text)

    def remove_realtime_text(self):
        """Удаление промежуточного текста"""
        if self.realtime_start_pos is not None and self.current_text:
            # Вычисляем количество символов для удаления
            current_pos = self.buffer.cursor_position
            chars_to_delete = current_pos - self.realtime_start_pos

            if chars_to_delete > 0:
                # Перемещаем курсор назад и удаляем символы
                self.buffer.cursor_position = self.realtime_start_pos
                for _ in range(chars_to_delete):
                    self.buffer.delete()

            self.realtime_start_pos = None

    def insert_text_at_cursor(self, text: str):
        """Вставка текста в текущую позицию курсора"""
        # Добавляем пробел перед текстом если курсор не в начале строки
        current_line = self.buffer.document.current_line_before_cursor
        if current_line and not current_line.endswith(' '):
            text = ' ' + text

        # Вставляем текст
        self.buffer.insert_text(text)

    async def initialize(self):
        """Инициализация редактора"""
        # Попытка подключения к STT серверу (необязательно)
        try:
            await self.stt_client.connect()
            connection_status = "✓ STT сервер подключен"
        except Exception:
            connection_status = "⚠ STT сервер недоступен (работа только как редактор)"

        # Вывод только в тестовом режиме
        if hasattr(self, '_initialization_output') and self._initialization_output:
            print("Минималистичный STT Редактор")
            print("============================")
            print(connection_status)
            print("\nГорячие клавиши:")
            print("F5 - Пауза/возобновление STT (запись начинается автоматически)")
            print("F3 - Копировать весь текст")
            print("Ctrl+C - Выход")
            print("Ctrl+A - Выделить все")
            print("F8 - Очистить весь текст")
            print("Ctrl+Q - Выход (альтернативный)")
            print("\nИндикаторы состояния:")
            print("● Зеленый - мониторинг голоса")
            print("● Красный - активное распознавание")
            print("● Оранжевый - пауза")
            print("\nАвтоматическое копирование:")
            print("- Распознанные предложения")
            print("- Выделенный мышью текст")
            print("\nРедактор готов к работе! Запись начнется автоматически.")

    async def cleanup(self):
        """Очистка ресурсов"""
        await self.stt_client.disconnect()

    async def run(self):
        """Запуск редактора"""
        try:
            await self.initialize()
            await self.app.run_async()
        finally:
            await self.cleanup()


async def main():
    """Главная функция"""
    import argparse

    parser = argparse.ArgumentParser(description="Минималистичный STT редактор")
    parser.add_argument('--test', action='store_true', help='Тестовый режим (показать интерфейс и выйти)')
    args = parser.parse_args()

    editor = MinimalSTTEditor()

    if args.test:
        # Тестовый режим - включаем вывод
        editor._initialization_output = True
        await editor.initialize()
        print("\n✓ Редактор инициализирован успешно")
        print("✓ Интерфейс создан корректно")
        print("✓ Все компоненты готовы")
        print("\nЗапустите без --test для полной работы")
        await editor.cleanup()
    else:
        # Обычный режим - выключаем вывод во время работы
        editor._initialization_output = False
        await editor.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nВыход из редактора...")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)