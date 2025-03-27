from backend.config.models import (
    GOOGLE_LANG_CODES,
    OPENAI_LANG_NAMES,
    PADDLE_OCR_LANGS,
    TESSERACT_LANG_CODES,
    OPTIMAL_OCR_ENGINES
)

from backend.config import get_settings


from .ocr import (
    get_mangaocr,
    get_paddleocr,
    get_easyocr,
    get_tesseract,
    get_optimal_ocr_engine,
    preprocess_image,
    ocr_with_mangaocr,
    ocr_with_paddle,
    ocr_with_easyocr,
    ocr_with_tesseract,
    get_tesseract_config
)

from .detection import (
    get_device,
    get_bubble_model,
    get_text_model,
    sort_text_bubbles
)

# Функция для извлечения текста из блоков
def extract_text_from_boxes(image_path, text_boxes, ocr_engine='auto', source_language='zh', use_gpu=False):
    """
    Извлекает текст из каждого текстового блока с унифицированной предобработкой
    и автоматическим выбором OCR
    """
    from backend.logger import get_app_logger
    logger = get_app_logger()
    
    logger.info(f"Извлечение текста из {len(text_boxes)} блоков...")
    
    # Автоматический выбор OCR, если задано 'auto'
    if ocr_engine == 'auto':
        ocr_engine = get_optimal_ocr_engine(source_language)
    
    logger.info(f"Используем OCR-движок: {ocr_engine} для языка {source_language}")
    
    from PIL import Image
    import tempfile
    import os
    
    img = Image.open(image_path)
    blocks_result = []
    
    for i, box in enumerate(text_boxes):
        x_min, y_min, x_max, y_max = box
        logger.debug(f"Обработка блока {i+1}/{len(text_boxes)}...")
        
        # Вырезаем фрагмент изображения
        crop_img = img.crop((x_min, y_min, x_max, y_max))
        
        # Сохраняем исходный вырезанный блок
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
            temp_path = temp.name
            crop_img.save(temp_path)
        
        try:
            # Выбираем соответствующий OCR в зависимости от движка
            if ocr_engine == 'paddleocr':
                text = ocr_with_paddle(temp_path, i, source_language, use_gpu)
            elif ocr_engine == 'mangaocr':
                text = ocr_with_mangaocr(temp_path, i, source_language, use_gpu)
            elif ocr_engine == 'easyocr':
                text = ocr_with_easyocr(temp_path, i, source_language, use_gpu)
            elif ocr_engine == 'tesseract':
                text = ocr_with_tesseract(temp_path, i, source_language)
            else:
                text = ""
                logger.warning(f"Неизвестный OCR-движок: {ocr_engine}")
            
            blocks_result.append({
                'id': i,
                'box': box,
                'text': text.strip(),
                'translated_text': None
            })
            logger.debug(f"Блок {i+1}: распознан текст '{text.strip()}'")
        except Exception as e:
            logger.error(f"Ошибка OCR для блока {i}: {e}")
            blocks_result.append({
                'id': i,
                'box': box,
                'text': "",
                'translated_text': None
            })
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    return blocks_result