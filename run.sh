#!/bin/bash

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено!"
    echo "Сначала запустите: ./install.sh"
    exit 1
fi

# Активация виртуального окружения
source venv/bin/activate

# Запуск приложения
echo "🚀 Запуск Simple STT Demo..."
echo
python3 simple_stt_demo.py