"""
Модуль для логирования приложения
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Глобальный словарь логгеров
loggers = {}

def setup_logger(name, log_file=None, level=logging.INFO, console=True, 
                max_size=10*1024*1024, backup_count=5):
    """
    Настраивает и возвращает именованный логгер
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу логов
        level: Уровень логирования
        console: Флаг для вывода в консоль
        max_size: Максимальный размер файла логов
        backup_count: Количество резервных копий
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Если логгер уже существует, возвращаем его
    if name in loggers:
        return loggers[name]
    
    # Создаем новый логгер
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Добавляем обработчик для файла
    if log_file:
        # Создаем директорию для файла логов, если она не существует
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Создаем обработчик для ротации файла логов
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_size, 
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Добавляем обработчик для консоли
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Сохраняем логгер в словарь
    loggers[name] = logger
    
    return logger

def get_logger(name, config=None):
    """
    Возвращает логгер с указанным именем
    
    Args:
        name: Имя логгера
        config: Настройки логирования (LogSettings)
        
    Returns:
        logging.Logger: Логгер
    """
    # Если логгер уже существует, возвращаем его
    if name in loggers:
        return loggers[name]
        
    # Если переданы настройки, используем их
    if config:
        level = getattr(logging, config.log_level.upper(), logging.INFO)
        return setup_logger(
            name, 
            log_file=config.log_file, 
            level=level, 
            console=config.console_log,
            max_size=config.max_size,
            backup_count=config.backup_count
        )
    else:
        # Иначе используем настройки по умолчанию
        return setup_logger(name)

# Основной логгер приложения
app_logger = None

def init_app_logger(config=None):
    """
    Инициализирует основной логгер приложения
    
    Args:
        config: Настройки логирования (LogSettings)
        
    Returns:
        logging.Logger: Основной логгер приложения
    """
    global app_logger
    app_logger = get_logger('manga_translator', config)
    return app_logger

def get_app_logger():
    """
    Возвращает основной логгер приложения
    
    Returns:
        logging.Logger: Основной логгер приложения
    """
    global app_logger
    if app_logger is None:
        app_logger = get_logger('manga_translator')
    return app_logger