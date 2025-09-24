#!/usr/bin/env python3
"""
Улучшенное демо-приложение для распознавания речи в реальном времени.
Использует Rich для красивого интерфейса с автообновляющимися панелями.
Основано на примере из RealtimeSTT.
"""

import os
import sys
from RealtimeSTT import AudioToTextRecorder
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout
import pyperclip  # для копирования в буфер обмена

class RichSTTDemo:
    def __init__(self):
        """Инициализация приложения с Rich интерфейсом."""
        # Инициализация Rich консоли
        self.console = Console()
        self.live = Live(console=self.console, refresh_per_second=10, screen=False)
        
        # Состояние приложения
        self.full_sentences = []
        self.displayed_text = ""
        self.prev_text = ""
        self.current_text = ""
        
        # Настройки определения пауз (как в оригинале)
        self.end_of_sentence_detection_pause = 0.45
        self.unknown_sentence_detection_pause = 0.7
        self.mid_sentence_detection_pause = 2.0
        
        self.console.print("[bold blue]🚀 Инициализация системы распознавания речи...[/bold blue]")
        
        # Создаем рекордер с оптимальными настройками для русского языка
        self.recorder_config = {
            'model': 'small',  # Баланс скорости и качества
            'language': 'ru',  # Русский язык (поддерживает английские термины)
            'realtime_model_type': 'tiny',  # Быстрая модель для real-time
            'compute_type': 'default',
            'device': 'cuda' if self.check_cuda() else 'cpu',
            
            # Real-time настройки
            'enable_realtime_transcription': True,
            'realtime_processing_pause': 0.02,  # Быстрое обновление
            'on_realtime_transcription_update': self.on_realtime_update,
            
            # VAD настройки
            'silero_sensitivity': 0.05,
            'webrtc_sensitivity': 3,
            'post_speech_silence_duration': self.unknown_sentence_detection_pause,
            'min_length_of_recording': 1.1,
            'min_gap_between_recordings': 0,
            'silero_deactivity_detection': True,
            'silero_use_onnx': True,
            
            # Улучшение качества
            'beam_size': 5,
            'beam_size_realtime': 3,
            'early_transcription_on_silence': 0,
            
            # Промпт для лучшего распознавания (адаптированный для русского)
            'initial_prompt_realtime': (
                "Завершай незаконченные предложения многоточием.\n"
                "Примеры:\n"
                "Законченное: Я программист на Python.\n"
                "Незаконченное: Когда я пишу код на...\n"
                "Законченное: Функция возвращает результат.\n"
                "Незаконченное: Потому что API...\n"
            ),
            
            # Отключаем лишние выводы
            'spinner': False,
            'no_log_file': True,
            'debug_mode': False
        }
        
        try:
            self.recorder = AudioToTextRecorder(**self.recorder_config)
            self.console.print(f"[bold green]✓ Модель загружена ({self.recorder_config['device'].upper()})[/bold green]")
        except Exception as e:
            self.console.print(f"[bold red]✗ Ошибка инициализации: {e}[/bold red]")
            sys.exit(1)
    
    def check_cuda(self):
        """Проверка доступности CUDA."""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def preprocess_text(self, text):
        """Предобработка текста (как в оригинале)."""
        # Убираем пробелы в начале
        text = text.lstrip()
        
        # Убираем начальные многоточия
        if text.startswith("..."):
            text = text[3:]
        
        # Снова убираем пробелы
        text = text.lstrip()
        
        # Делаем первую букву заглавной
        if text:
            text = text[0].upper() + text[1:]
        
        return text
    
    def on_realtime_update(self, text):
        """Обработка обновлений в реальном времени."""
        global recorder
        text = self.preprocess_text(text)
        self.current_text = text
        
        # Динамическое определение пауз на основе содержимого
        sentence_end_marks = ['.', '!', '?', '。']
        if text.endswith("..."):
            self.recorder.post_speech_silence_duration = self.mid_sentence_detection_pause
        elif text and text[-1] in sentence_end_marks and self.prev_text and self.prev_text[-1] in sentence_end_marks:
            self.recorder.post_speech_silence_duration = self.end_of_sentence_detection_pause
        else:
            self.recorder.post_speech_silence_duration = self.unknown_sentence_detection_pause
        
        self.prev_text = text
        self.update_display()
    
    def update_display(self):
        """Обновление отображения в Rich интерфейсе."""
        # Создаем Rich текст с чередующимися цветами для предложений
        rich_text = Text()
        
        # Отображаем завершенные предложения
        for i, sentence in enumerate(self.full_sentences):
            if i % 2 == 0:
                rich_text += Text(sentence, style="green") + Text(" ")
            else:
                rich_text += Text(sentence, style="cyan") + Text(" ")
        
        # Отображаем текущий текст (в процессе распознавания)
        if self.current_text:
            rich_text += Text(self.current_text, style="bold yellow")
        
        # Проверяем, изменился ли текст для отображения
        new_displayed_text = rich_text.plain
        if new_displayed_text != self.displayed_text:
            self.displayed_text = new_displayed_text
            
            # Создаем панель с информацией
            status = self.get_status_text()
            
            # Основная панель с транскрипцией
            main_panel = Panel(
                rich_text if rich_text.plain.strip() else Text("Скажите что-нибудь...", style="dim"),
                title="[bold green]📝 Транскрипция в реальном времени[/bold green]",
                border_style="bold green",
                padding=(1, 2)
            )
            
            # Панель статуса
            status_panel = Panel(
                status,
                title="[bold blue]ℹ️  Информация[/bold blue]",
                border_style="blue",
                padding=(0, 1)
            )
            
            # Создаем layout
            layout = Layout()
            layout.split_column(
                Layout(main_panel, size=None),
                Layout(status_panel, size=6)
            )
            
            self.live.update(layout)
    
    def get_status_text(self):
        """Получение текста статуса."""
        status_lines = [
            f"🎯 Язык: русский (с поддержкой EN терминов)",
            f"🧠 Модель: {self.recorder_config['model']} ({self.recorder_config['device'].upper()})",
            f"📊 Предложений записано: {len(self.full_sentences)}",
            f"⌨️  Ctrl+C - выход | Текст автоматически копируется в буфер"
        ]
        return Text("\n".join(status_lines), style="dim")
    
    def process_final_text(self, text):
        """Обработка финального текста после завершения фразы."""
        text = self.preprocess_text(text)
        text = text.rstrip()
        
        # Убираем многоточие в конце, если есть
        if text.endswith("..."):
            text = text[:-3].strip()
        
        if not text:
            return
        
        # Добавляем в список завершенных предложений
        self.full_sentences.append(text)
        self.prev_text = ""
        self.current_text = ""
        
        # Копируем в буфер обмена
        try:
            pyperclip.copy(text)
            self.console.print(f"[dim]📋 Скопировано в буфер: {text[:50]}{'...' if len(text) > 50 else ''}[/dim]")
        except:
            pass  # Игнорируем ошибки копирования
        
        # Сбрасываем паузу
        self.recorder.post_speech_silence_duration = self.unknown_sentence_detection_pause
        
        # Обновляем отображение
        self.update_display()
    
    def run(self):
        """Основной цикл приложения."""
        self.live.start()
        
        try:
            # Показываем начальное состояние
            initial_panel = Panel(
                Text("Скажите что-нибудь...", style="cyan bold"),
                title="[bold yellow]🎤 Ожидание ввода[/bold yellow]",
                border_style="bold yellow"
            )
            self.live.update(initial_panel)
            
            self.console.print("\n[bold green]🎙️  Приложение готово! Говорите в микрофон...[/bold green]")
            
            # Основной цикл распознавания
            while True:
                self.recorder.text(self.process_final_text)
                
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        """Корректное завершение работы."""
        self.live.stop()
        
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
        
        try:
            self.recorder.shutdown()
        except:
            pass
        
        self.console.print("[bold green]✅ Приложение завершено[/bold green]")
        sys.exit(0)


def main():
    """Точка входа в приложение."""
    try:
        app = RichSTTDemo()
        app.run()
    except Exception as e:
        console = Console()
        console.print(f"[bold red]Критическая ошибка: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()