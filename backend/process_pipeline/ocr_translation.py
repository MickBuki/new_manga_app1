"""
Функции для OCR и перевода текста
"""
import os
import time
import json
import base64
import io
import numpy as np
from PIL import Image as PILImage

from backend.config import get_settings
from backend.logger import get_app_logger
from backend.models import extract_text_from_boxes, get_optimal_ocr_engine
from backend.translation import translate_text_blocks
from backend.image_processing import create_translated_image
from backend.file_utils import save_text_blocks_info
from backend.file_utils.temp import get_temp_filepath, generate_unique_filename
from backend.manga_editor import MangaEditor

def process_ocr_and_translation(image_path, seg_results, bubble_mask=None, text_background_mask=None, output_path=None, 
                               translation_method=None, openai_api_key=None, ocr_engine=None, edit_mode=False, 
                               batch_id=None, file_index=0, original_filename=None, source_language='zh', target_language='ru'):
    """
    Комплексная обработка OCR и перевода изображения с автоматическим выбором OCR
    
    Args:
        image_path: Путь к изображению
        seg_results: Результаты сегментации
        bubble_mask: Маска пузырей (опционально)
        text_background_mask: Маска текстовых блоков (опционально)
        output_path: Путь для сохранения результатов (опционально)
        translation_method: Метод перевода ('google' или 'openai')
        openai_api_key: API ключ OpenAI (если используется translation_method='openai')
        ocr_engine: OCR движок ('auto', 'mangaocr', 'paddleocr', 'easyocr', 'tesseract')
        edit_mode: Включение режима редактирования
        batch_id: ID группы файлов
        file_index: Индекс файла в группе
        original_filename: Оригинальное имя файла
        source_language: Язык оригинала
        target_language: Язык перевода
        
    Returns:
        dict: Результаты обработки
    """
    if output_path is None:
        output_filename = generate_unique_filename('final_results', '.json')
        output_path = get_temp_filepath(output_filename)
        
    settings = get_settings()
    logger = get_app_logger()
    start_time = time.time()
    
    # Инициализируем редактор манги
    manga_editor = MangaEditor(settings.editor_sessions_dir)

    # Используем значения из настроек, если не указаны явно
    if translation_method is None:
        translation_method = settings.translator_default_method
    
    # Если не передан API ключ OpenAI, берем из настроек
    if translation_method == 'openai' and openai_api_key is None:
        openai_api_key = settings.openai_api_key

    try:
        logger.info(f"Начало OCR и перевода для {image_path}")
        logger.info(f"Метод перевода: {translation_method}")
        
        # Если OCR-движок не указан явно или указан 'auto', выбираем оптимальный для языка
        if ocr_engine is None or ocr_engine == 'auto':
            ocr_engine = get_optimal_ocr_engine(source_language)
            logger.info(f"Автоматически выбран OCR-движок: {ocr_engine} для языка {source_language}")
        else:
            logger.info(f"Используется указанный OCR-движок: {ocr_engine}")
        
        # Используем оригинальное имя файла из аргументов или из seg_results
        if original_filename is None:
            original_filename = seg_results.get('original_filename', os.path.basename(image_path))
        
        logger.info(f"Оригинальное имя файла: {original_filename}")
        logger.debug(f"Режим редактирования: {edit_mode}, batch_id: {batch_id}, file_index: {file_index}")
        
        # Используем текстовые боксы из результатов сегментации
        text_boxes = seg_results['text_boxes']
        logger.info(f"Загружено {len(text_boxes)} текстовых блоков")

        # Получаем изображение с масками
        final_base64 = seg_results.get('final', '')
        final_bytes = base64.b64decode(final_base64)
        final_img = PILImage.open(io.BytesIO(final_bytes))
        
        # Проверяем и создаем маски, если они не переданы
        if bubble_mask is None or text_background_mask is None:
            if final_img.mode == 'RGBA':
                # Извлекаем каналы из изображения
                r, g, b, a = final_img.split()
                
                # Создаем маски на основе цветовых каналов
                bubble_mask = np.array(r) == 255  # Синий канал для пузырей
                text_background_mask = np.array(b) == 255  # Красный канал для текстовых блоков
                
                # Преобразуем булевы маски в uint8
                bubble_mask = (bubble_mask * 255).astype(np.uint8)
                text_background_mask = (text_background_mask * 255).astype(np.uint8)
                
                logger.debug(f"Маски извлечены из альфа-канала, размер: bubble_mask {bubble_mask.shape}, text_background_mask {text_background_mask.shape}")
            else:
                error_msg = "Изображение final не имеет альфа-канала"
                logger.error(error_msg)
                raise ValueError(error_msg)

        logger.info(f"Извлечение текста с использованием {ocr_engine}...")
        text_blocks = extract_text_from_boxes(image_path, text_boxes, ocr_engine, source_language, settings.use_gpu)
        
        logger.info("Перевод текста...")
        translated_blocks, error_message = translate_text_blocks(
            text_blocks, 
            translation_method=translation_method, 
            openai_api_key=openai_api_key,
            src_lang=source_language,
            dest_lang=target_language
        )
        
        if error_message:
            logger.error(f"Ошибка при переводе: {error_message}")
            seg_results['error'] = True
            seg_results['error_message'] = error_message
            with open(output_path, 'w') as f:
                json.dump(seg_results, f)
            logger.warning(f"Сохранены результаты с ошибкой: {error_message}")
            return seg_results
        
        json_path = image_path + ".json"
        save_text_blocks_info(translated_blocks, json_path)
        
        # Получаем изображение с удаленным текстом
        text_removed_base64 = seg_results.get('text_removed', '')
        text_removed_bytes = base64.b64decode(text_removed_base64)
        text_removed_img = PILImage.open(io.BytesIO(text_removed_bytes))
        
        # Если включен режим редактирования, создаем сессию
        if edit_mode:
            logger.info(f"Создание сессии редактирования для {original_filename}")
            logger.debug(f"batch_id: {batch_id}, file_index: {file_index}")
            
            session_id = manga_editor.create_session(
                image_path,
                text_removed_img,
                translated_blocks,
                bubble_mask,  # Передаем маску пузырей
                text_background_mask=text_background_mask,  # Передаем маску текстовых блоков
                group_id=batch_id,
                file_index=file_index,
                original_filename=original_filename,
                source_language=source_language,
                target_language=target_language
            )
            
            # Проверяем, что сессия была создана успешно
            session_data = manga_editor.get_session(session_id)
            if session_data:
                logger.info(f"Сессия {session_id} успешно создана для файла {original_filename}")
                logger.debug(f"Группа: {session_data.get('group_id')}, найдено {len(session_data.get('all_files', []))} файлов в группе")
            else:
                logger.warning(f"Не удалось получить данные созданной сессии {session_id}")
            
            seg_results['edit_session_id'] = session_id
            seg_results['edit_batch_id'] = batch_id
        
        logger.info("Создание изображения с переводом...")
        translated_img_path = image_path + ".translated.png"
        
        # Вызываем функцию с обеими масками из модуля image_processing
        create_translated_image(
            image_path, 
            translated_blocks, 
            translated_img_path, 
            bubble_mask, 
            text_background_mask
        )
        
        logger.debug("Конвертация изображения в base64...")
        translated_img = PILImage.open(translated_img_path)
        
        # Импортируем функцию для конвертации в base64
        from backend.image_processing import image_to_base64
        translated_base64 = image_to_base64(translated_img)

        seg_results['translated'] = translated_base64
        seg_results['text_blocks'] = translated_blocks
        
        logger.info(f"Сохранение финальных результатов в {output_path}")
        with open(output_path, 'w') as f:
            json.dump(seg_results, f)
            
        if os.path.exists(translated_img_path):
            os.remove(translated_img_path)
            
        logger.info(f"OCR и перевод завершены за {time.time() - start_time:.2f} секунд")
        return seg_results
    except Exception as e:
        logger.error(f"Ошибка в process_ocr_and_translation: {e}", exc_info=True)
        if 'seg_results' not in locals():
            seg_results = {}
        seg_results['error'] = True
        seg_results['error_message'] = str(e)
        if 'original' in seg_results:
            seg_results['translated'] = seg_results['original']
            seg_results['text_blocks'] = [{'id': 0, 'box': [0, 0, 100, 100], 'text': 'Ошибка обработки', 'translated_text': 'Ошибка обработки'}]
            with open(output_path, 'w') as f:
                json.dump(seg_results, f)
            return seg_results
        else:
            raise