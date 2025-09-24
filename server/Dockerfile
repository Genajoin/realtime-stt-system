# Оптимизированный multi-stage Dockerfile
# Используем официальный PyTorch образ с CUDA - намного проще и надежнее!

# ═══════════════════════════════════════════════════════════════
# Stage 1: Официальный PyTorch с CUDA (уже включает PyTorch + CUDA + cuDNN)
# ═══════════════════════════════════════════════════════════════
FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime AS pytorch-base

# Обновляем pip и устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    ffmpeg \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ═══════════════════════════════════════════════════════════════
# Stage 2: Python зависимости приложения (~1GB)
# ═══════════════════════════════════════════════════════════════
FROM pytorch-base AS app-deps

WORKDIR /app

# Копируем requirements и устанавливаем зависимости приложения
COPY requirements-server.txt .
RUN pip3 install --no-cache-dir --no-compile -r requirements-server.txt

# ═══════════════════════════════════════════════════════════════
# Stage 3: Конфигурация окружения (~10MB)
# ═══════════════════════════════════════════════════════════════
FROM app-deps AS runtime-config

# Создаем директории и настраиваем окружение
RUN mkdir -p /app/models /app/logs /app/cache

# Настраиваем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CUDA_VISIBLE_DEVICES=0 \
    TORCH_HOME=/app/models \
    HF_HOME=/app/cache \
    TRANSFORMERS_CACHE=/app/cache \
    PIP_NO_CACHE_DIR=1

# ═══════════════════════════════════════════════════════════════
# Stage 4: Код приложения (~50KB, изменяется часто)
# ═══════════════════════════════════════════════════════════════
FROM runtime-config AS production

# Копируем код приложения (самый часто изменяемый слой)
COPY stt_server.py .
COPY install_packages.py .

# Открываем порты для WebSocket соединений
EXPOSE 8011 8012

# Проверка готовности с увеличенным timeout для GPU инициализации
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=3 \
    CMD python3 -c "import socket; socket.create_connection(('localhost', 8011), timeout=10)" || exit 1

# Команда по умолчанию с оптимальными параметрами для GPU
CMD ["python3", "-u", "stt_server.py", \
     "--model", "medium", \
     "--language", "ru", \
     "--realtime_model_type", "tiny", \
     "--control_port", "8011", \
     "--data_port", "8012", \
     "--device", "cuda", \
     "--enable_realtime_transcription", \
     "--silero_use_onnx"]