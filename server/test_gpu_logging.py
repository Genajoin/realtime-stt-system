#!/usr/bin/env python3
"""
Тест нового GPU логирования.
"""

import sys
import os
import logging

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from env_config import env_config
    
    # Настройка логирования как в сервере
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    logger = logging.getLogger('STTServer')
    
    class GPUTester:
        def log_gpu_status(self):
            """Проверка и логирование реального состояния GPU."""
            logger.info("GPU STATUS:")
            
            try:
                import torch
                
                # Проверка доступности CUDA
                cuda_available = torch.cuda.is_available()
                logger.info(f"  CUDA Available: {cuda_available}")
                
                if cuda_available:
                    # Информация о GPU устройствах
                    device_count = torch.cuda.device_count()
                    logger.info(f"  GPU Devices Count: {device_count}")
                    
                    for i in range(device_count):
                        gpu_name = torch.cuda.get_device_name(i)
                        gpu_memory = torch.cuda.get_device_properties(i).total_memory
                        gpu_memory_gb = gpu_memory / (1024**3)
                        logger.info(f"  GPU {i}: {gpu_name} ({gpu_memory_gb:.1f} GB)")
                    
                    # Проверка текущего GPU устройства
                    if device_count > 0:
                        current_device = torch.cuda.current_device()
                        logger.info(f"  Current GPU Device: {current_device}")
                        
                        # Проверка свободной памяти
                        try:
                            free_memory = torch.cuda.mem_get_info()[0]
                            total_memory = torch.cuda.mem_get_info()[1]
                            used_memory = total_memory - free_memory
                            
                            logger.info(f"  GPU Memory - Total: {total_memory / (1024**3):.1f} GB")
                            logger.info(f"  GPU Memory - Used: {used_memory / (1024**3):.1f} GB")
                            logger.info(f"  GPU Memory - Free: {free_memory / (1024**3):.1f} GB")
                        except Exception as e:
                            logger.warning(f"  Could not get GPU memory info: {e}")
                else:
                    logger.warning("  CUDA not available - will use CPU")
                    
            except ImportError:
                logger.error("  PyTorch not available - cannot check GPU status")
            except Exception as e:
                logger.error(f"  Error checking GPU status: {e}")
            
            logger.info("-" * 30)
        
        def get_actual_device(self):
            """Определение реального устройства, которое будет использоваться."""
            try:
                import torch
                if torch.cuda.is_available():
                    return "cuda"
                else:
                    return "cpu"
            except ImportError:
                return "cpu"
    
    if __name__ == '__main__':
        logger.info("Testing GPU logging system...")
        logger.info("=" * 50)
        
        tester = GPUTester()
        
        # Тест GPU статуса
        tester.log_gpu_status()
        
        # Тест определения устройства
        configured_device = env_config.get('device')
        actual_device = tester.get_actual_device()
        
        logger.info("DEVICE COMPARISON:")
        logger.info(f"  Configured Device: {configured_device}")
        logger.info(f"  Actual Device: {actual_device}")
        
        if configured_device != actual_device:
            logger.warning(f"  WARNING: Device fallback from {configured_device} to {actual_device}")
        else:
            logger.info(f"  SUCCESS: Device configuration matches actual device")
        
        logger.info("=" * 50)
        logger.info("GPU logging test completed successfully!")
        
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)