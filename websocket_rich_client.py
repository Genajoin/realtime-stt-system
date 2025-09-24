#!/usr/bin/env python3
"""
Rich клиент для WebSocket STT сервера.
Подключается к удаленному серверу через WebSocket и предоставляет 
красивый интерфейс для real-time транскрипции.
"""

import asyncio
import json
import sys
import time
import struct
from typing import Optional
import pyaudio
import websockets
import pyperclip
import argparse

from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table

class WebSocketSTTClient:
    def __init__(self, control_url: str = "ws://localhost:8011", 
                 data_url: str = "ws://localhost:8012"):
        """Инициализация WebSocket клиента."""
        self.control_url = control_url
        self.data_url = data_url
        
        # Rich интерфейс
        self.console = Console()
        self.live = Live(console=self.console, refresh_per_second=10, screen=False)
        
        # Состояние
        self.full_sentences = []
        self.current_text = ""
        self.displayed_text = ""
        self.is_recording = False
        
        # WebSocket соединения
        self.control_ws = None
        self.data_ws = None
        
        # Аудио настройки
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.audio_stream = None
        self.pyaudio_instance = None
        
    async def connect(self):
        """Подключение к WebSocket серверам."""
        try:
            self.control_ws = await websockets.connect(self.control_url)
            self.data_ws = await websockets.connect(self.data_url)
            self.console.print(f"[green]✓ Подключено к серверу[/green]")
            self.console.print(f"  Control: {self.control_url}")
            self.console.print(f"  Data: {self.data_url}")
            return True
        except Exception as e:
            self.console.print(f"[red]✗ Ошибка подключения: {e}[/red]")
            return False
    
    async def disconnect(self):
        """Отключение от WebSocket серверов."""
        if self.control_ws:
            await self.control_ws.close()
        if self.data_ws:
            await self.data_ws.close()
        self.console.print("[yellow]Отключен от сервера[/yellow]")
    
    def setup_audio(self):
        """Настройка аудио захвата с автоподбором параметров."""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # Список доступных устройств
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
                    self.console.print(f"[blue]Используется аудио устройство: {device_name}[/blue]")
                    break
            
            if input_device is None:
                raise Exception("Не найдено подходящее аудио устройство")
            
            # Пробуем разные sample rate до успешного подключения
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
                        self.console.print(f"[green]✓ Используется sample rate: {rate} Hz[/green]")
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
                self.console.print(f"[yellow]⚠ Используется default sample rate: {self.sample_rate} Hz[/yellow]")
            
            # Создаем аудио поток
            self.audio_stream = self.pyaudio_instance.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=input_device,
                frames_per_buffer=self.chunk_size
            )
            
            return True
        except Exception as e:
            self.console.print(f"[red]✗ Ошибка настройки аудио: {e}[/red]")
            return False
    
    def close_audio(self):
        """Закрытие аудио потока."""
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
    
    async def send_audio_chunk(self, audio_data):
        """Отправка аудио чанка на сервер."""
        if not self.data_ws:
            return
            
        # Подготавливаем метаданные
        metadata = {
            'sampleRate': self.sample_rate,
            'timestamp': time.time()
        }
        metadata_json = json.dumps(metadata).encode('utf-8')
        metadata_length = len(metadata_json)
        
        # Формируем сообщение: длина метаданных + метаданные + аудио
        message = struct.pack('<I', metadata_length) + metadata_json + audio_data
        
        try:
            await self.data_ws.send(message)
        except websockets.exceptions.ConnectionClosed:
            self.console.print("[red]Соединение с сервером потеряно[/red]")
    
    async def listen_for_responses(self):
        """Прослушивание ответов от сервера."""
        if not self.data_ws:
            return
            
        try:
            async for message in self.data_ws:
                if isinstance(message, str):
                    try:
                        data = json.loads(message)
                        msg_type = data.get('type')
                        
                        if msg_type == 'realtime':
                            self.current_text = data.get('text', '')
                            self.update_display()
                            
                        elif msg_type == 'fullSentence':
                            sentence = data.get('text', '')
                            if sentence.strip():
                                self.full_sentences.append(sentence)
                                self.current_text = ""
                                self.update_display()
                                
                                # Копируем в буфер обмена
                                try:
                                    pyperclip.copy(sentence)
                                except:
                                    pass
                                    
                        elif msg_type == 'recording_start':
                            self.is_recording = True
                            self.update_display()
                            
                        elif msg_type == 'recording_stop':
                            self.is_recording = False
                            self.update_display()
                            
                    except json.JSONDecodeError:
                        pass
                        
        except websockets.exceptions.ConnectionClosed:
            self.console.print("[red]Соединение с сервером потеряно[/red]")
    
    def update_display(self):
        """Обновление Rich интерфейса."""
        # Создаем Rich текст с предложениями
        rich_text = Text()
        
        # Отображаем завершенные предложения
        for i, sentence in enumerate(self.full_sentences):
            color = "green" if i % 2 == 0 else "cyan"
            rich_text += Text(sentence, style=color) + Text(" ")
        
        # Отображаем текущий текст
        if self.current_text:
            rich_text += Text(self.current_text, style="bold yellow")
        
        # Проверяем изменения
        new_displayed_text = rich_text.plain
        if new_displayed_text != self.displayed_text:
            self.displayed_text = new_displayed_text
            
            # Создаем layout
            layout = Layout()
            
            # Главная панель транскрипции
            main_content = rich_text if rich_text.plain.strip() else Text("Говорите в микрофон...", style="dim")
            main_panel = Panel(
                main_content,
                title="[bold green]📝 Real-time транскрипция (WebSocket клиент)[/bold green]",
                border_style="bold green",
                padding=(1, 2)
            )
            
            # Панель статуса
            status_table = Table.grid(padding=(0, 1))
            status_table.add_column()
            status_table.add_column()
            
            status_table.add_row("🌐 Сервер:", f"{self.control_url.replace('ws://', '')}")
            status_table.add_row("🎯 Статус:", "[green]●[/green] Записывается" if self.is_recording else "[yellow]●[/yellow] Ожидание")
            status_table.add_row("📊 Предложений:", str(len(self.full_sentences)))
            status_table.add_row("⌨️  Управление:", "Ctrl+C - выход")
            
            status_panel = Panel(
                status_table,
                title="[bold blue]ℹ️  Информация[/bold blue]",
                border_style="blue",
                padding=(0, 1)
            )
            
            # Компонуем layout
            layout.split_column(
                Layout(main_panel, size=None),
                Layout(status_panel, size=8)
            )
            
            self.live.update(layout)
    
    async def audio_capture_loop(self):
        """Основной цикл захвата аудио."""
        if not self.audio_stream:
            return
            
        try:
            while True:
                # Читаем аудио данные
                try:
                    audio_data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
                    await self.send_audio_chunk(audio_data)
                    
                    # Небольшая пауза чтобы не перегружать сервер
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    self.console.print(f"[red]Ошибка чтения аудио: {e}[/red]")
                    break
                    
        except asyncio.CancelledError:
            pass
    
    async def run(self):
        """Основной цикл работы клиента."""
        self.live.start()
        
        try:
            # Подключаемся к серверу
            if not await self.connect():
                return
            
            # Настраиваем аудио
            if not self.setup_audio():
                return
            
            # Показываем начальный интерфейс
            self.update_display()
            
            self.console.print("\n[bold green]🎙️  Клиент готов! Говорите в микрофон...[/bold green]")
            
            # Запускаем задачи
            audio_task = asyncio.create_task(self.audio_capture_loop())
            response_task = asyncio.create_task(self.listen_for_responses())
            
            # Ждем завершения
            await asyncio.gather(audio_task, response_task)
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Остановка по Ctrl+C...[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Ошибка: {e}[/red]")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Корректное завершение работы."""
        self.live.stop()
        
        # Показываем итоги
        if self.full_sentences:
            self.console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
            self.console.print("[bold green]📜 Полная транскрипция сессии:[/bold green]")
            self.console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]")
            
            full_text = ""
            for i, sentence in enumerate(self.full_sentences, 1):
                colored_text = f"[green]{sentence}[/green]" if i % 2 == 1 else f"[cyan]{sentence}[/cyan]"
                self.console.print(f"{i:2d}. {colored_text}")
                full_text += sentence + " "
            
            # Копируем весь текст в буфер
            try:
                pyperclip.copy(full_text.strip())
                self.console.print(f"\n[bold yellow]📋 Весь текст скопирован в буфер обмена![/bold yellow]")
            except:
                pass
            
            self.console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]")
        
        # Закрываем соединения
        self.close_audio()
        await self.disconnect()
        
        self.console.print("[bold green]✅ Клиент завершен[/bold green]")

def parse_args():
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(description='WebSocket STT клиент')
    parser.add_argument('--control-url', default='ws://localhost:8011',
                       help='URL для control WebSocket (default: ws://localhost:8011)')
    parser.add_argument('--data-url', default='ws://localhost:8012', 
                       help='URL для data WebSocket (default: ws://localhost:8012)')
    parser.add_argument('--server', help='IP адрес сервера (заменяет localhost в URLs)')
    
    return parser.parse_args()

async def main():
    """Главная функция."""
    args = parse_args()
    
    control_url = args.control_url
    data_url = args.data_url
    
    # Если указан сервер, заменяем localhost
    if args.server:
        control_url = control_url.replace('localhost', args.server)
        data_url = data_url.replace('localhost', args.server)
    
    client = WebSocketSTTClient(control_url, data_url)
    await client.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрограмма завершена")
        sys.exit(0)