#!/usr/bin/env python3
"""
Простой тест для проверки HTTP API endpoints.
Проверяет доступность сервера и корректность endpoints без реальной транскрипции.
"""

import requests
import sys

def test_health_endpoint(base_url: str = "http://localhost:8013") -> bool:
    """Тест health endpoint."""
    print(f"🔍 Проверка health endpoint: {base_url}/health")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Health check passed: {data}")
        return data.get('status') == 'ok'
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_info_endpoint(base_url: str = "http://localhost:8013") -> bool:
    """Тест info endpoint."""
    print(f"🔍 Проверка info endpoint: {base_url}/info")
    
    try:
        response = requests.get(f"{base_url}/info", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Info endpoint passed:")
        print(f"   Model: {data.get('model')}")
        print(f"   Device: {data.get('device')}")
        print(f"   Language: {data.get('language')}")
        print(f"   Max file size: {data.get('max_file_size_mb')} MB")
        print(f"   Supported formats: {', '.join(data.get('supported_formats', []))}")
        print(f"   Transcriber ready: {data.get('transcriber_ready')}")
        return True
        
    except Exception as e:
        print(f"❌ Info endpoint failed: {e}")
        return False

def test_transcribe_endpoint_without_file(base_url: str = "http://localhost:8013") -> bool:
    """Тест transcribe endpoint без файла (должен вернуть ошибку)."""
    print(f"🔍 Проверка transcribe endpoint без файла: {base_url}/transcribe")
    
    try:
        response = requests.post(f"{base_url}/transcribe", timeout=5)
        
        # Ожидаем ошибку 400
        if response.status_code == 400:
            print(f"✅ Transcribe endpoint correctly rejects request without file")
            return True
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Transcribe endpoint test failed: {e}")
        return False

def main():
    """Запуск всех тестов."""
    print("=" * 60)
    print("HTTP API Tests")
    print("=" * 60)
    
    # Получаем URL из аргументов или используем default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8013"
    
    print(f"\nТестирование сервера: {base_url}\n")
    
    results = []
    
    # Тест 1: Health endpoint
    results.append(("Health endpoint", test_health_endpoint(base_url)))
    print()
    
    # Тест 2: Info endpoint  
    results.append(("Info endpoint", test_info_endpoint(base_url)))
    print()
    
    # Тест 3: Transcribe без файла
    results.append(("Transcribe validation", test_transcribe_endpoint_without_file(base_url)))
    print()
    
    # Итоги
    print("=" * 60)
    print("Результаты тестов:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 Все тесты пройдены!")
        sys.exit(0)
    else:
        print("❌ Некоторые тесты не пройдены")
        sys.exit(1)

if __name__ == '__main__':
    main()
