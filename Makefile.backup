# Makefile для Simple STT Demo
# Автоматизация установки и запуска приложения распознавания речи

# Переменные
PYTHON := python3
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip
VENV_ACTIVATE := . $(VENV_DIR)/bin/activate

# Определение ОС
UNAME_S := $(shell uname -s)

# Цвета для вывода
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help install install-deps install-python run check clean test gpu-install cpu-install update lint format docker-build docker-run docker-stop docker-logs docker-gpu-build docker-gpu-run

# Помощь (команда по умолчанию)
help:
	@echo "$(BLUE)╔════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║     Simple STT Demo - Makefile Commands       ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Основные команды:$(NC)"
	@echo "  $(YELLOW)make install$(NC)      - Полная установка с виртуальным окружением"
	@echo "  $(YELLOW)make run$(NC)          - Запуск простого приложения"
	@echo "  $(YELLOW)make run-rich$(NC)     - Запуск с Rich интерфейсом (рекомендуется)"
	@echo "  $(YELLOW)make check$(NC)        - Проверка системы и зависимостей"
	@echo ""
	@echo "$(GREEN)Варианты установки:$(NC)"
	@echo "  $(YELLOW)make gpu-install$(NC)  - Установка с поддержкой GPU (CUDA 12.1)"
	@echo "  $(YELLOW)make cpu-install$(NC)  - Установка только для CPU"
	@echo ""
	@echo "$(GREEN)Дополнительные команды:$(NC)"
	@echo "  $(YELLOW)make test$(NC)         - Тестовый запуск простого приложения"
	@echo "  $(YELLOW)make test-rich$(NC)    - Тестовый запуск Rich приложения"
	@echo "  $(YELLOW)make clean$(NC)        - Удаление виртуального окружения"
	@echo "  $(YELLOW)make update$(NC)       - Обновление зависимостей"
	@echo "  $(YELLOW)make lint$(NC)         - Проверка кода"
	@echo "  $(YELLOW)make format$(NC)       - Форматирование кода"

# Полная установка
install: check-system create-venv install-deps install-python
	@echo ""
	@echo "$(GREEN)✅ Установка завершена успешно!$(NC)"
	@echo "$(YELLOW)Запустите приложение: make run$(NC)"

# Установка с GPU
gpu-install: check-system create-venv install-deps install-python-gpu
	@echo ""
	@echo "$(GREEN)✅ Установка с GPU завершена успешно!$(NC)"
	@echo "$(YELLOW)Запустите приложение: make run$(NC)"

# Установка только CPU
cpu-install: check-system create-venv install-deps install-python-cpu
	@echo ""
	@echo "$(GREEN)✅ Установка для CPU завершена успешно!$(NC)"
	@echo "$(YELLOW)Запустите приложение: make run$(NC)"

# Проверка системы
check-system:
	@echo "$(BLUE)🔍 Проверка системы...$(NC)"
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "$(RED)❌ Python3 не найден. Установите Python 3.8+$(NC)"; exit 1; }
	@echo "$(GREEN)✓ Python найден:$(NC) $$($(PYTHON) --version)"
	
ifeq ($(UNAME_S),Linux)
	@echo "$(GREEN)✓ ОС: Linux$(NC)"
	@echo "$(YELLOW)⚠ Убедитесь, что установлены системные пакеты:$(NC)"
	@echo "  sudo apt-get install python3-dev python3-venv portaudio19-dev ffmpeg"
else ifeq ($(UNAME_S),Darwin)
	@echo "$(GREEN)✓ ОС: macOS$(NC)"
	@echo "$(YELLOW)⚠ Убедитесь, что установлены:$(NC)"
	@echo "  brew install portaudio ffmpeg"
endif

# Создание виртуального окружения
create-venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(BLUE)📦 Создание виртуального окружения...$(NC)"; \
		$(PYTHON) -m venv $(VENV_DIR); \
		$(VENV_PIP) install --upgrade pip setuptools wheel; \
		echo "$(GREEN)✓ Виртуальное окружение создано$(NC)"; \
	else \
		echo "$(GREEN)✓ Виртуальное окружение уже существует$(NC)"; \
	fi

# Установка системных зависимостей
install-deps:
	@echo "$(BLUE)📦 Проверка системных зависимостей...$(NC)"
