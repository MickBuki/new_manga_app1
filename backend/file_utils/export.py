"""
Утилиты для экспорта переведенной манги
"""
import os
import zipfile
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from backend.logger import get_app_logger
from backend.config import get_settings

def create_pdf_from_images(image_paths, output_path=None, title="Manga Translation"):
    """
    Создает PDF документ из списка изображений
    
    Args:
        image_paths: Список путей к изображениям
        output_path: Путь для сохранения PDF (опционально)
        title: Заголовок PDF документа
        
    Returns:
        str: Путь к созданному PDF файлу
    """
    logger = get_app_logger()
    settings = get_settings()
    
    # Если путь не указан, создаем в директории translated_books
    if output_path is None:
        os.makedirs(settings.translated_books_dir, exist_ok=True)
        output_path = os.path.join(settings.translated_books_dir, "translated_manga.pdf")
    
    # Размер страницы по умолчанию - A4 альбомной ориентации
    page_width, page_height = landscape(A4)
    
    try:
        logger.info(f"Создание PDF из {len(image_paths)} изображений")
        
        # Создаем PDF документ
        c = canvas.Canvas(output_path, pagesize=landscape(A4))
        c.setTitle(title)
        
        for i, img_path in enumerate(image_paths):
            try:
                # Открываем изображение
                img = Image.open(img_path)
                img_width, img_height = img.size
                
                # Масштабируем изображение, чтобы оно поместилось на странице
                scale_factor = min(page_width / img_width, page_height / img_height) * 0.9
                scaled_width = img_width * scale_factor
                scaled_height = img_height * scale_factor
                
                # Центрируем изображение на странице
                x_offset = (page_width - scaled_width) / 2
                y_offset = (page_height - scaled_height) / 2
                
                # Добавляем изображение в PDF
                c.drawImage(img_path, x_offset, y_offset, scaled_width, scaled_height)
                
                # Если это не последнее изображение, добавляем новую страницу
                if i < len(image_paths) - 1:
                    c.showPage()
                    
                logger.debug(f"Добавлено изображение {i+1}/{len(image_paths)}: {img_path}")
            except Exception as e:
                logger.error(f"Ошибка при обработке изображения {img_path}: {e}")
                continue
                
        # Сохраняем PDF
        c.save()
        logger.info(f"PDF создан успешно: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Ошибка создания PDF: {e}")
        return None

def create_zip_from_images(image_paths, output_path=None):
    """
    Создает ZIP архив из списка изображений
    
    Args:
        image_paths: Список путей к изображениям
        output_path: Путь для сохранения ZIP (опционально)
        
    Returns:
        str: Путь к созданному ZIP архиву
    """
    logger = get_app_logger()
    settings = get_settings()
    
    # Если путь не указан, создаем в директории translated_books
    if output_path is None:
        os.makedirs(settings.translated_books_dir, exist_ok=True)
        output_path = os.path.join(settings.translated_books_dir, "translated_manga.zip")
    
    try:
        logger.info(f"Создание ZIP из {len(image_paths)} изображений")
        
        # Создаем ZIP архив
        with zipfile.ZipFile(output_path, 'w') as zip_file:
            for i, img_path in enumerate(image_paths):
                try:
                    # Добавляем файл в архив с его оригинальным именем
                    filename = os.path.basename(img_path)
                    zip_file.write(img_path, filename)
                    logger.debug(f"Добавлен файл {i+1}/{len(image_paths)}: {filename}")
                except Exception as e:
                    logger.error(f"Ошибка при добавлении файла {img_path} в архив: {e}")
                    continue
        
        logger.info(f"ZIP архив создан успешно: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Ошибка создания ZIP архива: {e}")
        return None