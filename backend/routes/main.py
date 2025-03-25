from . import main_bp
from flask import render_template, request, flash
from backend.auth import get_current_user, login_required
import os
import uuid
import time
import concurrent.futures
import re
from backend.config import get_settings
from backend.file_utils.processing import process_single_file, process_manga_folder
from backend.file_utils.folders import get_manga_folders, natural_sort_key
from backend.models import get_optimal_ocr_engine

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """Главная страница приложения"""
    current_user = get_current_user()
    settings = get_settings()
    USE_GPU = settings.use_gpu


    results = None
    error = None
    
    # Получаем список папок с мангой
    manga_folders = get_manga_folders()
    
    if request.method == 'POST':
        # Определяем тип формы
        form_type = request.form.get('form_type', 'individual_files')
    
        # Получаем метод перевода и API ключ
        translation_method = request.form.get('translation_method', 'google')
        openai_api_key = request.form.get('openai_api_key', '')
    
        # Получаем OCR движок (если указан вручную)
        manual_ocr_engine = request.form.get('ocr_engine')
        
        edit_mode = request.form.get('edit_mode', 'false') == 'true'

        # Получаем языки перевода
        source_language = request.form.get('source_language', 'zh')
        target_language = request.form.get('target_language', 'ru')

        # Всегда используем оптимальный OCR-движок для выбранного языка
        ocr_engine = get_optimal_ocr_engine(source_language)

        # Проверяем, что API ключ OpenAI указан, если выбран этот метод
        if translation_method == 'openai' and not openai_api_key:
            error = "Необходимо указать API ключ OpenAI для перевода через gpt-4o-mini"
            return render_template('index.html', results=None, error=error, 
                                 manga_folders=manga_folders, use_gpu=USE_GPU, current_user=current_user)
        
        if form_type == 'individual_files':
            if 'files' not in request.files:
                return "Нет файлов", 400
            files = request.files.getlist('files')
            if not files or all(file.filename == '' for file in files):
                return "Файлы не выбраны", 400
            
            temp_files = []
            results_with_order = []
            
            try:
                # Увеличиваем количество параллельных задач до 6
                max_workers = min(12, len(files))
                
                # Создаем уникальный batch_id для группы файлов
                batch_id = f"batch_{uuid.uuid4().hex}" if edit_mode else None
                print(f"Обработка {len(files)} файлов с batch_id: {batch_id}")
                
                # Обрабатываем файлы параллельно
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Создаем словарь для отслеживания порядка файлов
                    future_to_index = {}
                    futures = []
                    file_list = list(files)  # Преобразуем FileStorage в список для индексации
                    
                    # Отладочный вывод исходных имен файлов
                    print(f"Исходные имена файлов: {[file.filename for file in file_list]}")
                    
                    # Создаем список задач с задержкой между запусками
                    for i, file in enumerate(file_list):
                        future = executor.submit(
                            process_single_file, 
                            file, 
                            translation_method, 
                            openai_api_key, 
                            ocr_engine,
                            edit_mode,
                            batch_id,  # Передаем batch_id
                            i,  # Передаем индекс файла
                            source_language,
                            target_language
                        )
                        # Связываем future с индексом файла и именем файла
                        future_to_index[future] = {
                            'index': i,
                            'filename': file.filename
                        }
                        futures.append(future)
                        
                        # Добавляем задержку в 1 секунду между запусками потоков
                        if i < len(file_list) - 1:
                            print(f"Ожидание 1 секунды перед запуском следующего потока...")
                            time.sleep(1)
                    
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
                            
                            # Добавляем batch_id для связывания файлов в режиме редактирования
                            if edit_mode and batch_id:
                                file_result['edit_batch_id'] = batch_id
                            
                            print(f"Завершена обработка {file_name} (индекс: {original_index})")
                            
                            # Добавляем путь к временному файлу для последующего удаления
                            temp_files.append(file_path)
                            
                            # Если нет ошибки, добавляем результат с позицией
                            if not (file_result.get('error', False)):
                                results_with_order.append(file_result)
                            else:
                                error = file_result.get('error_message', 'Неизвестная ошибка')
                                return render_template('index.html', results=None, error=error, 
                                                     manga_folders=manga_folders, use_gpu=USE_GPU, current_user=current_user)
                        except Exception as e:
                            error = f"Ошибка обработки файла: {str(e)}"
                            return render_template('index.html', results=None, error=error, 
                                                 manga_folders=manga_folders, use_gpu=USE_GPU, current_user=current_user)
                
                # Сортируем результаты по исходному порядку
                results = sorted(results_with_order, key=lambda x: x['original_index'])
                
            except Exception as e:
                import traceback
                error_traceback = traceback.format_exc()
                error = f"Ошибка обработки: {str(e)}"
                print(error_traceback)
                return render_template('index.html', results=None, error=error, 
                                     manga_folders=manga_folders, use_gpu=USE_GPU, current_user=current_user)
            finally:
                # Удаляем временные файлы
                for file_path in temp_files:
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except:
                            pass
                        
        # Обработка папок с мангой
        elif form_type == 'manga_folders':
            # Проверка, выбрана ли папка для перевода всей папки
            folder_path = request.form.get('translate_all_folder')
            if folder_path:
                results = process_manga_folder(folder_path, translation_method, 
                                             openai_api_key, ocr_engine, edit_mode=edit_mode, 
                                             source_language=source_language, target_language=target_language)
            else:
                # Проверка, выбрана ли папка и выбранные изображения
                folder_path = request.form.get('folder_path')
                selected_images = request.form.getlist('selected_images')
                
                if folder_path and selected_images:
                    # Сортируем выбранные изображения по естественному порядку
                    selected_images = sorted(selected_images, key=lambda x: natural_sort_key(os.path.basename(x)))
                    results = process_manga_folder(folder_path, translation_method, 
                                                 openai_api_key, ocr_engine, 
                                                 selected_images, edit_mode=edit_mode, 
                                                 source_language=source_language, target_language=target_language)
                elif folder_path:
                    error = "Не выбрано ни одного изображения для перевода"
                    return render_template('index.html', results=None, error=error, 
                                        manga_folders=manga_folders, use_gpu=USE_GPU, current_user=current_user)
                else:
                    error = "Не выбрана папка для перевода"
                    return render_template('index.html', results=None, error=error, 
                                        manga_folders=manga_folders, use_gpu=USE_GPU, current_user=current_user)
    
    # Всегда возвращаем шаблон index.html
    return render_template('index.html', results=results, error=error, 
                          manga_folders=manga_folders, use_gpu=USE_GPU, current_user=current_user)