ifeq ($(UNAME_S),Linux)
	@which portaudio >/dev/null 2>&1 || echo "$(YELLOW)⚠ Рекомендуется: sudo apt-get install portaudio19-dev$(NC)"
	@which ffmpeg >/dev/null 2>&1 || echo "$(YELLOW)⚠ Рекомендуется: sudo apt-get install ffmpeg$(NC)"
else ifeq ($(UNAME_S),Darwin)
	@which portaudio >/dev/null 2>&1 || echo "$(YELLOW)⚠ Рекомендуется: brew install portaudio$(NC)"
	@which ffmpeg >/dev/null 2>&1 || echo "$(YELLOW)⚠ Рекомендуется: brew install ffmpeg$(NC)"
endif

# Установка Python зависимостей (автоопределение GPU)
install-python:
	@echo "$(BLUE)📦 Установка Python пакетов...$(NC)"
	@$(VENV_PIP) install --quiet colorama rich pyperclip
	@$(VENV_PIP) install --quiet RealtimeSTT
	@$(VENV_PIP) install --quiet faster-whisper
	
	@echo "$(BLUE)🔍 Проверка наличия GPU...$(NC)"
	@if command -v nvidia-smi >/dev/null 2>&1; then \
		echo "$(GREEN)✓ GPU обнаружен, устанавливаю PyTorch с CUDA 12.1...$(NC)"; \
		$(VENV_PIP) install --quiet torch==2.5.1+cu121 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121; \
	else \
		echo "$(YELLOW)ℹ GPU не обнаружен, устанавливаю CPU версию PyTorch...$(NC)"; \
		$(VENV_PIP) install --quiet torch torchaudio; \
	fi
	@echo "$(GREEN)✓ Python пакеты установлены$(NC)"

# Принудительная установка GPU версии
install-python-gpu:
	@echo "$(BLUE)📦 Установка Python пакетов с GPU поддержкой...$(NC)"
	@$(VENV_PIP) install --quiet colorama rich pyperclip
	@$(VENV_PIP) install --quiet RealtimeSTT
	@$(VENV_PIP) install --quiet faster-whisper
	@$(VENV_PIP) install --quiet torch==2.5.1+cu121 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
	@echo "$(GREEN)✓ Python пакеты с GPU установлены$(NC)"

# Принудительная установка CPU версии
install-python-cpu:
	@echo "$(BLUE)📦 Установка Python пакетов для CPU...$(NC)"
	@$(VENV_PIP) install --quiet colorama rich pyperclip
	@$(VENV_PIP) install --quiet RealtimeSTT
	@$(VENV_PIP) install --quiet faster-whisper
	@$(VENV_PIP) install --quiet torch torchaudio
	@echo "$(GREEN)✓ Python пакеты для CPU установлены$(NC)"

# Запуск простого приложения
run:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)❌ Виртуальное окружение не найдено!$(NC)"; \
		echo "$(YELLOW)Выполните: make install$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)🚀 Запуск Simple STT Demo...$(NC)"
	@echo ""
	@$(VENV_PYTHON) simple_stt_demo.py

# Запуск Rich приложения (рекомендуется)
run-rich:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)❌ Виртуальное окружение не найдено!$(NC)"; \
		echo "$(YELLOW)Выполните: make install$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)🚀 Запуск Rich STT Demo...$(NC)"
	@echo ""
	@$(VENV_PYTHON) rich_stt_demo.py

# Тестовый запуск простого приложения
test:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)❌ Виртуальное окружение не найдено!$(NC)"; \
		echo "$(YELLOW)Выполните: make install$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)🧪 Тестовый запуск простого приложения (10 секунд)...$(NC)"
	@timeout 10 $(VENV_PYTHON) simple_stt_demo.py || true

# Тестовый запуск Rich приложения
test-rich:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)❌ Виртуальное окружение не найдено!$(NC)"; \
		echo "$(YELLOW)Выполните: make install$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)🧪 Тестовый запуск Rich приложения (10 секунд)...$(NC)"
	@timeout 10 $(VENV_PYTHON) rich_stt_demo.py || true

