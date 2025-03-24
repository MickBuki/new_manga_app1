"""
Функции для работы с временными файлами
"""
import os
import glob
import uuid
from backend.logger import get_app_logger

def generate_unique_filename(prefix, extension):
    """
    Генерирует уникальное имя файла для избежания конфликтов при параллельной обработке
    
    Args:
        prefix: Префикс имени файла
        extension: Расширение файла (с точкой)
        
    Returns:
        str: Уникальное имя файла
    """
    return f"{prefix}_{uuid.uuid4().hex}{extension}"

def cleanup_temp_files():
    """
    Очищает временные файлы приложения
    """
    logger = get_app_logger()
    patterns = ["temp_*.*", "segmentation_results_*.json", "final_results_*.json"]
    total_removed = 0
    
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
                logger.debug(f"Удален временный файл: {file_path}")
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
    import json
    logger = get_app_logger()
    
    logger.info(f"Сохранение информации о текстовых блоках в {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(text_blocks, f, ensure_ascii=False, indent=2)
    logger.debug("Информация о текстовых блоках сохранена")