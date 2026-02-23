#!/usr/bin/env python3
"""
HTTP API сервер для загрузки и транскрипции аудио файлов.
Работает параллельно с WebSocket сервером для real-time транскрипции.
"""

import logging
import asyncio
from typing import Optional
from aiohttp import web
from env_config import env_config
from file_transcriber import FileTranscriber

logger = logging.getLogger('HTTPServer')

class HTTPTranscribeServer:
    """HTTP сервер для обработки загрузки файлов и транскрипции."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8013):
        """
        Инициализация HTTP сервера.
        
        Args:
            host: IP адрес для прослушивания
            port: Порт для HTTP сервера
        """
        self.host = host
        self.port = port
        self.app = web.Application(
            client_max_size=env_config.get('max_file_size_mb', 500) * 1024 * 1024
        )
        self.transcriber: Optional[FileTranscriber] = None
        
        # Настройка routes
        self.app.router.add_post('/transcribe', self.handle_transcribe)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/info', self.handle_info)
        
        logger.info(f"HTTP сервер инициализирован на {host}:{port}")
    
    async def initialize_transcriber(self):
        """Инициализация транскрайбера в event loop."""
        try:
            model_name = env_config.get('file_model', 'large')
            device = env_config.get('device', 'cuda')
            language = env_config.get('language')
            
            logger.info(f"Инициализация FileTranscriber: модель={model_name}, устройство={device}")
            
            # Создаем транскрайбер в отдельном потоке чтобы не блокировать event loop
            loop = asyncio.get_event_loop()
            self.transcriber = await loop.run_in_executor(
                None,
                lambda: FileTranscriber(model_name=model_name, device=device, language=language)
            )
            
            logger.info("FileTranscriber успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации транскрайбера: {e}")
            raise
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """
        Health check endpoint.
        
        GET /health
        
        Returns:
            JSON: {"status": "ok", "transcriber_ready": bool}
        """
        return web.json_response({
            "status": "ok",
            "transcriber_ready": self.transcriber is not None
        })
    
    async def handle_info(self, request: web.Request) -> web.Response:
        """
        Информация о сервере.
        
        GET /info
        
        Returns:
            JSON с информацией о конфигурации
        """
        info = {
            "model": env_config.get('file_model', 'large'),
            "device": env_config.get('device', 'cuda'),
            "language": env_config.get('language', 'auto'),
            "max_file_size_mb": env_config.get('max_file_size_mb', 500),
            "supported_formats": ["mp3", "wav", "m4a", "flac", "ogg", "opus"],
            "transcriber_ready": self.transcriber is not None
        }
        return web.json_response(info)
    
    async def handle_transcribe(self, request: web.Request) -> web.Response:
        """
        Endpoint для транскрипции загруженного аудио файла.
        
        POST /transcribe
        Content-Type: multipart/form-data
        
        Form fields:
            - file: аудио файл (обязательно)
            - beam_size: размер beam search (опционально, default=5)
            - language: язык аудио (опционально, override конфига)
            - vad_filter: использовать VAD фильтр (опционально, default=true)
            - include_segments: включить сегменты с временными метками (опционально, default=false)
        
        Returns:
            JSON:
            {
                "text": str,  # Полный текст транскрипции
                "language": str,  # Определенный язык
                "duration": float,  # Длительность аудио в секундах
                "segments": [...]  # Сегменты (если include_segments=true)
            }
        """
        if not self.transcriber:
            return web.json_response(
                {"error": "Транскрайбер не инициализирован"},
                status=503
            )
        
        try:
            # Читаем multipart form data
            reader = await request.multipart()
            
            audio_data = None
            audio_filename = None
            beam_size = 5
            language = None
            vad_filter = False
            include_segments = False
            
            # Парсим form fields
            async for field in reader:
                if field.name == 'file':
                    # Читаем файл
                    audio_filename = field.filename
                    audio_data = await field.read()
                    logger.info(f"Получен файл: {audio_filename}, размер: {len(audio_data) / (1024*1024):.2f}MB")
                    
                elif field.name == 'beam_size':
                    try:
                        beam_size = int(await field.text())
                    except ValueError:
                        pass
                        
                elif field.name == 'language':
                    language_text = await field.text()
                    if language_text and language_text.lower() not in ['auto', 'none', 'null']:
                        language = language_text
                        
                elif field.name == 'vad_filter':
                    vad_text = await field.text()
                    vad_filter = vad_text.lower() in ['true', '1', 'yes']
                    
                elif field.name == 'include_segments':
                    seg_text = await field.text()
                    include_segments = seg_text.lower() in ['true', '1', 'yes']
            
            # Проверяем что файл загружен
            if not audio_data:
                return web.json_response(
                    {"error": "Файл не загружен. Используйте поле 'file' в multipart/form-data"},
                    status=400
                )
            
            # Определяем расширение файла
            if audio_filename:
                file_ext = '.' + audio_filename.rsplit('.', 1)[-1].lower()
            else:
                file_ext = '.mp3'  # По умолчанию
            
            logger.info(f"Начало транскрипции: beam_size={beam_size}, language={language}, "
                       f"vad_filter={vad_filter}, file_ext={file_ext}")
            
            # Выполняем транскрипцию в отдельном потоке
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.transcriber.transcribe_bytes(
                    audio_data,
                    file_extension=file_ext,
                    beam_size=beam_size,
                    vad_filter=vad_filter
                )
            )
            
            # Формируем ответ
            response_data = {
                "text": result["text"],
                "language": result["language"],
                "duration": result["duration"]
            }
            
            # Добавляем сегменты если запрошено
            if include_segments:
                response_data["segments"] = result["segments"]
            
            logger.info(f"Транскрипция завершена: {len(result['text'])} символов, "
                       f"{result['duration']:.2f} сек")
            
            return web.json_response(response_data)
            
        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {e}", exc_info=True)
            return web.json_response(
                {"error": f"Ошибка транскрипции: {str(e)}"},
                status=500
            )
    
    async def start(self):
        """Запуск HTTP сервера."""
        try:
            # Инициализируем транскрайбер
            await self.initialize_transcriber()
            
            # Запускаем сервер
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
            
            logger.info(f"HTTP API сервер запущен на http://{self.host}:{self.port}")
            logger.info("Доступные endpoints:")
            logger.info(f"  POST http://{self.host}:{self.port}/transcribe - транскрипция файла")
            logger.info(f"  GET  http://{self.host}:{self.port}/health - проверка состояния")
            logger.info(f"  GET  http://{self.host}:{self.port}/info - информация о сервере")
            
            # Держим сервер запущенным
            return runner
            
        except Exception as e:
            logger.error(f"Ошибка запуска HTTP сервера: {e}")
            raise

async def run_http_server():
    """Запуск HTTP сервера как standalone приложение."""
    port = env_config.get('http_port', 8013)
    server = HTTPTranscribeServer(port=port)
    runner = await server.start()
    
    try:
        # Ждем бесконечно
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Остановка HTTP сервера...")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    # Запуск сервера
    asyncio.run(run_http_server())
