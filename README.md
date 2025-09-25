# 🎙️ Realtime STT System

Система распознавания речи в реальном времени с клиент-серверной архитектурой через WebSocket.

## 🏗️ Архитектура

```
┌─────────────────┐    WebSocket    ┌─────────────────────────┐
│   Rich Client   │ ──────────────► │   Docker GPU Server    │
│   (локально)    │    8011/8012    │     (genaminipc.awg)    │
└─────────────────┘                 └─────────────────────────┘
│                                   │
├─ Микрофон                         ├─ Whisper Medium (~2GB GPU)
├─ Rich интерфейс                   ├─ RTX 3090 Ti / CUDA 12.8
├─ WebSocket клиент                 ├─ Real-time транскрипция
└─ Аудио захват                     └─ Environment-based config
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

#### Стандартный терминальный клиент
```bash
# Через Makefile (рекомендуется)
make run-websocket-client

# Или напрямую
python3 websocket_rich_client.py --server genaminipc.awg
```



#### 🆕 Минималистичный STT редактор (новый!)

**Терминальный редактор в стиле mcedit БЕЗ рамок и границ:**
```bash
# Через Makefile (рекомендуется)
make run-minimal-editor

# Или напрямую
python3 websocket_minimal_editor.py
```

**Ключевые особенности:**
- ✅ **БЕЗ БОРДЮРОВ** - чистое копирование многострочного текста
- ✅ **Поддержка мыши** - выделение текста drag & drop
- ✅ **Вставка в позицию курсора** - STT текст появляется где нужно
- ✅ **Автокопирование в буфер** - каждое распознанное предложение
- ✅ **Минимальный интерфейс** - только редактор + статус строка
- ✅ **Оптимизирован для маленьких окон** - идеально для узких терминалов

**Управление:**
- **F1** - переключить STT запись (start/stop)
- **F3** - копировать весь текст в буфер
- **Ctrl+C** - выход из редактора
- **Ctrl+A** - выделить все
- **Ctrl+Q** - выход (альтернативный)

**Автокопирование:**
- **STT текст** - каждое распознанное предложение автоматически копируется
- **Выделенный текст** - любой выделенный мышью текст мгновенно копируется в буфер

#### GUI Редактор
```bash
# С автозагрузкой конфигурации
python3 start_editor.py

# Или напрямую  
python3 transcription_editor.py
```

## 🛠️ Команды управления

### Makefile команды

```bash
make help                    # Показать все команды
make run-websocket-client    # Запустить обычный WebSocket клиент
make run-minimal-editor      # Запустить минималистичный редактор
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

## 🎛️ Управление в минималистичном редакторе

**Управление:**
- **F1** - переключить STT запись (start/stop)
- **F3** - копировать весь текст в буфер
- **Ctrl+C** - выход из редактора
- **Ctrl+A** - выделить все
- **Ctrl+Q** - выход (альтернативный)

**Автокопирование:**
- **STT текст** - каждое распознанное предложение автоматически копируется
- **Выделенный текст** - любой выделенный мышью текст мгновенно копируется в буфер

## 🔧 Конфигурация

### Улучшенные параметры распознавания

**Для лучшего качества распознавания обновлены таймауты:**
```bash
POST_SPEECH_SILENCE_DURATION=1.5    # Увеличено с 0.7 до 1.5 сек
MIN_LENGTH_OF_RECORDING=2.0          # Увеличено с 1.1 до 2.0 сек
```

Эти изменения позволяют модели лучше определять конец предложений и улучшают качество распознавания длинных фраз.

### Серверная часть (Docker)

**Модели:**
- **Основная**: Whisper Medium (~2GB GPU память, высокое качество)
- **Real-time**: Whisper Tiny (~300MB GPU память, быстрый отклик)

**Железо:**
- GPU: RTX 3090 Ti (24GB VRAM, ~21GB используется)
- CUDA: 12.8 с автоматической проверкой доступности
- Порты: 8011 (control), 8012 (data)

### Конфигурация через переменные окружения

**Быстрый старт без настройки:**
```bash
# Сервер работает "из коробки" со значениями по умолчанию
docker compose up -d
```

**Кастомная конфигурация:**
```bash
# Скопируйте шаблон и отредактируйте
cp .env.example .env
# Измените параметры в .env
docker compose up -d
```

