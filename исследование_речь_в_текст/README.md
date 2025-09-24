# Исследование: Создание приложения для преобразования речи в текст в реальном времени

## Введение
Цель данного исследования - анализ существующих решений для создания приложения, которое преобразует речь в текст в режиме реального времени, исправляя найденные ошибки, для использования под Linux Ubuntu.

## Анализированные библиотеки

### 1. Vosk API (/alphacep/vosk-api)
- **Описание**: Оффлайн speech recognition toolkit, поддерживает 20+ языков, continuous transcription, zero-latency streaming.
- **Реальное время**: Да, streaming поддерживается.
- **Исправление ошибок**: Поддержка WER (Word Error Rate) evaluation, но встроенные механизмы исправления ограничены.
- **Совместимость с Ubuntu**: Полная поддержка Linux.
- **Преимущества**: Быстрый, оффлайн, низкая задержка.
- **Недостатки**: Меньше языков по сравнению с Whisper.

### 2. Whisper (/openai/whisper)
- **Описание**: General-purpose speech recognition model, multilingual, поддерживает ASR и translation.
- **Реальное время**: Основной фокус на файлах, но есть streaming версии (faster-whisper).
- **Исправление ошибок**: Встроенные normalizers для английского, WER calculation.
- **Совместимость с Ubuntu**: Полная, требует ffmpeg.
- **Преимущества**: Высокая точность, multilingual.
- **Недостатки**: Может быть медленнее для реального времени без оптимизаций.

### 3. Sherpa ONNX (/k2-fsa/sherpa-onnx)
- **Описание**: Toolkit для speech recognition, synthesis, VAD, локальный, поддерживает streaming.
- **Реальное время**: Да, streaming ASR from microphone, различные модели (Zipformer, Paraformer).
- **Исправление ошибок**: Homophone replacer (HR) для исправления омофонов, добавление пунктуации.
- **Совместимость с Ubuntu**: Полная поддержка Linux.
- **Преимущества**: Real-time, VAD, punctuation, homophone correction.
- **Недостатки**: Требует загрузки моделей.

### 4. Faster Whisper (/systran/faster-whisper)
- **Описание**: Реализация Whisper с CTranslate2, до 4x быстрее, с quantization.
- **Реальное время**: Поддержка batched transcription, VAD filter.
- **Исправление ошибок**: Наследует от Whisper, word-level timestamps.
- **Совместимость с Ubuntu**: Полная, поддержка CUDA/CPU.
- **Преимущества**: Быстрее оригинального Whisper, поддержка GPU.
- **Недостатки**: Зависит от Whisper.

## Рекомендации
Для приложения на Ubuntu рекомендуется использовать Sherpa ONNX для реального времени с исправлением ошибок (homophone replacer). Для высокой точности - Faster Whisper.

## Реализация
Приложение может быть написано на Python, используя одну из библиотек. Для реального времени использовать streaming API.