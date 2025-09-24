# Исследование решений для распознавания речи в реальном времени

## Цель исследования
Найти и сравнить существующие решения для создания приложения распознавания речи со следующими требованиями:
- **Стриминг в реальном времени** (видеть текст по мере говорения)
- **Поддержка русского и английского языков** с возможностью смешивания
- **Коррекция ошибок** и расстановка знаков препинания
- **Работа на Linux Ubuntu**
- **Возможность использования GPU** и работы только на CPU
- **Быстрое копирование в буфер обмена**

## Обнаруженные решения

### 1. RealtimeSTT (Лучший выбор для локального решения)
**Репозиторий**: github.com/koljab/realtimestt

**Преимущества:**
- ✅ **Полноценный стриминг** с промежуточными результатами
- ✅ **Основан на faster-whisper** - поддержка 100+ языков включая русский
- ✅ **GPU и CPU поддержка** через CUDA и ONNX
- ✅ **VAD (Voice Activity Detection)** для автоматического определения речи
- ✅ **Простая интеграция с Python**
- ✅ **Callback-функции** для обработки текста в реальном времени
- ✅ **Wake words** поддержка
- ✅ **WebSocket сервер** для создания web-интерфейса

**Недостатки:**
- ❌ Нет встроенной коррекции ошибок (нужна дополнительная обработка)
- ❌ Пунктуация зависит от модели Whisper

**Установка:**
```bash
pip install RealtimeSTT
pip install torch==2.5.1+cu121 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
```

**Пример использования:**
```python
from RealtimeSTT import AudioToTextRecorder

def process_text(text):
    print(text)
    # Здесь можно добавить копирование в буфер

recorder = AudioToTextRecorder(
    model="large-v3",
    language="ru",  # или "auto" для автоопределения
    enable_realtime_transcription=True,
    on_realtime_transcription_update=lambda text: print(f"Промежуточный: {text}")
)

while True:
    recorder.text(process_text)
```

### 2. Whisper Streaming (UFAL)
**Репозиторий**: github.com/ufal/whisper_streaming

**Преимущества:**
- ✅ **Настоящий стриминг** с минимальной задержкой
- ✅ **Поддержка faster-whisper и OpenAI API**
- ✅ **Мультиязычность** через Whisper
- ✅ **Buffer trimming** для оптимизации памяти
- ✅ **Поддержка VAC/VAD**

**Недостатки:**
- ❌ Более сложная настройка
- ❌ Меньше документации

**Установка:**
```bash
pip install faster-whisper
pip install librosa soundfile
pip install torch torchaudio  # для VAC
```

### 3. OpenAI Realtime API (Облачное решение премиум-класса)
**API**: OpenAI Realtime API

**Преимущества:**
- ✅ **Отличное качество распознавания**
- ✅ **Встроенная коррекция и пунктуация**
- ✅ **WebSocket стриминг**
- ✅ **Поддержка множества языков**
- ✅ **Нет нагрузки на локальное железо**

**Недостатки:**
- ❌ **Платное решение** (дорого для постоянного использования)
- ❌ **Требует интернет**
- ❌ **Приватность** - аудио отправляется на серверы OpenAI

**Пример:**
```javascript
import { RealtimeClient } from '@openai/realtime-api-beta';

const client = new RealtimeClient({ 
    apiKey: process.env.OPENAI_API_KEY 
});

client.updateSession({ 
    input_audio_transcription: { model: 'whisper-1' },
    language: 'ru'
});

client.on('conversation.updated', (event) => {
    const { item, delta } = event;
    // Обработка транскрипции
});
```

### 4. Google Cloud Speech-to-Text (Облачное решение)
**API**: Google Cloud Speech-to-Text

**Преимущества:**
- ✅ **Отличная поддержка русского и английского**
- ✅ **Автоматическая пунктуация**
- ✅ **Стриминг через gRPC**
- ✅ **Высокая точность**

**Недостатки:**
- ❌ **Платное** ($0.006 за 15 секунд)
- ❌ **Требует интернет**
- ❌ **Сложная настройка аутентификации**

**Пример:**
```python
from google.cloud import speech

client = speech.SpeechClient()
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="ru-RU",  # или "en-US"
    enable_automatic_punctuation=True
)

streaming_config = speech.StreamingRecognitionConfig(
    config=config,
    interim_results=True
)
```

### 5. Vosk (Легковесное локальное решение)
**Репозиторий**: github.com/alphacep/vosk-api

**Преимущества:**
- ✅ **Полностью оффлайн**
- ✅ **Очень быстрый на CPU**
- ✅ **Малый размер моделей** (50-2000 МБ)
- ✅ **Поддержка русского**
- ✅ **Настоящий стриминг**

