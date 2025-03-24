"""
Точка входа для запуска приложения Manga Translator
"""
import argparse

# Парсим аргументы командной строки
parser = argparse.ArgumentParser(description='Manga Translator')
parser.add_argument('--gpu', action='store_true', help='Использовать GPU для обработки (по умолчанию: CPU)')
parser.add_argument('--debug', action='store_true', help='Включить режим отладки')
parser.add_argument('--host', type=str, default='127.0.0.1', help='Хост для запуска приложения')
parser.add_argument('--port', type=int, default=5000, help='Порт для запуска приложения')
args = parser.parse_args()

# Инициализируем настройки приложения
from backend.config import init_settings
settings = init_settings(args)

# Также устанавливаем режим отладки из аргументов
if args.debug:
    settings.debug = True

# Инициализируем логгер
from backend.logger import init_app_logger
logger = init_app_logger(settings.log_settings)
logger.info(f"Запуск приложения {settings.app_name}")

# Импортируем приложение
from backend.app import app

# Создаем необходимые директории
from backend.file_utils import ensure_dirs_exist
ensure_dirs_exist()

# Очищаем временные файлы при запуске
from backend.file_utils import cleanup_temp_files
cleanup_temp_files()

# Регистрация очистки при завершении
import atexit
atexit.register(cleanup_temp_files)

# Выводим информацию о режиме работы
gpu_status = "GPU" if settings.use_gpu else "CPU"
logger.info(f"=== {settings.app_name} запущен в режиме {gpu_status} ===")

if settings.use_gpu:
    import torch
    if not torch.cuda.is_available():
        logger.warning("ВНИМАНИЕ: GPU запрошен, но CUDA недоступна. Будет использован CPU.")

if __name__ == '__main__':
    # Запускаем Flask-приложение
    app.run(
        host=args.host,
        port=args.port,
        debug=settings.debug
    )