# Dockerfile для RealtimeSTT сервера (временно без GPU)
FROM ubuntu:22.04

# Устанавливаем системные зависимости
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

# Создаем рабочую директорию
WORKDIR /app

# Копируем requirements для сервера
COPY requirements-server.txt .

# Устанавливаем Python зависимости
RUN pip3 install --no-cache-dir -r requirements-server.txt

# Устанавливаем PyTorch для CPU
RUN pip3 install --no-cache-dir torch==2.5.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cpu

# Копируем код сервера
COPY stt_server.py .
COPY install_packages.py .

# Создаем директории для моделей и логов
RUN mkdir -p /app/models /app/logs

# Настраиваем переменные окружения
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV TORCH_HOME=/app/models

# Открываем порты для WebSocket соединений
EXPOSE 8011 8012

# Проверка готовности
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import socket; socket.create_connection(('localhost', 8011), timeout=5)" || exit 1

# Команда по умолчанию
CMD ["python3", "stt_server.py", \
     "--model", "small", \
     "--language", "ru", \
     "--realtime_model_type", "tiny", \
     "--control_port", "8011", \
     "--data_port", "8012", \
     "--device", "cpu", \
     "--enable_realtime_transcription", \
     "--silero_use_onnx"]