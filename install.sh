#!/bin/bash

echo "=== Установка Simple STT Demo ==="
echo

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8 или выше."
    exit 1
fi

echo "✓ Python3 найден: $(python3 --version)"

# Обновление pip
echo "📦 Обновление pip..."
python3 -m pip install --upgrade pip

# Установка системных зависимостей для Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Обнаружена Linux система"
    echo "📦 Установка системных зависимостей..."
    
    # Проверка наличия apt-get
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-dev python3-pip
        sudo apt-get install -y portaudio19-dev
        sudo apt-get install -y ffmpeg
    else
        echo "⚠️  apt-get не найден. Установите вручную:"
        echo "   - python3-dev"
        echo "   - portaudio19-dev"
        echo "   - ffmpeg"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Обнаружена macOS"
    if command -v brew &> /dev/null; then
        brew install portaudio
        brew install ffmpeg
    else
        echo "⚠️  Homebrew не найден. Установите вручную:"
        echo "   - portaudio"
        echo "   - ffmpeg"
    fi
fi

# Создание виртуального окружения
echo "🔧 Создание виртуального окружения..."
python3 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Установка базовых пакетов
echo "📦 Установка базовых пакетов..."
pip install --upgrade pip setuptools wheel

# Установка RealtimeSTT и зависимостей
echo "📦 Установка RealtimeSTT..."
pip install RealtimeSTT

# Установка colorama для цветного вывода
pip install colorama

# Проверка наличия CUDA
echo "🔍 Проверка CUDA..."
if command -v nvidia-smi &> /dev/null; then
    echo "✓ CUDA обнаружена"
    echo "📦 Установка PyTorch с поддержкой CUDA 12.1..."
    pip install torch==2.5.1+cu121 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
else
    echo "ℹ️  CUDA не обнаружена, используем CPU версию"
    echo "📦 Установка PyTorch для CPU..."
    pip install torch torchaudio
fi

# Установка faster-whisper
echo "📦 Установка faster-whisper..."
pip install faster-whisper

# Делаем скрипт исполняемым
chmod +x simple_stt_demo.py

echo
echo "✅ Установка завершена!"
echo
echo "Для запуска приложения:"
echo "  1. Активируйте виртуальное окружение: source venv/bin/activate"
echo "  2. Запустите: python3 simple_stt_demo.py"
echo
echo "Или просто запустите: ./run.sh"