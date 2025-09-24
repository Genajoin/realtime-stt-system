# Dockerfile для GPU сервера RealtimeSTT
FROM nvidia/cuda:12.1-base-ubuntu22.04

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    portaudio19-dev \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Создание виртуального окружения
RUN python3 -m venv /app/venv

# Активация виртуального окружения и установка Python пакетов
ENV PATH="/app/venv/bin:$PATH"

# Установка PyTorch с CUDA 12.1
RUN pip install --no-cache-dir torch==2.5.1+cu121 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

# Установка основных зависимостей
RUN pip install --no-cache-dir \
    RealtimeSTT \
    faster-whisper \
    websockets \
    numpy \
    scipy \
    colorama

# Копирование исходного кода сервера
COPY RealtimeSTT_server/ /app/RealtimeSTT_server/

# Создание директории для моделей
RUN mkdir -p /app/models

# Установка переменных окружения для GPU
ENV CUDA_VISIBLE_DEVICES=0
ENV TORCH_USE_CUDA_DSA=1

# Порты для WebSocket
EXPOSE 8011 8012

# Команда запуска сервера с настройками для русского языка
CMD ["python3", "/app/RealtimeSTT_server/stt_server.py", \
     "--model", "small", \
     "--language", "ru", \
     "--realtime_model_type", "tiny", \
     "--device", "cuda", \
     "--gpu_device_index", "0", \
     "--control_port", "8011", \
     "--data_port", "8012", \
     "--enable_realtime_transcription", \
     "--silero_sensitivity", "0.05", \
     "--webrtc_sensitivity", "3", \
     "--min_length_of_recording", "1.1", \
     "--beam_size", "5", \
     "--beam_size_realtime", "3"]