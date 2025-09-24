# Оптимизированный multi-stage Dockerfile
# Стейджи разделены по типу и размеру зависимостей для максимального кеширования

# ═══════════════════════════════════════════════════════════════
# Stage 1: Базовый PyTorch образ с CUDA (уже готов)
# ═══════════════════════════════════════════════════════════════
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime AS pytorch-base

# Только создаем рабочую директорию
WORKDIR /app

# ═══════════════════════════════════════════════════════════════
# Stage 2: Системные библиотеки через conda (средний размер, редко меняются)
# ═══════════════════════════════════════════════════════════════
FROM pytorch-base AS system-libs

# Устанавливаем системные зависимости через conda
RUN conda install -c conda-forge -y \
    portaudio \
    ffmpeg \
    pyaudio \
    librosa \
    && conda clean -afy

# ═══════════════════════════════════════════════════════════════
# Stage 3: Большие Python библиотеки (крупные, редко меняются)
# ═══════════════════════════════════════════════════════════════
FROM system-libs AS heavy-deps

# Устанавливаем тяжелые Python зависимости (librosa уже через conda)
RUN pip3 install --no-cache-dir --no-compile \
    RealtimeSTT>=0.2.0 \
    faster-whisper>=1.1.0

# ═══════════════════════════════════════════════════════════════
# Stage 4: Остальные Python зависимости (легкие, могут меняться)
# ═══════════════════════════════════════════════════════════════
FROM heavy-deps AS light-deps

# Копируем requirements и устанавливаем оставшиеся зависимости
COPY requirements-server.txt .
RUN pip3 install --no-cache-dir --no-compile -r requirements-server.txt

# ═══════════════════════════════════════════════════════════════
# Stage 5: Конфигурация окружения (~10MB)
# ═══════════════════════════════════════════════════════════════
FROM light-deps AS runtime-config

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
# Stage 6: Код приложения (~50KB, изменяется часто)
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