"""
Функции для обработки файлов манги
"""
import os
import time
import json
import base64
import io
import concurrent.futures
from PIL import Image
import shutil

from backend.logger import get_app_logger
from backend.config import get_settings
from .temp import generate_unique_filename, save_text_blocks_info, get_temp_filepath
from .folders import natural_sort_key
from backend.process_pipeline import process_segmentation, process_ocr_and_translation

def process_single_file(file, translation_method, openai_api_key, ocr_engine, edit_mode=False, batch_id=None, file_index=0, source_language='zh', target_language='ru'):
    """
    Обрабатывает один файл изображения и возвращает результаты
    
    Args:
        file: Файл из request.files
        translation_method: Метод перевода ('google' или 'openai')
        openai_api_key: API ключ OpenAI (если используется translation_method='openai')
        ocr_engine: OCR движок ('auto', 'mangaocr', 'paddleocr', 'easyocr', 'tesseract')
        edit_mode: Включение режима редактирования
        batch_id: ID группы файлов
        file_index: Индекс файла в группе
        source_language: Язык оригинала
        target_language: Язык перевода
        
    Returns:
        tuple: (путь к временному файлу, результаты обработки)
    """
    
    
    logger = get_app_logger()
    settings = get_settings()
    
    # Сохраняем оригинальное имя файла
    original_filename = file.filename
    
    # Создаем уникальные имена для временных файлов
    temp_filename = generate_unique_filename('temp_image', '.png')
    file_path = get_temp_filepath(temp_filename)
    file.save(file_path)
    
    # Уникальный идентификатор для временных файлов
    unique_id = generate_unique_filename('', '')
    seg_results_filename = f'segmentation_results_{unique_id}.json'
    final_results_filename = f'final_results_{unique_id}.json'
    seg_results_path = get_temp_filepath(seg_results_filename)
    final_results_path = get_temp_filepath(final_results_filename)
    
    logger.info(f"Обработка файла {original_filename}")
    
    try:
        # Выполняем сегментацию
        logger.info(f"Сегментация для {original_filename}...")
        seg_results, bubble_mask, text_background_mask = process_segmentation(file_path, seg_results_path)
        
        # Сохраняем оригинальное имя файла в результатах для дальнейшего использования
        seg_results['original_filename'] = original_filename
        
        # Выполняем OCR и перевод с учетом режима редактирования
        logger.info(f"OCR и перевод для {original_filename}...")
        logger.debug(f"Режим редактирования: {edit_mode}, batch_id: {batch_id}, file_index: {file_index}")
        
        file_result = process_ocr_and_translation(
            file_path, 
            seg_results, 
            bubble_mask,
            text_background_mask,
            final_results_path,
            translation_method=translation_method, 
            openai_api_key=openai_api_key, 
            ocr_engine=ocr_engine,
            edit_mode=edit_mode,
            batch_id=batch_id,
            file_index=file_index,
            original_filename=original_filename,
            source_language=source_language,
            target_language=target_language
        )
        
        # Проверяем на наличие ошибки перевода
        if file_result.get('error'):
            logger.error(f"Ошибка при переводе {original_filename}: {file_result.get('error_message')}")
            return file_path, file_result
        
        file_result['filename'] = original_filename
        
        # Сохраняем переведенное изображение для возможности скачивания
        try:
            # Создаем директорию, если ее нет
            os.makedirs(settings.translated_books_dir, exist_ok=True)
            
            # Сохраняем изображение из base64
            translated_image_path = os.path.join(settings.translated_books_dir, original_filename)
            translated_base64 = file_result['translated']
            img_data = base64.b64decode(translated_base64)
            img = Image.open(io.BytesIO(img_data))
            img.save(translated_image_path)
            
            # Добавляем путь к результату
            file_result['image_path'] = translated_image_path
            logger.info(f"Изображение сохранено для скачивания: {translated_image_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения изображения для скачивания: {e}")
        
        return file_path, file_result
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Ошибка обработки файла {original_filename}: {str(e)}")
        logger.debug(error_traceback)
        return file_path, {"error": True, "error_message": str(e), "filename": original_filename}
    finally:
        # Удаление временных файлов
        for path in [seg_results_path, final_results_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.warning(f"Ошибка при удалении временного файла {path}: {e}")

def process_single_image(image_path, translation_method, openai_api_key, ocr_engine, translated_folder, edit_mode=False, batch_id=None, file_index=0, source_language='zh', target_language='ru'):
    """
    Обрабатывает одно изображение из папки манги
    
    Args:
        image_path: Путь к изображению
        translation_method: Метод перевода ('google' или 'openai')
        openai_api_key: API ключ OpenAI (если используется translation_method='openai')
        ocr_engine: OCR движок ('auto', 'mangaocr', 'paddleocr', 'easyocr', 'tesseract')
        translated_folder: Папка для сохранения переведенного изображения
        edit_mode: Включение режима редактирования
        batch_id: ID группы файлов
        file_index: Индекс файла в группе
        source_language: Язык оригинала
        target_language: Язык перевода
        
    Returns:
        tuple: (путь к временному файлу, результаты обработки)
    """
    
    logger = get_app_logger()
    
    # Создаем уникальные имена для временных файлов
    unique_id = generate_unique_filename('', '')
    temp_filename = generate_unique_filename('temp_image', '.png')
    file_path = get_temp_filepath(temp_filename)
    shutil.copy(image_path, file_path)
    
    # Получаем имя файла
    image_name = os.path.basename(image_path)
    
    # Обновленные пути для временных файлов
    seg_results_filename = f'segmentation_results_{unique_id}.json'
    final_results_filename = f'final_results_{unique_id}.json'
    seg_results_path = get_temp_filepath(seg_results_filename)
    final_results_path = get_temp_filepath(final_results_filename)
    
    logger.info(f"Обработка файла {image_name} из папки")
    
    try:
        # Выполняем сегментацию
        logger.info(f"Сегментация для {image_name}...")
        seg_results, bubble_mask, text_background_mask = process_segmentation(file_path, seg_results_path)
        
        # Выполняем OCR и перевод с учетом режима редактирования и batch_id
        logger.info(f"OCR и перевод для {image_name}...")
        file_result = process_ocr_and_translation(
            file_path,
            seg_results,
            bubble_mask,
            text_background_mask,
            final_results_path,
            translation_method=translation_method,
            openai_api_key=openai_api_key,
            ocr_engine=ocr_engine,
            edit_mode=edit_mode,
            batch_id=batch_id,
            file_index=file_index,
            original_filename=image_name,
            source_language=source_language,
            target_language=target_language
        )
        
        # Сохраняем переведенное изображение в папку translated_books
        translated_image_path = os.path.join(translated_folder, image_name)
        translated_base64 = file_result['translated']
        
        # Декодируем base64 и сохраняем изображение
        img_data = base64.b64decode(translated_base64)
        img = Image.open(io.BytesIO(img_data))
        img.save(translated_image_path)
        
        # Добавляем информацию о файле в результаты
        file_result['filename'] = image_name
        file_result['image_path'] = translated_image_path
        
        logger.info(f"Изображение для скачивания: {translated_image_path}")
        
        return file_path, file_result
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Ошибка обработки файла {image_name}: {str(e)}")
        logger.debug(error_traceback)
        return file_path, {"error": True, "error_message": str(e), "filename": image_name}
    finally:
        # Удаление временных файлов
        for path in [seg_results_path, final_results_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.warning(f"Ошибка при удалении временного файла {path}: {e}")

def process_manga_folder(folder_path, translation_method='google', openai_api_key='', ocr_engine='mangaocr', selected_images=None, edit_mode=False, source_language='zh', target_language='ru'):
    """
    Обработка всех изображений в папке манги с параллельной обработкой
    и сохранением исходного порядка файлов
    
    Args:
        folder_path: Путь к папке с мангой
        translation_method: Метод перевода ('google' или 'openai')
        openai_api_key: API ключ OpenAI (если используется translation_method='openai')
        ocr_engine: OCR движок ('auto', 'mangaocr', 'paddleocr', 'easyocr', 'tesseract')
        selected_images: Список путей к выбранным изображениям
        edit_mode: Включение режима редактирования
        source_language: Язык оригинала
        target_language: Язык перевода
        
    Returns:
        list: Результаты обработки
    """
    logger = get_app_logger()
    settings = get_settings()
    temp_files = []
    
    # Создаем папку для переведенных изображений
    translated_folder = folder_path.replace(settings.books_dir, settings.translated_books_dir)
    os.makedirs(translated_folder, exist_ok=True)
    
    try:
        # Получаем список изображений в папке
        if selected_images:
            # Сортируем выбранные изображения по естественному порядку
            image_paths = sorted(selected_images, key=lambda x: natural_sort_key(os.path.basename(x)))
            logger.debug(f"Выбранные изображения после сортировки: {[os.path.basename(path) for path in image_paths]}")
        else:
            image_paths = []
            # Используем естественную сортировку для файлов в папке
            for image_name in sorted(os.listdir(folder_path), key=natural_sort_key):
                image_path = os.path.join(folder_path, image_name)
                if os.path.isfile(image_path) and image_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    image_paths.append(image_path)
        
        logger.info(f"Будет обработано {len(image_paths)} файлов из папки {os.path.basename(folder_path)}")
        
        # Создаем batch_id для группы файлов если включен режим редактирования
        batch_id = f"batch_{generate_unique_filename('', '')}" if edit_mode else None
        
        # Увеличиваем количество параллельных задач до 6
        max_workers = min(12, len(image_paths))
        logger.info(f"Используем {max_workers} потоков для обработки")
        
        # Хранит результаты с исходной позицией для сортировки
        results_with_order = []
        
        # Обрабатываем изображения параллельно
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Создаем словарь для отслеживания порядка файлов
            future_to_index = {}
            futures = []
            
            # Создаем список задач с задержкой между запусками
            for i, image_path in enumerate(image_paths):
                future = executor.submit(
                    process_single_image, 
                    image_path, 
                    translation_method, 
                    openai_api_key, 
                    ocr_engine,
                    translated_folder,
                    edit_mode,
                    batch_id,  # Передаем batch_id
                    i,  # Передаем индекс файла
                    source_language,  # Передаем исходный язык
                    target_language   # Передаем язык перевода
                )
                # Связываем future с индексом в исходном списке и именем файла
                future_to_index[future] = {
                    'index': i,
                    'filename': os.path.basename(image_path)
                }
                futures.append(future)
                
                # Добавляем задержку в 4 секунды между запусками потоков
                if i < len(image_paths) - 1:
                    logger.debug(f"Ожидание 4 секунды перед запуском следующего потока...")
                    time.sleep(4)
            
            # Собираем результаты по мере завершения задач
            for future in concurrent.futures.as_completed(futures):
                try:
                    file_path, file_result = future.result()
                    file_info = future_to_index[future]
                    original_index = file_info['index']
                    file_name = file_info['filename']
                    
                    # Добавляем индекс и имя файла для сортировки
                    file_result['original_index'] = original_index
                    file_result['filename'] = file_name
                    
                    # Добавляем batch_id в результаты
                    if edit_mode and batch_id:
                        file_result['edit_batch_id'] = batch_id
                    
                    logger.info(f"Завершена обработка {file_name} (индекс: {original_index})")
                    
                    # Добавляем путь к временному файлу для последующего удаления
                    temp_files.append(file_path)
                    
                    # Если нет ошибки, добавляем результат с позицией
                    if not (file_result.get('error', False)):
                        results_with_order.append(file_result)
                    else:
                        logger.error(f"Ошибка при обработке {file_name}: {file_result.get('error_message', 'Неизвестная ошибка')}")
                except Exception as e:
                    logger.error(f"Исключение при обработке изображения: {str(e)}")
        
        # Сортируем результаты по исходному порядку
        results = sorted(results_with_order, key=lambda x: x['original_index'])
        logger.debug(f"Порядок сортировки результатов: {[result['filename'] for result in results]}")
        return results
        
    finally:
        # Удаляем временные файлы
        for file_path in temp_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Ошибка при удалении временного файла {file_path}: {e}")
    
    return results