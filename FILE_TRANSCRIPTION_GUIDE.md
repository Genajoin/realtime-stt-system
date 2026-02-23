# 📄 Руководство по транскрипции файлов

## Быстрый старт

### 1. Запуск сервера

Убедитесь что Docker контейнер с STT сервером запущен:

```bash
cd ~/dev/realtime-stt-system
docker compose up -d

# Проверьте что HTTP API доступен
docker compose logs -f | grep "HTTP API"
```

Вы должны увидеть:
```
HTTP API server started on port 8013
```

### 2. Простая транскрипция файла

```bash
# Базовая транскрипция
./transcribe-file.sh audio.mp3

# С сохранением в файл
./transcribe-file.sh audio.mp3 -o transcript.txt

# С улучшенным качеством
./transcribe-file.sh audio.mp3 -b 5 -o transcript.txt
```

### 3. Продвинутые опции

```bash
# Указать язык вручную
./transcribe-file.sh audio.mp3 -l ru -o transcript.txt

# Включить временные метки
./transcribe-file.sh audio.mp3 --segments -o transcript.txt

# Тихий режим (только текст в stdout)
./transcribe-file.sh audio.mp3 -q > transcript.txt

# Указать другой сервер
./transcribe-file.sh audio.mp3 -s http://192.168.1.100:8013
```

## HTTP API использование

### cURL примеры

```bash
# Простая транскрипция
curl -X POST http://genaminipc.awg:8013/transcribe \
  -F "file=@audio.mp3"

# С параметрами качества
curl -X POST http://genaminipc.awg:8013/transcribe \
  -F "file=@audio.mp3" \
  -F "beam_size=5" \
  -F "language=ru" \
  -F "include_segments=true"

# Проверка состояния сервера
curl http://genaminipc.awg:8013/health

# Информация о конфигурации
curl http://genaminipc.awg:8013/info
```

### Python примеры

```python
import requests

# Простая транскрипция
with open('audio.mp3', 'rb') as f:
    response = requests.post(
        'http://genaminipc.awg:8013/transcribe',
        files={'file': f}
    )
    result = response.json()
    print(result['text'])

# С параметрами
with open('audio.mp3', 'rb') as f:
    response = requests.post(
        'http://genaminipc.awg:8013/transcribe',
        files={'file': f},
        data={
            'beam_size': '5',
            'language': 'ru',
            'include_segments': 'true'
        }
    )
    result = response.json()
    
    # Текст транскрипции
    print(result['text'])
    
    # Временные метки
    for segment in result.get('segments', []):
        print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}")
```

### JavaScript/Node.js примеры

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function transcribe(filePath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));
  form.append('beam_size', '10');
  form.append('language', 'ru');
  
  const response = await axios.post(
    'http://genaminipc.awg:8013/transcribe',
    form,
    { headers: form.getHeaders() }
  );
  
  console.log(response.data.text);
}

transcribe('audio.mp3');
```

## Параметры запроса

### POST /transcribe

| Параметр | Тип | Обязательный | Default | Описание |
|----------|-----|--------------|---------|----------|
| file | file | Да | - | Аудио файл (MP3, WAV, M4A, FLAC, OGG, OPUS) |
| beam_size | int | Нет | 5 | Размер beam search (1-10, выше = лучше качество, медленнее) |
| language | string | Нет | auto | Язык аудио (ru, en, auto, ...) |
| vad_filter | bool | Нет | false | Использовать VAD фильтр для удаления тишины (отключен для предотвращения повторов) |
| include_segments | bool | Нет | false | Включить временные метки в ответ |

### Формат ответа

```json
{
  "text": "Полный текст транскрипции",
  "language": "ru",
  "duration": 123.45,
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Первый сегмент текста"
    },
    {
      "start": 5.2,
      "end": 10.8,
      "text": "Второй сегмент текста"
    }
  ]
}
```

## Ограничения

- **Максимальный размер файла:** 500 MB (настраивается через `MAX_FILE_SIZE_MB` в .env)
- **Максимальная длительность:** 2 часа
- **Поддерживаемые форматы:** MP3, WAV, M4A, FLAC, OGG, OPUS
- **Таймаут:** 10 минут на транскрипцию

## Конфигурация

Параметры в `.env`:

```bash
# HTTP API порт
HTTP_PORT=8013