**Основные параметры** (`.env`):
```bash
# Модель и качество
WHISPER_MODEL=medium              # tiny, base, small, medium, large
LANGUAGE=ru                       # Язык распознавания
DEVICE=cuda                       # cuda (GPU) или cpu

# Улучшенные настройки VAD для качества (обновлено!)
POST_SPEECH_SILENCE_DURATION=1.5    # Пауза после речи (было 0.7)
MIN_LENGTH_OF_RECORDING=2.0          # Минимальная длительность (было 1.1)
SILERO_SENSITIVITY=0.05              # Чувствительность VAD (0.0-1.0)

# Настройки производительности  
BEAM_SIZE=5                       # Качество распознавания (1-10)
ENABLE_REALTIME_TRANSCRIPTION=true

# Сетевые параметры
CONTROL_PORT=8011                 # WebSocket control порт
DATA_PORT=8012                    # WebSocket data порт

# GUI клиент
SERVER_HOST=genaminipc.awg        # Адрес сервера для GUI
```

Подробное описание всех параметров: [CONFIGURATION.md](CONFIGURATION.md)

## 🖥️ GUI Редактор транскрипции

**Функции:**
- ✅ **Автоматический режим** - запускается и начинает запись сам
- ✅ Редактируемое текстовое поле в реальном времени  
- ✅ Автоматическое получение транскрибированного текста
- ✅ Ручное редактирование текста
- ✅ Копирование в буфер обмена одним кликом
- ✅ Простой интерфейс без лишних кнопок

**Запуск:**
```bash
python3 start_editor.py  # С автозагрузкой .env
```

Подробная документация: [README_GUI.md](README_GUI.md)

### Система логирования

Сервер выводит подробную диагностическую информацию при запуске:

- **GPU статус**: доступность CUDA, количество устройств, память
- **Конфигурация модели**: размер, язык, устройство (запрошенное vs реальное)  
- **Сетевые параметры**: порты WebSocket серверов
- **VAD настройки**: чувствительность детекции голоса
- **Настройки качества**: beam size, промпт для улучшения точности
- **Использование памяти**: до и после загрузки модели

**Пример диагностических предупреждений:**
```
WARNING: Device fallback from cuda to cpu  # GPU недоступна
DEVICE FALLBACK: cuda -> cpu               # Модель загружена на CPU
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

### Использование ресурсов (RTX 3090 Ti)

| Модель | CPU RAM | GPU VRAM | Качество | Скорость | Рекомендация |
|--------|---------|----------|----------|----------|--------------|
| tiny   | 400MB   | ~300MB   | Базовое  | Очень быстро | Слабые GPU |
| base   | 500MB   | ~500MB   | Хорошее  | Быстро | Средние GPU |
| small  | 600MB   | ~1GB     | Хорошее+ | Быстро | Хорошие GPU |
| **medium** | **900MB** | **~2GB** | **Отличное** | **Оптимально** | **Рекомендуется** |
| large  | 1.2GB   | ~5GB     | Максимальное | Медленно | Мощные GPU |

### Мониторинг ресурсов в реальном времени

```bash
# Статус Docker контейнеров
ssh genaminipc.awg "docker stats --no-stream"

# Использование GPU  
ssh genaminipc.awg "nvidia-smi"

# Логи с диагностикой GPU
ssh genaminipc.awg "docker logs realtime-stt-server-gpu --tail 30"
```

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

## 🔍 Мониторинг и диагностика

### Проверка конфигурации при запуске

Сервер выводит подробную диагностику:

```
STT SERVER CONFIGURATION
==================================================
GPU STATUS:
  CUDA Available: True
  GPU Devices Count: 1
  GPU 0: NVIDIA GeForce RTX 3090 Ti (24.0 GB)
  Current GPU Device: 0
  GPU Memory - Total: 24.0 GB
  GPU Memory - Used: 19.7 GB  
  GPU Memory - Free: 4.3 GB
MODEL SETTINGS:
  Whisper Model: medium
  Language: ru
  Configured Device: cuda
  Actual Device: cuda
NETWORK SETTINGS:
  Control Port: 8011
  Data Port: 8012
==================================================
```

### Команды мониторинга

```bash
# Логи сервера с диагностикой
ssh genaminipc.awg 'cd ~/dev/realtime-stt-system && docker compose logs -f'

# Статус контейнеров и использование ресурсов  
ssh genaminipc.awg 'cd ~/dev/realtime-stt-system && docker compose ps && docker stats --no-stream'

# GPU мониторинг
ssh genaminipc.awg 'nvidia-smi'
ssh genaminipc.awg 'watch -n 2 nvidia-smi'  # обновление каждые 2 сек

# Проверка конфигурации без перезапуска
ssh genaminipc.awg 'cd ~/dev/realtime-stt-system && docker exec realtime-stt-server-gpu python test_gpu_logging.py'
```

## 🚨 Troubleshooting

### Проблемы с GPU

**Сервер работает на CPU вместо GPU:**
```bash
# Проверить логи на предмет предупреждений
docker logs realtime-stt-server-gpu | grep -i "warning\|cuda\|device"

