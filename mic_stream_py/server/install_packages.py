#!/usr/bin/env python3
"""
Утилита для автоматической проверки и установки пакетов Python.
Упрощенная версия для Docker контейнера.
"""

import importlib
import subprocess
import sys

def check_and_install_packages(packages):
    """
    Проверяет наличие пакетов и устанавливает отсутствующие.
    
    Args:
        packages (list): Список словарей с информацией о пакетах
    """
    for package_info in packages:
        module_name = package_info['module_name']
        install_name = package_info.get('install_name', module_name)
        attribute = package_info.get('attribute')
        
        try:
            # Пытаемся импортировать модуль
            module = importlib.import_module(module_name)
            
            # Если указан атрибут, проверяем его наличие
            if attribute and not hasattr(module, attribute):
                raise ImportError(f"Атрибут {attribute} не найден в модуле {module_name}")
                
            print(f"✓ {module_name} уже установлен")
            
        except ImportError:
            print(f"⚠ {module_name} не найден, устанавливаю {install_name}...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', install_name
                ])
                print(f"✓ {install_name} успешно установлен")
            except subprocess.CalledProcessError as e:
                print(f"✗ Ошибка установки {install_name}: {e}")
                sys.exit(1)

if __name__ == '__main__':
    # Тестируем функцию
    test_packages = [
        {
            'module_name': 'websockets',
            'install_name': 'websockets',
        },
        {
            'module_name': 'numpy',
            'install_name': 'numpy',
        }
    ]
    check_and_install_packages(test_packages)