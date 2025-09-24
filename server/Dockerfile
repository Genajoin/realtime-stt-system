# Multi-stage Dockerfile для GPU с оптимальным кешированием
# Stage 1: Базовый образ NVIDIA CUDA с системными зависимостями
FROM nvidia/cuda:11.8-runtime-ubuntu22.04 AS base

# Устанавливаем системные зависимости (редко изменяются)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    portaudio19-dev \
    ffmpeg \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Установка больших Python зависимостей
FROM base AS python-deps

WORKDIR /app

# Копируем requirements и устанавливаем базовые зависимости (изменяются редко)
COPY requirements-server.txt .
RUN pip3 install --no-cache-dir -r requirements-server.txt

# Устанавливаем PyTorch с CUDA поддержкой (самая большая зависимость)
RUN pip3 install --no-cache-dir torch==2.5.1+cu118 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu118

# Stage 3: Production образ с кодом приложения
FROM python-deps AS production

# Создаем директории для моделей и логов
RUN mkdir -p /app/models /app/logs

# Настраиваем переменные окружения
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV TORCH_HOME=/app/models

# Копируем код приложения (изменяется часто - поэтому в конце)
COPY stt_server.py .
COPY install_packages.py .

# Открываем порты для WebSocket соединений
EXPOSE 8011 8012

# Проверка готовности
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import socket; socket.create_connection(('localhost', 8011), timeout=5)" || exit 1

# Команда по умолчанию с GPU поддержкой
CMD ["python3", "stt_server.py", \
     "--model", "small", \
     "--language", "ru", \
     "--realtime_model_type", "tiny", \
     "--control_port", "8011", \
     "--data_port", "8012", \
     "--device", "cuda", \
     "--enable_realtime_transcription", \
     "--silero_use_onnx"]