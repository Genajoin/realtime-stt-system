# Максимально оптимизированный multi-stage Dockerfile
# Стейджи упорядочены по частоте изменений для лучшего кеширования

# ═══════════════════════════════════════════════════════════════
# Stage 1: Базовая система (изменяется крайне редко)
# ═══════════════════════════════════════════════════════════════
FROM ubuntu:22.04 AS system-base

# Устанавливаем системные зависимости одним слоем
RUN apt-get update && apt-get install -y \
    python3=3.10.* \
    python3-pip \
    python3-dev \
    portaudio19-dev \
    ffmpeg \
    wget \
    curl \
    git \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Добавляем NVIDIA репозиторий для cuDNN
RUN wget -qO - https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub | apt-key add - \
    && echo "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64 /" > /etc/apt/sources.list.d/cuda.list \
    && apt-get update \
    && apt-get install -y libcudnn8 libcudnn8-dev \
    && rm -rf /var/lib/apt/lists/*

# ═══════════════════════════════════════════════════════════════
# Stage 2: PyTorch установка (большая, редко изменяется)
# ═══════════════════════════════════════════════════════════════
FROM system-base AS pytorch-stage

# Устанавливаем только PyTorch с CUDA (самый большой компонент ~2GB)
RUN pip3 install --no-cache-dir --no-compile \
    torch==2.5.1+cu121 \
    torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu121

# ═══════════════════════════════════════════════════════════════
# Stage 3: Python зависимости приложения (средняя частота изменений)
# ═══════════════════════════════════════════════════════════════
FROM pytorch-stage AS app-deps

WORKDIR /app

# Копируем requirements и устанавливаем зависимости приложения
COPY requirements-server.txt .
RUN pip3 install --no-cache-dir --no-compile -r requirements-server.txt

# ═══════════════════════════════════════════════════════════════
# Stage 4: Конфигурация окружения (редко изменяется)
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
# Stage 5: Код приложения (изменяется часто - финальный слой)
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