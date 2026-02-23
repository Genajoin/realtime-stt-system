# Changelog: Добавление HTTP API для транскрипции файлов

## Дата: 2025-01-18

### Что добавлено

#### 1. HTTP API сервер для транскрипции файлов

**Новые файлы:**
- `mic_stream_py/server/file_transcriber.py` - Модуль для транскрипции аудио файлов через Whisper
- `mic_stream_py/server/http_api.py` - HTTP REST API сервер на aiohttp
- `mic_stream_py/client/file_transcribe_client.py` - Python клиент для отправки файлов
- `mic_stream_py/server/requirements-server.txt` - Зависимости сервера
- `mic_stream_py/server/test_http_api.py` - Тесты для HTTP API
- `transcribe-file.sh` - Bash скрипт для быстрой транскрипции
- `FILE_TRANSCRIPTION_GUIDE.md` - Подробное руководство по использованию

**Модифицированные файлы:**
- `mic_stream_py/server/stt_server.py` - Интеграция HTTP сервера
- `mic_stream_py/server/env_config.py` - Добавлены параметры HTTP API
- `mic_stream_py/server/Dockerfile` - Добавлены новые модули и порт 8013
- `docker-compose.yml` - Экспозиция порта 8013
- `.env.example` - Добавлены параметры HTTP_PORT, MAX_FILE_SIZE_MB, FILE_MODEL
- `README.md` - Обновлена документация с описанием нового API

### Ключевые особенности

#### API Endpoints

1. **POST /transcribe** - Транскрипция загруженного файла
   - Поддержка форматов: MP3, WAV, M4A, FLAC, OGG, OPUS
   - Автоматическая конвертация в WAV
   - Параметры: beam_size, language, vad_filter, include_segments
   - Максимальный размер: 500MB (настраивается)
   - Максимальная длительность: 2 часа

2. **GET /health** - Проверка состояния сервера

3. **GET /info** - Информация о конфигурации

#### Технические детали

- **Модель для файлов:** Whisper Large (настраивается через FILE_MODEL)
- **Порт:** 8013 (настраивается через HTTP_PORT)
- **Асинхронная обработка:** aiohttp + asyncio
- **Валидация:** Размер файла, длительность, формат
- **Обработка ошибок:** Детальные сообщения об ошибках
- **Производительность:** ~10x realtime на RTX 3090 Ti с Large моделью

### Использование

#### Быстрый старт

```bash
# Простая транскрипция
./transcribe-file.sh audio.mp3

# С сохранением в файл
./transcribe-file.sh audio.mp3 -o transcript.txt

# С улучшенным качеством и временными метками
./transcribe-file.sh audio.mp3 -b 10 --segments -o result.txt
```

#### HTTP API

```bash
# curl
curl -X POST http://genaminipc.awg:8013/transcribe \
  -F "file=@audio.mp3" \
  -F "beam_size=10"

# Python
import requests
with open('audio.mp3', 'rb') as f:
    response = requests.post(
        'http://genaminipc.awg:8013/transcribe',
        files={'file': f}
    )
    print(response.json()['text'])
```

### Конфигурация

Новые переменные окружения в `.env`:

```bash
# HTTP API порт для загрузки файлов
HTTP_PORT=8013

# Максимальный размер загружаемого файла в MB
MAX_FILE_SIZE_MB=500

# Модель Whisper для обработки файлов
FILE_MODEL=large
```

### Архитектурные изменения

#### До:
```
WebSocket (8011/8012) → Real-time STT (Whisper Medium)
```

#### После:
```
WebSocket (8011/8012) → Real-time STT (Whisper Medium)
HTTP API (8013)       → File STT (Whisper Large)
```

### Зависимости

Добавлены новые зависимости:
- `aiohttp>=3.9.0` - HTTP сервер
- `librosa>=0.10.0` - Конвертация аудио (уже была)
- `soundfile>=0.12.0` - Сохранение WAV (добавлена)

### Совместимость

- ✅ Обратная совместимость с существующим WebSocket API
- ✅ Real-time транскрипция продолжает работать без изменений
- ✅ Все существующие клиенты совместимы
- ✅ Docker образ совместим с предыдущей версией

### Производительность

| Операция | До | После |
|----------|-----|-------|
| Real-time STT | ✅ Whisper Medium | ✅ Whisper Medium (без изменений) |
| Транскрипция файлов | ❌ Недоступна | ✅ Whisper Large (~10x realtime) |
| GPU память | ~2GB | ~2GB (real-time) + ~5GB (файлы, по требованию) |
| Порты | 8011, 8012 | 8011, 8012, 8013 |

### Тестирование

```bash
# Проверка HTTP API endpoints
python3 mic_stream_py/server/test_http_api.py

# Проверка транскрипции
./transcribe-file.sh test_audio.mp3 -o test_result.txt
```

### Известные ограничения

1. Large модель требует ~5GB GPU памяти
2. Первая транскрипция медленнее из-за загрузки модели (~1-2 минуты)
3. Таймаут HTTP запроса: 10 минут

### Будущие улучшения

- [ ] Поддержка потоковой загрузки больших файлов
- [ ] Кеширование результатов транскрипции
- [ ] WebSocket для прогресс-бара длинных файлов
- [ ] Batch API для обработки множества файлов
- [ ] Поддержка speaker diarization

### Migration Guide

Для обновления с предыдущей версии:

1. Обновить `.env` с новыми параметрами (опционально)
2. Пересобрать Docker образ: `docker compose build`
3. Перезапустить контейнер: `docker compose up -d`
4. Проверить доступность HTTP API: `curl http://localhost:8013/health`

Никаких breaking changes для существующих клиентов!

### Команда разработки

- Архитектура и реализация: AI Assistant
- Интеграция с существующей системой: AI Assistant
- Документация: AI Assistant

### Ссылки

- [FILE_TRANSCRIPTION_GUIDE.md](FILE_TRANSCRIPTION_GUIDE.md) - Подробное руководство
- [README.md](README.md#-транскрипция-файлов-new) - Обновленная документация
- [AGENTS.md](AGENTS.md) - Инструкции для ИИ-агентов