# Проверка установки и зависимостей
check:
	@echo "$(BLUE)╔════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║            Проверка системы                   ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════╝$(NC)"
	@echo ""
	
	@echo "$(BLUE)📋 Системная информация:$(NC)"
	@echo "  ОС: $$(uname -s) $$(uname -r)"
	@echo "  Python: $$($(PYTHON) --version 2>&1)"
	
	@echo ""
	@echo "$(BLUE)📦 Виртуальное окружение:$(NC)"
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "$(GREEN)  ✓ Найдено в $(VENV_DIR)$(NC)"; \
		echo "  Python: $$($(VENV_PYTHON) --version 2>&1)"; \
	else \
		echo "$(YELLOW)  ⚠ Не найдено$(NC)"; \
	fi
	
	@echo ""
	@echo "$(BLUE)🔧 Системные зависимости:$(NC)"
	@command -v ffmpeg >/dev/null 2>&1 && echo "$(GREEN)  ✓ ffmpeg$(NC)" || echo "$(YELLOW)  ⚠ ffmpeg не найден$(NC)"
	@command -v portaudio >/dev/null 2>&1 && echo "$(GREEN)  ✓ portaudio$(NC)" || echo "$(YELLOW)  ⚠ portaudio не проверен$(NC)"
	
	@echo ""
	@echo "$(BLUE)🎮 GPU:$(NC)"
	@if command -v nvidia-smi >/dev/null 2>&1; then \
		echo "$(GREEN)  ✓ CUDA доступна$(NC)"; \
		nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1 | sed 's/^/  /'; \
	else \
		echo "$(YELLOW)  ⚠ CUDA не обнаружена (будет использоваться CPU)$(NC)"; \
	fi
	
	@if [ -d "$(VENV_DIR)" ]; then \
		echo ""; \
		echo "$(BLUE)📚 Python пакеты:$(NC)"; \
		@$(VENV_PYTHON) -c "import RealtimeSTT; print('  ✓ RealtimeSTT:', RealtimeSTT.__version__ if hasattr(RealtimeSTT, '__version__') else 'установлен')" 2>/dev/null || echo "$(YELLOW)  ⚠ RealtimeSTT не установлен$(NC)"; \
		@$(VENV_PYTHON) -c "import faster_whisper; print('  ✓ faster-whisper установлен')" 2>/dev/null || echo "$(YELLOW)  ⚠ faster-whisper не установлен$(NC)"; \
		@$(VENV_PYTHON) -c "import torch; print(f'  ✓ PyTorch: {torch.__version__}'); print(f'    CUDA: {torch.cuda.is_available()}')" 2>/dev/null || echo "$(YELLOW)  ⚠ PyTorch не установлен$(NC)"; \
	fi
	
	@echo ""
	@if [ -d "$(VENV_DIR)" ] && $(VENV_PYTHON) -c "import RealtimeSTT" 2>/dev/null; then \
		echo "$(GREEN)✅ Система готова к работе!$(NC)"; \
		echo "$(YELLOW)Запустите: make run-rich (рекомендуется) или make run$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Требуется установка$(NC)"; \
		echo "$(YELLOW)Выполните: make install$(NC)"; \
	fi

# Обновление зависимостей
update:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)❌ Виртуальное окружение не найдено!$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)📦 Обновление пакетов...$(NC)"
	@$(VENV_PIP) install --upgrade pip setuptools wheel
	@$(VENV_PIP) install --upgrade RealtimeSTT faster-whisper colorama
	@echo "$(GREEN)✓ Пакеты обновлены$(NC)"

# Очистка
clean:
	@echo "$(YELLOW)🗑️  Удаление виртуального окружения...$(NC)"
	@rm -rf $(VENV_DIR)
	@rm -rf __pycache__
	@rm -rf *.pyc
	@rm -rf .pytest_cache
	@echo "$(GREEN)✓ Очистка завершена$(NC)"

# Проверка кода линтером
lint:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)❌ Виртуальное окружение не найдено!$(NC)"; \
		exit 1; \
	fi
	@$(VENV_PIP) install --quiet flake8
	@echo "$(BLUE)🔍 Проверка кода...$(NC)"
	@$(VENV_PYTHON) -m flake8 simple_stt_demo.py --max-line-length=100 --ignore=E501,W503

# Форматирование кода
format:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)❌ Виртуальное окружение не найдено!$(NC)"; \
		exit 1; \
	fi
	@$(VENV_PIP) install --quiet black
	@echo "$(BLUE)🎨 Форматирование кода...$(NC)"
	@$(VENV_PYTHON) -m black simple_stt_demo.py
	@echo "$(GREEN)✓ Код отформатирован$(NC)"

# Установка dev зависимостей
dev-install: install
	@echo "$(BLUE)📦 Установка инструментов разработки...$(NC)"
	@$(VENV_PIP) install --quiet flake8 black pytest ipython
	@echo "$(GREEN)✓ Dev инструменты установлены$(NC)"

