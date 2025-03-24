"""
Модуль для управления конфигурацией приложения
"""

import os
import json
import argparse
from .settings import AppSettings, LogSettings

# Глобальный экземпляр настроек
settings = None

def init_settings(args=None):
    """
    Инициализирует настройки приложения
    
    Args:
        args: Аргументы командной строки (результат argparse.parse_args())
        
    Returns:
        AppSettings: Экземпляр настроек приложения
    """
    global settings
    
    # Создаем настройки и загружаем их из файла
    settings = AppSettings()
    
    # Загружаем настройки из окружения
    settings.load_from_env()
    
    # Если переданы аргументы командной строки, применяем их
    if args:
        settings.use_gpu = getattr(args, 'gpu', False)
    
    # Инициализируем настройки логирования
    settings.log_settings = LogSettings()
    settings.log_settings.log_level = os.environ.get('LOG_LEVEL', 'INFO')
    settings.log_settings.log_file = os.environ.get('LOG_FILE', 'manga_translator.log')
    
    return settings

def get_settings():
    """
    Возвращает экземпляр настроек приложения
    
    Returns:
        AppSettings: Экземпляр настроек приложения
    """
    global settings
    if settings is None:
        # Если настройки не инициализированы, создаем значения по умолчанию
        settings = init_settings()
    return settings