# Makefile для Realtime STT System
# Клиент-серверная архитектура через WebSocket

# Переменные
PYTHON := python3

# Цвета для вывода
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help run-minimal-editor docker-build docker-run docker-stop docker-logs docker-status deploy remote-logs remote-status clean

# Помощь (команда по умолчанию)
help:
	@echo "$(BLUE)╔════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║          Realtime STT System Commands         ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Клиент команды:$(NC)"
	@echo "  $(YELLOW)make run-minimal-editor$(NC)       - Минималистичный STT редактор без рамок"
	@echo ""
	@echo "$(GREEN)Docker команды:$(NC)"
	@echo "  $(YELLOW)make docker-build$(NC)         - Сборка Docker образа"
	@echo "  $(YELLOW)make docker-run$(NC)           - Запуск контейнера"
	@echo "  $(YELLOW)make docker-stop$(NC)          - Остановка контейнера"
	@echo "  $(YELLOW)make docker-logs$(NC)          - Просмотр логов"
	@echo "  $(YELLOW)make docker-status$(NC)        - Статус и ресурсы"
	@echo ""
	@echo "$(GREEN)Удаленный сервер:$(NC)"
	@echo "  $(YELLOW)make deploy$(NC)               - Деплой на genaminipc.awg"
	@echo "  $(YELLOW)make remote-logs$(NC)          - Логи с сервера"
	@echo "  $(YELLOW)make remote-status$(NC)        - Статус сервера"
	@echo ""
	@echo "$(GREEN)Утилиты:$(NC)"
	@echo "  $(YELLOW)make clean$(NC)                - Очистка проекта"

# ════════════════════════════════════════════════════════════════
# Клиент команды
# ════════════════════════════════════════════════════════════════

run-minimal-editor:
	@echo "$(GREEN)✏️  Запуск минималистичного STT редактора...$(NC)"
	@echo "$(BLUE)📝 Терминальный редактор в стиле mcedit БЕЗ рамок$(NC)"
	@echo "$(BLUE)🎤 F1 - переключить запись STT, автокопирование при выделении мышью$(NC)"
	@echo "$(BLUE)🌐 Конфигурация загружается из .env файла$(NC)"
	@$(PYTHON) websocket_minimal_editor.py

# ════════════════════════════════════════════════════════════════
# Docker команды для локальной разработки
# ════════════════════════════════════════════════════════════════

docker-build:
	@echo "$(BLUE)🐳 Сборка Docker образа с GPU поддержкой...$(NC)"
	docker compose build

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

# ════════════════════════════════════════════════════════════════
# Команды для удаленного сервера
# ════════════════════════════════════════════════════════════════

deploy:
	@echo "$(BLUE)🌐 Деплой на удаленный сервер...$(NC)"
	git push origin master
	ssh genaminipc.awg "cd ~/dev/realtime-stt-system && git pull && docker compose down && docker compose up --build -d"
	@echo "$(GREEN)✅ Деплой завершен$(NC)"

remote-logs:
	@echo "$(BLUE)📋 Логи с удаленного сервера:$(NC)"
	ssh genaminipc.awg "cd ~/dev/realtime-stt-system && docker compose logs -f"

remote-status:
	@echo "$(BLUE)📊 Статус на удаленном сервере:$(NC)"
	ssh genaminipc.awg "cd ~/dev/realtime-stt-system && docker compose ps && echo && docker stats --no-stream"

# ════════════════════════════════════════════════════════════════
# Утилиты
# ════════════════════════════════════════════════════════════════

clean:
	@echo "$(YELLOW)🧹 Очистка проекта...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Проект очищен$(NC)"

test-connection:
	@echo "$(BLUE)🔌 Тестирование подключения к серверу...$(NC)"
	@timeout 5 bash -c "echo > /dev/tcp/genaminipc.awg/8011" && echo "$(GREEN)✅ Порт 8011 доступен$(NC)" || echo "$(RED)❌ Порт 8011 недоступен$(NC)"
	@timeout 5 bash -c "echo > /dev/tcp/genaminipc.awg/8012" && echo "$(GREEN)✅ Порт 8012 доступен$(NC)" || echo "$(RED)❌ Порт 8012 недоступен$(NC)"

# Команда по умолчанию
.DEFAULT_GOAL := help

docker-build-no-cache:
	@echo "$(YELLOW)🐳 Принудительная сборка без кеша (медленно!)...$(NC)"
	docker compose build --no-cache --progress=plain