**Недостатки:**
- ❌ **Качество хуже Whisper**
- ❌ **Нет автоматической пунктуации**
- ❌ **Сложнее смешивать языки**

### 6. Faster-Whisper (База для многих решений)
**Репозиторий**: github.com/systran/faster-whisper

**Преимущества:**
- ✅ **В 4 раза быстрее оригинального Whisper**
- ✅ **Поддержка quantization** (INT8)
- ✅ **Batched inference**
- ✅ **VAD фильтрация**

**Недостатки:**
- ❌ **Нет встроенного стриминга** (нужна обертка)
- ❌ **Обрабатывает только завершенные аудио**

## Сравнительная таблица

| Решение | Стриминг | Языки | GPU/CPU | Оффлайн | Пунктуация | Сложность | Цена |
|---------|----------|-------|---------|---------|------------|-----------|------|
| **RealtimeSTT** | ✅ Отличный | ✅ 100+ | ✅/✅ | ✅ | ⚠️ Зависит от модели | Простая | Бесплатно |
| **Whisper Streaming** | ✅ Отличный | ✅ 100+ | ✅/✅ | ✅ | ⚠️ Зависит от модели | Средняя | Бесплатно |
| **OpenAI Realtime** | ✅ Отличный | ✅ Много | ☁️ | ❌ | ✅ | Простая | $$$$ |
| **Google Speech** | ✅ Хороший | ✅ Много | ☁️ | ❌ | ✅ | Средняя | $$$ |
| **Vosk** | ✅ Отличный | ✅ 20+ | ❌/✅ | ✅ | ❌ | Простая | Бесплатно |
| **Faster-Whisper** | ❌ | ✅ 100+ | ✅/✅ | ✅ | ⚠️ | Средняя | Бесплатно |

## Рекомендации

### 🏆 Оптимальное решение: RealtimeSTT + постобработка

**Почему:**
1. **Полностью локальное** - приватность и независимость от интернета
2. **Отличный стриминг** - видите текст сразу
3. **Поддержка GPU и CPU** - работает на любом железе
4. **Основан на Whisper** - высокое качество распознавания
5. **Простая интеграция** - быстрый старт разработки

**План реализации:**
```python
# 1. Базовое распознавание с RealtimeSTT
from RealtimeSTT import AudioToTextRecorder
import pyperclip
import tkinter as tk

class SpeechToTextApp:
    def __init__(self):
        self.recorder = AudioToTextRecorder(
            model="large-v3",
            language="auto",  # Автоопределение ru/en
            enable_realtime_transcription=True,
            use_microphone=True,
            gpu_device_index=0,
            on_realtime_transcription_update=self.on_update,
            ensure_sentence_ends_with_period=True,
            ensure_sentence_starting_uppercase=True
        )
        self.setup_gui()
    
    def on_update(self, text):
        # Показываем промежуточный текст
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(1.0, text)
    
    def on_complete(self, text):
        # Копируем в буфер при завершении
        corrected_text = self.correct_text(text)
        pyperclip.copy(corrected_text)
        
    def correct_text(self, text):
        # Здесь можно добавить:
        # - Исправление через language_tool_python
        # - Или API для грамматики (Яндекс.Спеллер для русского)
        # - Или локальную модель T5 для коррекции
        return text
```

### Альтернативные варианты:

**Для максимального качества с интернетом:**
- Google Cloud Speech-to-Text - лучшая поддержка русского языка и пунктуации

**Для минимальных требований к железу:**
- Vosk - работает даже на Raspberry Pi

**Для web-приложения:**
- RealtimeSTT с WebSocket сервером + web интерфейс

## Дополнительные компоненты для улучшения

### 1. Коррекция ошибок
```bash
pip install language_tool_python  # Для английского
pip install pyaspeller  # Для русского (Яндекс.Спеллер)
```

### 2. Улучшение пунктуации
```python
# Использование модели punctuator для добавления знаков препинания
from deepmultilingualpunctuation import PunctuationModel
model = PunctuationModel()
text_with_punctuation = model.restore_punctuation(text)
```

### 3. GUI окно
```python
# Простое окно с PyQt5 или Tkinter
# - Горячие клавиши через pynput
# - Полупрозрачное окно поверх всех
# - Автокопирование в буфер
```

## Выводы

Для ваших требований **RealtimeSTT** - оптимальный выбор как основа приложения. Он предоставляет:
- ✅ Все необходимые функции из коробки
- ✅ Простую интеграцию
- ✅ Хорошее качество через Whisper
- ✅ Возможность работы оффлайн

Дополнив его модулями для коррекции текста и простым GUI, вы получите именно то приложение, которое описали в требованиях.