# По умолчанию показываем помощь
.DEFAULT_GOAL := help
# Docker команды
docker-up:
	@echo "$(GREEN)🐳 Запуск Docker сервера...$(NC)"
	@mkdir -p models logs
	@docker-compose up --build -d
	@echo "$(GREEN)✓ Docker сервер запущен на localhost:8011-8012$(NC)"

docker-down:
	@echo "$(YELLOW)🐳 Остановка Docker сервера...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Docker сервер остановлен$(NC)"

docker-logs:
	@docker-compose logs -f stt-server

docker-rebuild:
	@echo "$(BLUE)🐳 Пересборка Docker образа...$(NC)"
	@docker-compose down
	@docker-compose build --no-cache
	@docker-compose up -d
	@echo "$(GREEN)✓ Docker сервер пересобран и запущен$(NC)"

# WebSocket клиенты
client:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)❌ Виртуальное окружение не найдено!$(NC)"; \
		echo "$(YELLOW)Выполните: make install$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)🌐 Запуск WebSocket клиента...$(NC)"
	@$(VENV_PYTHON) websocket_rich_client.py

client-server:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)❌ Виртуальное окружение не найдено!$(NC)"; \
		echo "$(YELLOW)Выполните: make install$(NC)"; \
		exit 1; \
	fi
	@read -p "Введите IP адрес сервера: " server_ip; \
	echo "$(GREEN)🌐 Подключение к серверу $$server_ip...$(NC)"; \
	$(VENV_PYTHON) websocket_rich_client.py --server $$server_ip

# ════════════════════════════════════════════════════════════════
# Docker команды для удаленного сервера
# ════════════════════════════════════════════════════════════════

docker-build:
	@echo "$(BLUE)🐳 Сборка Docker образа с GPU поддержкой...$(NC)"
	docker compose build --no-cache

docker-run:
	@echo "$(BLUE)🚀 Запуск Docker контейнера...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✅ Сервер запущен на портах 8011 (control) и 8012 (data)$(NC)"

docker-stop:
	@echo "$(YELLOW)⏹️  Остановка Docker контейнера...$(NC)"
	docker compose down

docker-restart: docker-stop docker-run
	@echo "$(GREEN)🔄 Перезапуск контейнера завершен$(NC)"

docker-logs:
	@echo "$(BLUE)📋 Логи Docker контейнера:$(NC)"
	docker compose logs -f

docker-status:
	@echo "$(BLUE)📊 Статус Docker контейнеров:$(NC)"
	docker compose ps
	@echo ""
	@echo "$(BLUE)💾 Использование ресурсов:$(NC)"
	docker stats --no-stream

docker-clean:
	@echo "$(YELLOW)🧹 Очистка Docker ресурсов...$(NC)"
	docker compose down
	docker system prune -f
	@echo "$(GREEN)✅ Очистка завершена$(NC)"

# Команды для удаленного сервера
deploy:
	@echo "$(BLUE)🌐 Деплой на удаленный сервер...$(NC)"
	git push origin master
	ssh genaminipc.awg "cd realtime-stt-system && git pull && docker compose down && docker compose up --build -d"
	@echo "$(GREEN)✅ Деплой завершен$(NC)"

remote-logs:
	@echo "$(BLUE)📋 Логи с удаленного сервера:$(NC)"
	ssh genaminipc.awg "cd realtime-stt-system && docker compose logs -f"

remote-status:
	@echo "$(BLUE)📊 Статус на удаленном сервере:$(NC)"
	ssh genaminipc.awg "cd realtime-stt-system && docker compose ps && echo && docker stats --no-stream"

docker-build-verbose:
	@echo "$(BLUE)🐳 Подробная сборка Docker образа с анализом кеширования...$(NC)"
	docker compose build --progress=plain --no-cache

docker-cache-info:
	@echo "$(BLUE)📊 Информация о Docker кеше:$(NC)"
	docker system df
	@echo ""
	@echo "$(BLUE)🔍 Docker образы:$(NC)"
	docker images | grep realtime-stt

docker-optimize:
	@echo "$(YELLOW)🧹 Очистка неиспользуемого кеша...$(NC)"
	docker system prune -f
	docker builder prune -f

run-websocket-client:
	@echo "$(GREEN)🌐 Запуск WebSocket клиента для удаленного сервера...$(NC)"
	@echo "$(BLUE)Подключение к серверу: genaminipc.awg$(NC)"
	@python3 websocket_rich_client.py --server genaminipc.awg
