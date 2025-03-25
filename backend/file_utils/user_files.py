"""
Функции для работы с пользовательскими файлами
"""
import os
import shutil
from backend.config import get_settings
from backend.logger import get_app_logger

def get_user_directory(user_id, dir_type="books"):
    """
    Получает путь к указанной директории пользователя
    
    Args:
        user_id: ID пользователя
        dir_type: Тип директории ("books", "translated", "temp", "editor", "thumbnails")
        
    Returns:
        str: Путь к директории
    """
    settings = get_settings()
    
    # Базовая директория пользователя
    user_dir = os.path.join(settings.data_dir, "users", user_id)
    
    # Выбираем тип директории
    if dir_type == "books":
        return os.path.join(user_dir, "books")
    elif dir_type == "translated":
        return os.path.join(user_dir, "translated")
    elif dir_type == "temp":
        return os.path.join(user_dir, "temp")
    elif dir_type == "editor":
        return os.path.join(user_dir, "editor_sessions")
    elif dir_type == "thumbnails":
        return os.path.join(user_dir, "thumbnails")
    else:
        return user_dir

def ensure_user_directories(user_id):
    """
    Создает необходимые директории для пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        dict: Пути к созданным директориям
    """
    logger = get_app_logger()
    
    directories = {
        "books": get_user_directory(user_id, "books"),
        "translated": get_user_directory(user_id, "translated"),
        "temp": get_user_directory(user_id, "temp"),
        "editor": get_user_directory(user_id, "editor"),
        "thumbnails": get_user_directory(user_id, "thumbnails")
    }
    
    for dir_name, dir_path in directories.items():
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Создана директория пользователя {user_id}: {dir_path}")
    
    return directories

def get_file_path(user_id, filename, dir_type="books"):
    """
    Получает путь к файлу в директории пользователя
    
    Args:
        user_id: ID пользователя
        filename: Имя файла
        dir_type: Тип директории
        
    Returns:
        str: Полный путь к файлу
    """
    user_dir = get_user_directory(user_id, dir_type)
    return os.path.join(user_dir, filename)

def save_file(file, user_id, dir_type="books", filename=None):
    """
    Сохраняет файл в директории пользователя
    
    Args:
        file: Объект файла (FileStorage) или путь к файлу
        user_id: ID пользователя
        dir_type: Тип директории
        filename: Имя файла (если не указано, используется имя из file)
        
    Returns:
        str: Путь к сохраненному файлу
    """
    logger = get_app_logger()
    
    # Получаем директорию пользователя
    user_dir = get_user_directory(user_id, dir_type)
    
    # Если директория не существует, создаем ее
    if not os.path.exists(user_dir):
        os.makedirs(user_dir, exist_ok=True)
    
    # Определяем имя файла
    if filename is None:
        if hasattr(file, 'filename'):
            filename = file.filename
        else:
            filename = os.path.basename(file)
    
    # Путь к новому файлу
    dest_path = os.path.join(user_dir, filename)
    
    # Сохраняем файл
    if hasattr(file, 'save'):
        file.save(dest_path)
    else:
        # Если file это путь к файлу, копируем его
        shutil.copy2(file, dest_path)
    
    logger.debug(f"Файл сохранен для пользователя {user_id}: {dest_path}")
    
    return dest_path

def copy_file(source_path, user_id, dir_type="books", filename=None):
    """
    Копирует файл в директорию пользователя
    
    Args:
        source_path: Путь к исходному файлу
        user_id: ID пользователя
        dir_type: Тип директории
        filename: Имя файла (если None, используется базовое имя source_path)
        
    Returns:
        str: Путь к новому файлу
    """
    logger = get_app_logger()
    
    # Получаем директорию пользователя
    user_dir = get_user_directory(user_id, dir_type)
    
    # Если директория не существует, создаем ее
    if not os.path.exists(user_dir):
        os.makedirs(user_dir, exist_ok=True)
    
    # Определяем имя файла
    if filename is None:
        filename = os.path.basename(source_path)
    
    # Путь к новому файлу
    dest_path = os.path.join(user_dir, filename)
    
    # Копируем файл
    shutil.copy2(source_path, dest_path)
    logger.debug(f"Файл скопирован для пользователя {user_id}: {dest_path}")
    
    return dest_path

def list_files(user_id, dir_type="books", extension=None):
    """
    Получает список файлов в директории пользователя
    
    Args:
        user_id: ID пользователя
        dir_type: Тип директории
        extension: Расширение файлов (например, '.png')
        
    Returns:
        list: Список путей к файлам
    """
    user_dir = get_user_directory(user_id, dir_type)
    
    if not os.path.exists(user_dir):
        return []
    
    files = []
    
    for filename in os.listdir(user_dir):
        file_path = os.path.join(user_dir, filename)
        
        if os.path.isfile(file_path):
            if extension:
                if filename.lower().endswith(extension.lower()):
                    files.append(file_path)
            else:
                files.append(file_path)
    
    return files

def list_subdirectories(user_id, dir_type="books"):
    """
    Получает список поддиректорий в директории пользователя
    
    Args:
        user_id: ID пользователя
        dir_type: Тип директории
        
    Returns:
        list: Список имен поддиректорий
    """
    user_dir = get_user_directory(user_id, dir_type)
    
    if not os.path.exists(user_dir):
        return []
    
    subdirs = []
    
    for item in os.listdir(user_dir):
        item_path = os.path.join(user_dir, item)
        
        if os.path.isdir(item_path):
            subdirs.append(item)
    
    return subdirs

def is_file_owner(user_id, file_path):
    """
    Проверяет, является ли пользователь владельцем файла
    
    Args:
        user_id: ID пользователя
        file_path: Путь к файлу
        
    Returns:
        bool: True, если пользователь является владельцем
    """
    # Получаем директории пользователя
    user_dirs = [
        get_user_directory(user_id, "books"),
        get_user_directory(user_id, "translated"),
        get_user_directory(user_id, "temp"),
        get_user_directory(user_id, "editor"),
        get_user_directory(user_id, "thumbnails")
    ]
    
    # Преобразуем абсолютные пути к нормализованным путям
    file_path = os.path.normpath(os.path.abspath(file_path))
    user_dirs = [os.path.normpath(os.path.abspath(d)) for d in user_dirs]
    
    # Проверяем, находится ли файл в одной из директорий пользователя
    for user_dir in user_dirs:
        if file_path.startswith(user_dir):
            return True
    
    return False