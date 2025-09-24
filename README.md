# 🎙️ Realtime STT System

Система распознавания речи в реальном времени с клиент-серверной архитектурой через WebSocket.

## 🏗️ Архитектура

```
┌─────────────────┐    WebSocket    ┌─────────────────────────┐
│   Rich Client   │ ──────────────► │   Docker GPU Server    │
│   (локально)    │    8011/8012    │     (genaminipc.awg)    │
└─────────────────┘                 └─────────────────────────┘
│                                   │
├─ Микрофон                         ├─ Whisper Medium (769MB)
├─ Rich интерфейс                   ├─ RTX 3090 Ti / CUDA
├─ WebSocket клиент                 ├─ Real-time транскрипция
└─ Аудио захват                     └─ Русский + английский язык
```

## 🚀 Быстрый старт

### 1. Запуск сервера (на genaminipc.awg)

```bash
# Сборка и запуск Docker контейнера
cd ~/dev/realtime-stt-system
docker compose down
docker compose build --no-cache  # ~10 минут первый раз
docker compose up -d

# Проверка статуса
docker compose ps
docker compose logs -f
```

### 2. Запуск клиента (локально)

```bash
# Через Makefile (рекомендуется)
make run-websocket-client

# Или напрямую
python3 websocket_rich_client.py --server genaminipc.awg
```

## 🛠️ Команды управления

### Makefile команды

```bash
make help                    # Показать все команды
make run-websocket-client    # Запустить WebSocket клиент
make deploy                  # Деплой на удаленный сервер
make remote-logs            # Логи с сервера
make remote-status          # Статус на сервере
```

### Docker команды

```bash
# Локальная разработка
make docker-build           # Сборка образа
make docker-run             # Запуск контейнера
make docker-logs            # Просмотр логов
make docker-stop            # Остановка
make docker-status          # Статус и ресурсы

# Удаленный сервер  
make deploy                 # Полный деплой
make remote-logs            # Мониторинг логов
```

## 🔧 Конфигурация

### Серверная часть (Docker)

**Модели:**
- **Основная**: Whisper Medium (769MB, высокое качество)
- **Real-time**: Whisper Tiny (39MB, быстрый отклик)

**Железо:**
- GPU: RTX 3090 Ti (24GB VRAM)
- CUDA: 12.1
- Порты: 8011 (control), 8012 (data)

**Параметры** (в `server/Dockerfile`):
```dockerfile
CMD ["python3", "-u", "stt_server.py",
     "--model", "medium",              # Whisper модель
     "--language", "ru",               # Русский язык  
     "--realtime_model_type", "tiny",  # Real-time модель
     "--device", "cuda",               # GPU ускорение
     "--enable_realtime_transcription",
     "--silero_use_onnx"]
```

### Клиентская часть

**Аудио:**
- Sample rate: автоподбор (16kHz, 44.1kHz, 48kHz)
- Формат: 16-bit PCM
- Каналы: моно

**WebSocket:**
- Control: `ws://genaminipc.awg:8011`
- Data: `ws://genaminipc.awg:8012`

## 📊 Производительность

| Модель | Размер | VRAM | Качество | Скорость |
|--------|--------|------|----------|----------|
| tiny   | 39MB   | ~1GB | Базовое  | Очень быстро |
| small  | 244MB  | ~2GB | Хорошее  | Быстро |
| **medium** | **769MB** | **~5GB** | **Отличное** | **Оптимально** |
| large  | 1.5GB  | ~10GB| Максимальное | Медленно |

## 🐳 Docker оптимизация

**6-стадийная сборка** с детальным разделением зависимостей:

1. **pytorch-base**: Официальный PyTorch + CUDA (готовый образ)
2. **system-libs**: Системные библиотеки через conda (~200MB, редко меняются)
3. **heavy-deps**: Крупные Python библиотеки (~1.5GB, редко меняются)
   - RealtimeSTT, faster-whisper, librosa
4. **light-deps**: Легкие Python зависимости (~300MB, могут меняться)
5. **runtime-config**: Переменные окружения и директории (~10MB)
6. **production**: Код приложения (~50KB, изменяется часто)

**Преимущества:**
- Первая сборка: ~8 минут (PyTorch уже в образе)
- Пересборка при изменении кода: ~20 секунд
- Изменение легких зависимостей: ~2-3 минуты (только стадии 4-6)
- Изменение тяжелых библиотек: ~5-7 минут (стадии 3-6)
- Максимальное гранулярное кеширование

## 🔍 Мониторинг

```bash
# Логи сервера
ssh genaminipc.awg 'cd ~/dev/realtime-stt-system && docker compose logs -f'

# Статус и ресурсы
ssh genaminipc.awg 'cd ~/dev/realtime-stt-system && docker compose ps && docker stats --no-stream'

# Использование GPU
ssh genaminipc.awg 'nvidia-smi'
```

## 🚨 Troubleshooting

### Проблемы с аудио
```bash
# Проверить занятость микрофона
ps aux | grep -E "(python.*stt|python.*rich)" | grep -v grep
kill <PID>  # если найдены процессы

# Проверить аудио устройства
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)}') for i in range(p.get_device_count())]"
```

### Проблемы с Docker
```bash
# Пересборка без кеша
docker compose build --no-cache --progress=plain

# Очистка ресурсов
docker system prune -f
docker volume prune -f

# Проверка портов
netstat -tlnp | grep -E ":801[12]"
```

### WebSocket соединение
```bash
# Тест TCP подключения
telnet genaminipc.awg 8011

# Проверка через curl
curl -I http://genaminipc.awg:8011
```

## 📚 API

### WebSocket протокол

**Control канал** (порт 8011):
- Управляющие команды
- Статус сервера
- Конфигурация

**Data канал** (порт 8012):  
- Передача аудио потока
- Получение транскрипции
- Real-time обновления

## 🎯 Roadmap

- [ ] Web интерфейс для управления
- [ ] Поддержка множественных клиентов
- [ ] API для интеграции с другими приложениями
- [ ] Метрики и аналитика
- [ ] Поддержка других языков

## 👥 Contributing

1. Fork проекта
2. Создайте feature ветку (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## 📄 License

Этот проект использует MIT License. Подробности в файле `LICENSE`.

---

🚀 **Готов к использованию!** Запустите `make run-websocket-client` и начните говорить!