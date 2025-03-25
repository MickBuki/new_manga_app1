"""
Функции для работы с папками и файлами манги
"""
import os
import re
from backend.config import get_settings
from backend.logger import get_app_logger
from backend.file_utils.user_files import get_user_directory, ensure_user_directories

def natural_sort_key(s):
    """
    Функция для естественной сортировки строк, чтобы '2' шел перед '10'
    
    Args:
        s: Строка для сортировки
        
    Returns:
        list: Список для сортировки
    """
    return [int(text) if text.isdigit() else text.lower() 
            for text in re.split(r'(\d+)', s)]

def get_manga_folders(user_id=None):
    """
    Получение списка папок с мангой из директории books
    Сортирует папки и изображения внутри них
    
    Args:
        user_id: ID пользователя (если None, используется общая директория)
        
    Returns:
        list: Список папок с мангой и изображениями
    """
    settings = get_settings()
    logger = get_app_logger()
    
    # Если указан пользователь, получаем его директорию books
    if user_id:
        books_dir = get_user_directory(user_id, "books")
        ensure_user_directories(user_id)  # Гарантируем создание директорий
    else:
        books_dir = settings.books_dir
    
    # Создаем папку books, если она не существует
    if not os.path.exists(books_dir):
        os.makedirs(books_dir)
        logger.info(f"Создана директория {books_dir}")
        return []
    
    manga_folders = []
    folder_id = 0
    
    # Получаем список папок в директории books и сортируем их
    logger.info(f"Сканирование папок манги в {books_dir}")
    for folder_name in sorted(os.listdir(books_dir)):
        folder_path = os.path.join(books_dir, folder_name)
        
        # Проверяем, что это папка
        if os.path.isdir(folder_path):
            folder_images = []
            image_count = 0
            
            # Получаем список изображений в папке и сортируем их
            for image_name in sorted(os.listdir(folder_path), key=lambda x: natural_sort_key(x)):
                image_path = os.path.join(folder_path, image_name)
                
                # Проверяем, что это файл изображения
                if os.path.isfile(image_path) and image_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    # Формируем URL для миниатюры
                    thumbnail_url = f'/thumbnails/{user_id}/{folder_name}/{image_name}' if user_id else f'/static/thumbnails/{folder_name}/{image_name}'
                    
                    image_count += 1
                    folder_images.append({
                        'name': image_name,
                        'path': image_path,
                        'thumbnail_url': thumbnail_url,
                    })
            
            # Сортируем изображения по имени
            folder_images = sorted(folder_images, key=lambda x: natural_sort_key(x['name']))
            
            # Добавляем папку в список
            manga_folders.append({
                'id': folder_id,
                'name': folder_name,
                'path': folder_path,
                'images': folder_images
            })
            
            logger.debug(f"Найдена папка {folder_name} с {len(folder_images)} изображениями")
            folder_id += 1
    
    logger.info(f"Найдено {len(manga_folders)} папок с мангой")
    return manga_folders

def ensure_dirs_exist():
    """
    Создает необходимые директории для работы приложения
    """
    settings = get_settings()
    logger = get_app_logger()
    
    directories = [
        settings.books_dir,
        settings.translated_books_dir,
        settings.static_dir,
        settings.thumbnails_dir,
        settings.temp_dir,
        settings.editor_sessions_dir,
        settings.data_dir
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Создана директория {directory}")