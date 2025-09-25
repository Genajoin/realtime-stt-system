# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a real-time speech-to-text (STT) system with client-server WebSocket architecture. The system consists of:
- **Server**: Docker containerized STT server running Whisper models with GPU support
- **Clients**: Multiple Python WebSocket clients (terminal-based and GUI)

## Architecture

```
┌─────────────────┐    WebSocket    ┌─────────────────────────┐
│   Client Apps   │ ──────────────► │   Docker GPU Server    │
│   (local)       │  ports 8011/8012│  (genaminipc.awg)      │
└─────────────────┘                 └─────────────────────────┘
```

- **Server**: Located in `server/` directory, runs in Docker with NVIDIA GPU support
- **Clients**: Root directory Python files for different client types
- **Communication**: WebSocket on ports 8011 (control) and 8012 (data)

## Core Components

### Server (`server/`)
- `stt_server.py`: Main STT server using RealtimeSTT and Whisper
- `env_config.py`: Environment configuration management with defaults
- `Dockerfile`: Multi-stage Docker build optimized for CUDA/GPU
- `requirements-server.txt`: Server Python dependencies

### Clients (root directory)
- `websocket_minimal_editor.py`: Minimal terminal editor without borders
- `transcription_editor.py`: GUI editor with tkinter
- `start_editor.py`: Auto-configuring GUI launcher

## Configuration

The system uses environment-based configuration with sensible defaults:

- **Required file**: `.env.example` (template)
- **Optional file**: `.env` (user configuration)
- **Config module**: `server/env_config.py` handles defaults and validation

Key configuration categories:
- Whisper models (tiny, base, small, medium, large)
- Device selection (cuda/cpu with automatic fallback)
- VAD (Voice Activity Detection) settings
- WebSocket ports and networking
- Quality parameters (beam size, timeouts)

## Development Commands

### Client Operations
```bash
make run-websocket-client     # Standard WebSocket client
make run-editable-client      # Full-featured editable client
make run-simple-editable      # Stable simplified editable client
```

### Docker Server Management
```bash
make docker-build            # Build Docker image
make docker-run              # Start container
make docker-stop             # Stop container
make docker-logs             # View container logs
make docker-status           # Container status and resource usage
```

### Remote Server Operations
```bash
make deploy                  # Deploy to genaminipc.awg server
make remote-logs             # View remote server logs
make remote-status           # Check remote server status
```

### Development Utilities
```bash
make clean                   # Clean Python cache files and logs
make test-connection         # Test WebSocket port connectivity
```

## Testing

- Test files in `server/` directory: `test_*.py`
- No centralized test runner - individual test files
- GPU configuration testing: `server/test_gpu_logging.py`
- Environment testing: `server/test_config.py`

## Docker Architecture

Multi-stage Docker build with layers:
1. **pytorch-base**: CUDA-enabled PyTorch foundation
2. **system-libs**: System dependencies via conda
3. **heavy-deps**: Large Python libraries (RealtimeSTT, faster-whisper)
4. **light-deps**: Lightweight Python dependencies
5. **runtime-config**: Environment setup
6. **production**: Application code

Benefits: Fast rebuilds when only application code changes (~20s vs ~8min full build)

## GPU Support

- Primary target: NVIDIA RTX 3090 Ti with CUDA 12.8
- Automatic fallback: CUDA → CPU if GPU unavailable
- Memory requirements vary by model (300MB for tiny → 5GB for large)
- GPU reservation configured in `docker-compose.yml`

## Multilingual Support

Enhanced for Russian-English mixed technical terminology:
- Language setting: `LANGUAGE=auto` for automatic detection
- Custom initial prompt with IT terminology
- Optimized beam search settings for multilingual content
- VAD timeouts tuned for mixed-language speech patterns

## Key Files for Understanding

- `README.md`: Comprehensive user documentation
- `Makefile`: All available commands with descriptions
- `docker-compose.yml`: Docker service definition
- `server/env_config.py`: Configuration system implementation
- `.env.example`: Configuration template with all options

## Development Notes

- All client applications load configuration from `.env` file
- Server runs in Docker with volume mounts for models/cache/logs
- WebSocket protocol uses separate control and data channels
- Rich terminal UI used for enhanced user experience
- Multiple client variants for different use cases (standard, editable, GUI)