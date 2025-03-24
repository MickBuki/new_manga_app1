"""
Основной файл приложения Flask
"""
from flask import Flask

from backend.config import get_settings
from backend.logger import get_app_logger
from backend.routes import register_blueprints

# Получаем настройки и логгер
settings = get_settings()
logger = get_app_logger()

# Создаем Flask-приложение
app = Flask(__name__, 
            static_folder='../frontend/static',
            template_folder='../frontend/templates')

# Регистрируем blueprints для маршрутов
register_blueprints(app)

# Если запускаем файл напрямую, импортируем и выполняем run.py
if __name__ == '__main__':
    import sys
    import os
    
    # Добавляем текущую директорию в пути поиска модулей
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Импортируем и запускаем
    import run