# Должно быть: "Actual Device: cuda", если "Actual Device: cpu" - проблема с GPU
# Проверить конфигурацию Docker Compose
cat docker-compose.yml | grep -A 10 deploy

# Должна быть раскомментирована секция:
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

**Недостаточно GPU памяти:**
```bash
# Проверить использование GPU памяти
nvidia-smi

# Если GPU память заполнена, остановить другие GPU процессы или использовать меньшую модель
# В .env изменить WHISPER_MODEL=small или WHISPER_MODEL=base
```

### Проблемы с конфигурацией

**Изменения в .env не применяются:**
```bash
# После изменения .env файла нужно перезапустить контейнер
docker compose down
docker compose up -d

# Проверить что переменные загружены
docker exec realtime-stt-server-gpu env | grep -E "WHISPER|DEVICE|PORT"
```

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

### Проверка качества распознавания

**Плохое качество распознавания:**

1. **Проверить модель и устройство:**
   ```bash
   # Должно быть: Model: medium, Actual Device: cuda
   docker logs realtime-stt-server-gpu | head -30
   ```

2. **Увеличить качество в .env:**
   ```bash
   WHISPER_MODEL=large        # Лучшая модель (если есть GPU память)
   BEAM_SIZE=10              # Увеличить для лучшего качества
   SILERO_SENSITIVITY=0.03   # Уменьшить для меньших ложных срабатываний
   ```

3. **Проверить микрофон:**
   - Используйте хороший микрофон
   - Минимизируйте фоновый шум
   - Говорите четко и громко

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

## ✨ Ключевые особенности

### 🚀 Производственная готовность
- **Environment-based конфигурация**: работает без .env файла  
- **Комплексное логирование**: полная диагностика GPU/CPU, памяти, конфигурации
- **Docker GPU поддержка**: автоматическое переключение CUDA/CPU с предупреждениями
- **Оптимизированная Docker сборка**: 6-stage build с максимальным кешированием
- **Мониторинг производительности**: real-time статистика ресурсов

### 🎛️ Гибкая настройка
- **Множественные модели**: от tiny (300MB GPU) до large (5GB GPU)
- **Автоматическая адаптация**: fallback с GPU на CPU при недоступности
- **Улучшенные VAD настройки**: увеличены таймауты для лучшего качества
- **Настраиваемые VAD**: Silero и WebRTC с регулируемой чувствительностью  
- **Quality tuning**: beam size, промпты, языковые настройки

### 🖊️ Минималистичный редактор
- **БЕЗ БОРДЮРОВ** - чистое копирование многострочного текста
- **Поддержка мыши** - выделение текста drag & drop
- **Вставка в позицию курсора** - STT текст появляется где нужно
- **Автокопирование в буфер** - каждое распознанное предложение
- **Минимальный интерфейс** - только редактор + статус строка
- **Оптимизирован для маленьких окон** - идеально для узких терминалов

### 📊 Диагностика и отладка  
- **GPU memory tracking**: мониторинг до/после загрузки модели
- **Configuration validation**: проверка соответствия настроек и реального состояния
- **Performance metrics**: использование CPU, GPU, RAM в реальном времени
- **Comprehensive logging**: структурированные логи для Docker deployments

## 🎯 Roadmap

- [ ] Web интерфейс для управления и мониторинга
- [ ] Поддержка множественных клиентов с load balancing
- [ ] REST API для интеграции с другими приложениями  
- [ ] Prometheus метрики и Grafana дашборды
- [ ] Поддержка дополнительных языков (EN, DE, FR)
- [ ] Streaming API для real-time интеграций

## 👥 Contributing

1. Fork проекта
2. Создайте feature ветку (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## 📄 License

Этот проект использует MIT License. Подробности в файле `LICENSE`.

---

## 🎉 Готов к использованию!

**Быстрый старт:**
```bash
# 1. Запуск сервера (автоматическая конфигурация)
ssh genaminipc.awg "cd ~/dev/realtime-stt-system && docker compose up -d"

# 2. Запуск клиента  
make run-websocket-client

# 3. Начинайте говорить! 🎤
```

**Проверка работы GPU:**
```bash
# Убедитесь что в логах: "Actual Device: cuda" и "Model successfully loaded on GPU!"
ssh genaminipc.awg "docker logs realtime-stt-server-gpu | head -30"
```

🚀 **Высокое качество распознавания русской речи с GPU ускорением!**