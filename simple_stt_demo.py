#!/usr/bin/env python3
"""
Простое демо-приложение для распознавания речи в реальном времени.
Использует RealtimeSTT для транскрипции аудио с микрофона.
"""

import sys
import os
from colorama import init, Fore, Style
from RealtimeSTT import AudioToTextRecorder

# Инициализация colorama для цветного вывода в терминале
init()

class SimpleSTTDemo:
    def __init__(self):
        """Инициализация приложения для распознавания речи."""
        print(f"{Fore.CYAN}=== Простое приложение распознавания речи ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Инициализация модели...{Style.RESET_ALL}")
        
        try:
            # Создаем рекордер с оптимальными настройками
            self.recorder = AudioToTextRecorder(
                model="small",  # Используем small для баланса скорости и качества
                language="ru",  # Русский язык (поддерживает английские термины)
                compute_type="default",
                device="cuda" if self.check_cuda() else "cpu",
                
                # Включаем транскрипцию в реальном времени
                enable_realtime_transcription=True,
                realtime_processing_pause=0.1,  # Обновление каждые 100мс
                realtime_model_type="tiny",  # Быстрая модель для реального времени
                
                # Используем одну модель для всего (проще и надежнее)
                use_main_model_for_realtime=True,
                
                # Настройки VAD (Voice Activity Detection)
                silero_sensitivity=0.4,
                webrtc_sensitivity=3,
                post_speech_silence_duration=0.4,
                min_length_of_recording=0.5,
                
                # Улучшение текста
                ensure_sentence_starting_uppercase=True,
                ensure_sentence_ends_with_period=True,
                
                # Callbacks
                on_realtime_transcription_update=self.on_realtime_update,
                on_realtime_transcription_stabilized=self.on_stabilized_update,
                on_recording_start=self.on_recording_start,
                on_recording_stop=self.on_recording_stop,
                on_vad_detect_start=self.on_vad_start,
                on_vad_detect_stop=self.on_vad_stop,
                
                # Отключаем спиннер для чистого вывода
                spinner=False,
                debug_mode=False
            )
            

            
            print(f"{Fore.GREEN}✓ Модель загружена успешно!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Используется: {self.recorder.device.upper()}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}✗ Ошибка инициализации: {e}{Style.RESET_ALL}")
            sys.exit(1)
            
        self.current_line = ""
        self.full_text = []
        
    def check_cuda(self):
        """Проверка доступности CUDA."""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def on_realtime_update(self, text):
        """Обработка промежуточных результатов транскрипции."""
        # Очищаем текущую строку и выводим новый текст
        sys.stdout.write('\r' + ' ' * len(self.current_line) + '\r')
        self.current_line = f"{Fore.YELLOW}▶ {text}{Style.RESET_ALL}"
        sys.stdout.write(self.current_line)
        sys.stdout.flush()
    
    def on_stabilized_update(self, text):
        """Обработка стабилизированного текста (более точного)."""
        # Перезаписываем текущую строку стабилизированным текстом
        sys.stdout.write('\r' + ' ' * len(self.current_line) + '\r')
        self.current_line = f"{Fore.GREEN}► {text}{Style.RESET_ALL}"
        sys.stdout.write(self.current_line)
        sys.stdout.flush()
    
    def on_recording_start(self):
        """Вызывается при начале записи."""
        print(f"\n{Fore.GREEN}🎤 Запись началась...{Style.RESET_ALL}")
    
    def on_recording_stop(self):
        """Вызывается при остановке записи."""
        print(f"\n{Fore.RED}🔴 Запись остановлена{Style.RESET_ALL}")
    
    def on_vad_start(self):
        """Вызывается при обнаружении голоса."""
        sys.stdout.write(f"\r{Fore.CYAN}[Обнаружена речь]{Style.RESET_ALL} ")
        sys.stdout.flush()
    
    def on_vad_stop(self):
        """Вызывается при окончании речи."""
        pass
    
    def process_final_text(self, text):
        """Обработка финального текста после завершения фразы."""
        if text.strip():
            # Очищаем промежуточную строку
            sys.stdout.write('\r' + ' ' * len(self.current_line) + '\r')
            
            # Выводим финальный текст
            print(f"{Fore.WHITE}✓ {text}{Style.RESET_ALL}")
            
            # Сохраняем в историю
            self.full_text.append(text)
            self.current_line = ""
    
    def run(self):
        """Основной цикл приложения."""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Приложение готово к работе!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Настройки:{Style.RESET_ALL}")
        print(f"  • Основной язык: русский")
        print(f"  • Английские термины будут распознаваться латиницей")
        print(f"  • Модель: small (баланс скорости и качества)")
        print(f"{Fore.YELLOW}Команды:{Style.RESET_ALL}")
        print(f"  • Говорите в микрофон для распознавания")
        print(f"  • Нажмите Ctrl+C для выхода")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        print(f"{Fore.GREEN}🎙️  Слушаю... (говорите в микрофон){Style.RESET_ALL}\n")
        
        try:
            while True:
                # Ждем и обрабатываем речь
                self.recorder.text(self.process_final_text)
                
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        """Корректное завершение работы."""
        print(f"\n\n{Fore.YELLOW}Завершение работы...{Style.RESET_ALL}")
        
        if self.full_text:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Полная транскрипция сессии:{Style.RESET_ALL}")
            for i, text in enumerate(self.full_text, 1):
                print(f"{i}. {text}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        try:
            self.recorder.shutdown()
        except:
            pass
            
        print(f"{Fore.GREEN}✓ Приложение завершено{Style.RESET_ALL}")
        sys.exit(0)


def main():
    """Точка входа в приложение."""
    try:
        app = SimpleSTTDemo()
        app.run()
    except Exception as e:
        print(f"{Fore.RED}Критическая ошибка: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()