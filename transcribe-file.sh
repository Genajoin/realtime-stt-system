#!/bin/bash
# Простой скрипт для транскрибации аудио файлов

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT_SCRIPT="$SCRIPT_DIR/mic_stream_py/client/file_transcribe_client.py"

# Проверяем наличие Python скрипта
if [ ! -f "$CLIENT_SCRIPT" ]; then
    echo "Ошибка: Клиентский скрипт не найден: $CLIENT_SCRIPT"
    exit 1
fi

# Запускаем Python скрипт с переданными аргументами
python3 "$CLIENT_SCRIPT" "$@"