# Максимальный размер файла в MB
MAX_FILE_SIZE_MB=500

# Модель для обработки файлов (large для максимального качества)
FILE_MODEL=large
```

## Troubleshooting

### Сервер не отвечает

```bash
# Проверьте что контейнер запущен
docker ps | grep realtime-stt

# Проверьте логи
docker compose logs -f

# Проверьте порт
curl http://genaminipc.awg:8013/health
```

### Ошибка "Transcriber not initialized"

Подождите ~1-2 минуты после запуска контейнера для загрузки модели Whisper Large.

```bash
# Проверьте готовность
curl http://genaminipc.awg:8013/info
# Ищите "transcriber_ready": true
```

### Медленная транскрипция

- Используйте меньший `beam_size` (1-3)
- Проверьте что используется GPU (в логах должно быть "Actual Device: cuda")
- Рассмотрите использование меньшей модели через `FILE_MODEL=medium` в .env

### Повторы в транскрипции

- VAD фильтр отключен по умолчанию для предотвращения повторов
- Если повторы все равно есть, используйте `beam_size=1` для детерминированного результата
- Для зашумленных аудио можно включить VAD: `./transcribe-file.sh audio.mp3 --vad`

### Ошибка "File too large"

Увеличьте `MAX_FILE_SIZE_MB` в `.env` и перезапустите контейнер:

```bash
docker compose down
docker compose up -d
```

## Примеры использования

### Batch транскрипция всех MP3 файлов в папке

```bash
#!/bin/bash
for file in *.mp3; do
    echo "Обработка: $file"
    ./transcribe-file.sh "$file" -o "${file%.mp3}.txt" -b 5
done
```

### Транскрипция с уведомлением

```bash
#!/bin/bash
./transcribe-file.sh audio.mp3 -o transcript.txt && \
    notify-send "Транскрипция завершена" "Файл: transcript.txt"
```

### Автоматическая обработка новых файлов

```bash
#!/bin/bash
# watch_and_transcribe.sh

inotifywait -m /path/to/audio -e create -e moved_to --format '%f' | \
while read filename; do
    if [[ $filename == *.mp3 ]]; then
        echo "Обнаружен новый файл: $filename"
        ./transcribe-file.sh "/path/to/audio/$filename" \
            -o "/path/to/transcripts/${filename%.mp3}.txt"
    fi
done
```

## Интеграция с другими инструментами

### ffmpeg конвертация перед отправкой

```bash
# Конвертация видео в аудио
ffmpeg -i video.mp4 -vn -acodec mp3 audio.mp3

# Транскрипция
./transcribe-file.sh audio.mp3 -o transcript.txt
```

### Использование с yt-dlp

```bash
# Скачать аудио с YouTube
yt-dlp -x --audio-format mp3 "https://youtube.com/watch?v=..." -o audio.mp3

# Транскрибировать
./transcribe-file.sh audio.mp3 -o transcript.txt
```

## Производительность

| Модель | Качество | Скорость (на RTX 3090 Ti) | GPU память |
|--------|----------|----------------------------|------------|
| tiny | Базовое | ~100x realtime | ~300MB |
| base | Хорошее | ~50x realtime | ~500MB |
| small | Хорошее+ | ~30x realtime | ~1GB |
| medium | Отличное | ~20x realtime | ~2GB |
| **large** | **Максимальное** | **~10x realtime** | **~5GB** |

*Скорость указана для аудио без тишины с VAD фильтром*

## Дополнительные ресурсы

- [README.md](README.md) - Общая документация системы
- [AGENTS.md](AGENTS.md) - Инструкции для ИИ-агентов
- [Whisper Documentation](https://github.com/openai/whisper) - Официальная документация Whisper
