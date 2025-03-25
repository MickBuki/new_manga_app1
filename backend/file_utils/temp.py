"""
Функции для работы с временными файлами
"""
import os
import glob
import uuid
from backend.logger import get_app_logger
from backend.config import get_settings
import json

def generate_unique_filename(prefix, extension):
    """
    Генерирует уникальное имя файла для избежания конфликтов при параллельной обработке
    
    Args:
        prefix: Префикс имени файла
        extension: Расширение файла (с точкой)
        
    Returns:
        str: Путь к временному файлу
    """
    # Получаем директорию для временных файлов из настроек
    
    temp_dir = get_settings().temp_dir
    
    # Создаем директорию, если она не существует
    os.makedirs(temp_dir, exist_ok=True)
    
    # Генерируем уникальное имя файла
    filename = f"{prefix}_{uuid.uuid4().hex}{extension}"
    
    # Возвращаем полный путь
    return os.path.join(temp_dir, filename)

def get_temp_filepath(filename):
    """
    Возвращает полный путь к файлу в директории для временных файлов.
    Если filename уже содержит путь к temp_dir, возвращает filename без изменений.
    
    Args:
        filename: Имя файла или путь
        
    Returns:
        str: Полный путь к файлу в временной директории
    """
    settings = get_settings()
    temp_dir = settings.temp_dir
    
    # Проверяем, если filename уже содержит полный путь в temp_dir
    if filename.startswith(temp_dir):
        return filename
    
    # Создаем директорию, если она не существует
    os.makedirs(temp_dir, exist_ok=True)
    
    # Возвращаем полный путь
    return os.path.join(temp_dir, os.path.basename(filename))

def cleanup_temp_files():
    """
    Очищает временные файлы приложения
    """
    logger = get_app_logger()
    settings = get_settings()
    temp_dir = settings.temp_dir
    
    patterns = ["temp_*.*", "segmentation_results_*.json", "final_results_*.json"]
    total_removed = 0
    
    # Проверяем файлы в директории temp
    for pattern in patterns:
        for file_path in glob.glob(os.path.join(temp_dir, pattern)):
            try:
                os.remove(file_path)
                logger.debug(f"Удален временный файл: {file_path}")
                total_removed += 1
            except Exception as e:
                logger.warning(f"Не удалось удалить {file_path}: {e}")
    
    # Также проверяем и очищаем файлы в корне проекта (для совместимости)
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
                logger.debug(f"Удален временный файл из корня: {file_path}")
                total_removed += 1
            except Exception as e:
                logger.warning(f"Не удалось удалить {file_path}: {e}")
    
    if total_removed > 0:
        logger.info(f"Удалено {total_removed} временных файлов")
    
    return total_removed

def save_text_blocks_info(text_blocks, output_path):
    """
    Сохраняет информацию о текстовых блоках в JSON файл
    
    Args:
        text_blocks: Список текстовых блоков
        output_path: Путь для сохранения JSON файла
    """

    logger = get_app_logger()
    
    # Убедимся, что директория существует, если output_path содержит путь
    dirname = os.path.dirname(output_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    
    logger.info(f"Сохранение информации о текстовых блоках в {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(text_blocks, f, ensure_ascii=False, indent=2)
    logger.debug("Информация о текстовых блоках сохранена")