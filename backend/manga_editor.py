import os
import json
import uuid
import base64
import io
import numpy as np
import cv2
from PIL import Image as PILImage, ImageDraw, ImageFont
import tempfile
import time
import glob
import functools
from threading import Lock

class MangaEditor:
    """
    Модуль для редактирования переведенной манги
    Позволяет пользователям изменять текст перевода и создавать обновленные изображения
    """
    
    def __init__(self, sessions_dir='data/editor_sessions'):
        """
        Инициализация редактора манги
        
        Args:
            sessions_dir: Директория для хранения сессий редактирования
        """
        self.sessions_dir = sessions_dir
        os.makedirs(sessions_dir, exist_ok=True)
        
        # Добавляем кэш для сессий
        self.session_cache = {}
        self.group_cache = {}
        self.cache_lock = Lock()
        self.cache_max_size = 100  # Максимальное количество кэшированных сессий
        
    # Декоратор для кэширования результатов
    def _cache_session(func):
        @functools.wraps(func)
        def wrapper(self, session_id, *args, **kwargs):
            # Проверяем кэш перед вызовом функции
            if session_id in self.session_cache and not kwargs.get('force_reload', False):
                print(f"Использую кэшированную сессию {session_id}")
                return self.session_cache[session_id]
            
            # Вызываем оригинальный метод
            result = func(self, session_id, *args, **kwargs)
            
            # Кэшируем результат
            if result:
                with self.cache_lock:
                    # Очищаем кэш, если он слишком большой
                    if len(self.session_cache) > self.cache_max_size:
                        # Удаляем самые старые записи
                        oldest_keys = sorted(self.session_cache.keys(), 
                                          key=lambda k: self.session_cache[k].get('cache_timestamp', 0))[:10]
                        for key in oldest_keys:
                            del self.session_cache[key]
                    
                    # Добавляем метку времени и кэшируем
                    result['cache_timestamp'] = time.time()
                    self.session_cache[session_id] = result
            
            return result
        
        return wrapper
        
    def clear_session_cache(self, session_id=None):
        """
        Очищает кэш сессий
        
        Args:
            session_id: ID конкретной сессии для очистки (или None для полной очистки)
        """
        with self.cache_lock:
            if session_id:
                if session_id in self.session_cache:
                    session_data = self.session_cache[session_id]
                    group_id = session_data.get('group_id')
                    
                    # Удаляем сессию из кэша
                    del self.session_cache[session_id]
                    
                    # Удаляем сессию из кэша группы
                    if group_id and group_id in self.group_cache:
                        if session_id in self.group_cache[group_id]:
                            del self.group_cache[group_id][session_id]
            else:
                # Очищаем весь кэш
                self.session_cache.clear()
                self.group_cache.clear()
        
    def create_session(self, original_image_path, text_removed_image, text_blocks, text_mask, 
                  group_id=None, file_index=0, original_filename=None, text_background_mask=None, 
                  source_language='zh', target_language='ru'):
        """
        Создает новую сессию редактирования
        
        Args:
            original_image_path: Путь к исходному изображению
            text_removed_image: Изображение с удаленным текстом (numpy array или PIL Image)
            text_blocks: Список блоков текста с координатами и переводом
            text_mask: Маска текста (numpy array)
            group_id: ID группы связанных сессий (optional)
            file_index: Индекс файла в группе для сохранения порядка
            original_filename: Оригинальное имя файла (если отличается от basename original_image_path)
            
        Returns:
            str: ID сессии
        """
        session_id = f"edit_{uuid.uuid4().hex}"
        
        # Создаем временные файлы для изображений
        session_dir = os.path.join(self.sessions_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Сохраняем исходное изображение
        if original_filename is None:
            original_filename = os.path.basename(original_image_path)
        
        print(f"Создание сессии: {session_id}")
        print(f"Оригинальный файл: {original_filename}")
        print(f"Batch ID: {group_id}")
        print(f"Индекс файла: {file_index}")
        
        original_copy_path = os.path.join(session_dir, "original_" + original_filename)
        text_removed_path = os.path.join(session_dir, "text_removed_" + original_filename)
        translated_path = os.path.join(session_dir, "translated_" + original_filename)
        
        # Копируем исходное изображение
        if os.path.exists(original_image_path):
            pil_img = PILImage.open(original_image_path)
            pil_img.save(original_copy_path)
        
        # Сохраняем изображение с удаленным текстом
        if isinstance(text_removed_image, np.ndarray):
            PILImage.fromarray(text_removed_image).save(text_removed_path)
        elif isinstance(text_removed_image, PILImage.Image):
            text_removed_image.save(text_removed_path)
        
        # Создаем переведенное изображение
        if text_blocks and len(text_blocks) > 0:
            try:
                # Создаем переведенное изображение используя существующий метод
                self._create_translated_image(text_removed_path, text_blocks, translated_path, text_mask)
                print(f"Создано переведенное изображение для сессии {session_id}")
            except Exception as e:
                print(f"Ошибка при создании переведенного изображения: {e}")
                # Если не удалось создать переведенное изображение, копируем изображение без текста
                if os.path.exists(text_removed_path):
                    import shutil
                    shutil.copy(text_removed_path, translated_path)
        
        # Преобразуем маску текста в список для сериализации JSON
        text_mask_list = text_mask.tolist() if isinstance(text_mask, np.ndarray) else text_mask
        
        # Если не указан group_id, используем текущий session_id как group_id
        if group_id is None:
            group_id = session_id
            
        # Создаем данные сессии с информацией о группе и индексе
        session_data = {
            "session_id": session_id,
            "group_id": group_id,
            "file_index": file_index,  # Добавляем индекс файла
            "created_at": time.time(),
            "original_filename": original_filename,
            "original_path": original_copy_path,
            "text_removed_path": text_removed_path,
            "translated_path": translated_path,  # Добавляем путь к переведенному изображению
            "text_blocks": text_blocks,
            "text_mask": text_mask_list,
            "source_language": source_language,
            "target_language": target_language
        }
        
        # Сохраняем данные сессии
        session_file = os.path.join(session_dir, "session.json")
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        # Обновляем кэши
        with self.cache_lock:
            # Инициализируем кэш группы, если он не существует
            if group_id not in self.group_cache:
                self.group_cache[group_id] = {}
            
            # Добавляем сессию в кэш группы
            self.group_cache[group_id][session_id] = {
                "session_id": session_id,
                "original_filename": original_filename,
                "file_index": file_index
            }
            
            # Выводим для отладки текущие файлы в группе
            print(f"Файлы в группе {group_id}:")
            for sid, sdata in self.group_cache[group_id].items():
                print(f"  {sid}: {sdata['original_filename']}")
            
            # Добавляем новую сессию в кэш сессий
            session_data['cache_timestamp'] = time.time()
            self.session_cache[session_id] = session_data
        
        return session_id
    
    @_cache_session
    def get_session(self, session_id, force_reload=False):
        """
        Получает данные сессии по ID
        
        Args:
            session_id: ID сессии
            force_reload: Принудительная перезагрузка данных из файла
            
        Returns:
            dict: Данные сессии или None, если сессия не найдена
        """
        try:
            print(f"Получение данных сессии {session_id} (force_reload={force_reload})")
            
            # Загружаем данные сессии из файла, если принудительная перезагрузка
            if force_reload or session_id not in self.session_cache:
                session_dir = os.path.join(self.sessions_dir, session_id)
                session_file = os.path.join(session_dir, "session.json")
                
                if not os.path.exists(session_file):
                    print(f"Файл сессии не существует: {session_file}")
                    return None
                    
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    
                # Определяем группу сессий
                group_id = session_data.get("group_id", session_id)
                print(f"Получен group_id из файла: {group_id}")
                
                # Проверка наличия переведенного изображения и его создание при отсутствии
                if "translated_path" not in session_data and "text_blocks" in session_data:
                    try:
                        text_blocks = session_data["text_blocks"]
                        text_mask = np.array(session_data.get("text_mask", []))
                        text_removed_path = session_data.get("text_removed_path")
                        original_filename = session_data.get("original_filename", "unknown.png")
                        
                        translated_path = os.path.join(session_dir, "translated_" + original_filename)
                        
                        if os.path.exists(text_removed_path):
                            print(f"Создание отсутствующего переведенного изображения для сессии {session_id}")
                            self._create_translated_image(text_removed_path, text_blocks, translated_path, text_mask)
                            session_data["translated_path"] = translated_path
                            
                            # Обновляем файл сессии с новым путем
                            updated_data = session_data.copy()
                            with open(session_file, 'w', encoding='utf-8') as f:
                                json.dump(updated_data, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"Ошибка при создании переведенного изображения для сессии {session_id}: {e}")
                
                # Обновляем кэш группы для текущей сессии
                self._update_group_cache(group_id, session_id, session_data)
                
                # Сохраняем сессию в кэше
                with self.cache_lock:
                    session_data['cache_timestamp'] = time.time()
                    self.session_cache[session_id] = session_data.copy()
            else:
                # Используем кэшированные данные
                session_data = self.session_cache[session_id].copy()
                group_id = session_data.get("group_id", session_id)
                print(f"Получен group_id из кэша: {group_id}")
            
            # Всегда получаем обновленный список файлов группы
            all_files = self._get_group_files(group_id)
            
            # Сортируем файлы по индексу
            all_files.sort(key=lambda x: x.get("file_index", 0))
            
            # Фильтруем связанные сессии - исключаем текущую
            related_sessions = [f for f in all_files if f.get("session_id") != session_id]
            
            # Добавляем информацию в данные сессии
            session_data['all_files'] = all_files
            session_data['related_sessions'] = related_sessions
            
            print(f"Для сессии {session_id} найдено {len(all_files)} файлов в группе {group_id}")
            print(f"Связанные сессии: {len(related_sessions)}")
            
            return session_data
        except Exception as e:
            print(f"Ошибка при получении сессии {session_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _update_group_cache(self, group_id, session_id, session_data):
        """
        Обновляет кэш группы для указанной сессии
        
        Args:
            group_id: ID группы
            session_id: ID сессии
            session_data: Данные сессии
        """
        with self.cache_lock:
            # Инициализируем кэш группы, если он не существует
            if group_id not in self.group_cache:
                self.group_cache[group_id] = {}
            
            # Добавляем/обновляем сессию в кэше группы
            self.group_cache[group_id][session_id] = {
                "session_id": session_id,
                "original_filename": session_data.get("original_filename", "unknown.png"),
                "file_index": session_data.get("file_index", 0)
            }

    def _get_group_files(self, group_id):
        """
        Получает список всех файлов в группе
        
        Args:
            group_id: ID группы
            
        Returns:
            list: Список файлов в группе
        """
        try:
            # Всегда ищем на диске все файлы, и игнорируем кэш
            print(f"Поиск файлов для группы {group_id} в файловой системе")
            
            disk_files = []
            
            for session_dir in glob.glob(os.path.join(self.sessions_dir, "edit_*")):
                current_id = os.path.basename(session_dir)
                session_file = os.path.join(session_dir, "session.json")
                
                if not os.path.exists(session_file):
                    continue
                    
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        try:
                            file_data = json.load(f)
                        except json.JSONDecodeError:
                            print(f"Пропуск сессии {current_id}: ошибка формата JSON")
                            continue
                        
                    # Проверяем, входит ли в ту же группу
                    file_group_id = file_data.get("group_id")
                    if file_group_id == group_id:
                        # Получаем оригинальное имя файла
                        original_filename = file_data.get("original_filename", "unknown.png")
                        
                        file_info = {
                            "session_id": current_id,
                            "original_filename": original_filename,
                            "file_index": file_data.get("file_index", 0)
                        }
                        disk_files.append(file_info)
                        
                        # Обновляем кэш группы
                        with self.cache_lock:
                            if group_id not in self.group_cache:
                                self.group_cache[group_id] = {}
                            self.group_cache[group_id][current_id] = file_info
                        
                        print(f"Нашли файл в группе {group_id}: {current_id} - {original_filename}")
                except Exception as e:
                    print(f"Пропуск сессии {current_id}: {str(e)}")
            
            # Обновляем кэш группы полным списком найденных файлов
            with self.cache_lock:
                if disk_files:
                    self.group_cache[group_id] = {
                        file_info['session_id']: file_info 
                        for file_info in disk_files
                    }
            
            print(f"Найдено {len(disk_files)} файлов для группы {group_id}")
            
            return disk_files
        except Exception as e:
            print(f"Ошибка при получении файлов группы {group_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def update_translation(self, session_id, block_id, new_text, style=None):
        """
        Обновляет перевод и стиль текстового блока
        
        Args:
            session_id: ID сессии
            block_id: ID блока текста
            new_text: Новый текст перевода
            style: Словарь со стилями текста (опционально)
            
        Returns:
            bool: True если обновление успешно, иначе False
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        # Обновляем текст и стиль для указанного блока
        text_blocks = session_data.get("text_blocks", [])
        updated = False
        
        for block in text_blocks:
            if block['id'] == block_id:
                block['translated_text'] = new_text
                
                # Обновляем стиль, если он предоставлен
                if style is not None:
                    # Инициализируем стиль, если его нет
                    if 'style' not in block:
                        block['style'] = {}
                    
                    # Обновляем только предоставленные поля стиля
                    for key, value in style.items():
                        block['style'][key] = value
                
                updated = True
                break
        
        if not updated:
            return False
            
        # Обновляем данные сессии
        session_data["text_blocks"] = text_blocks
        
        # Удаляем служебные поля перед сохранением
        clean_session_data = session_data.copy()
        for key in ['related_sessions', 'all_files', 'cache_timestamp']:
            if key in clean_session_data:
                del clean_session_data[key]
                
        session_dir = os.path.join(self.sessions_dir, session_id)
        session_file = os.path.join(session_dir, "session.json")
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(clean_session_data, f, ensure_ascii=False, indent=2)
            
        # Обновляем кэш
        with self.cache_lock:
            self.session_cache[session_id] = session_data
            
        return True
    
    def generate_preview(self, session_id):
        """
        Генерирует предпросмотр с обновленным текстом
        
        Args:
            session_id: ID сессии
            
        Returns:
            str: Base64-encoded изображение предпросмотра или None в случае ошибки
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return None
        
        # Получаем необходимые данные
        text_removed_path = session_data.get("text_removed_path")
        text_blocks = session_data.get("text_blocks", [])
        text_mask = np.array(session_data.get("text_mask", []))
        
        if not os.path.exists(text_removed_path) or not text_blocks:
            return None
            
        # Создаем временный файл для предпросмотра
        session_dir = os.path.join(self.sessions_dir, session_id)
        preview_path = os.path.join(session_dir, "preview.png")
        
        try:
            # Генерируем изображение с обновленным текстом
            self._create_translated_image(text_removed_path, text_blocks, preview_path, text_mask)
            
            # Преобразуем в base64
            preview_img = PILImage.open(preview_path)
            buffered = io.BytesIO()
            preview_img.save(buffered, format="PNG")
            preview_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return preview_base64
        except Exception as e:
            print(f"Ошибка генерации предпросмотра: {e}")
            return None
    
    def save_edited_image(self, session_id, filename=None):
        """
        Сохраняет отредактированное изображение
        
        Args:
            session_id: ID сессии
            filename: Имя файла для сохранения (опционально)
            
        Returns:
            tuple: (успех (bool), путь к сохраненному файлу или сообщение об ошибке)
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False, "Сессия не найдена"
        
        # Получаем необходимые данные
        text_removed_path = session_data.get("text_removed_path")
        text_blocks = session_data.get("text_blocks", [])
        text_mask = np.array(session_data.get("text_mask", []))
        original_filename = session_data.get("original_filename", "edited_manga.png")
        
        if not os.path.exists(text_removed_path) or not text_blocks:
            return False, "Недостаточно данных для создания изображения"
        
        # Определяем имя файла для сохранения
        if not filename:
            # Генерируем имя файла из оригинального
            filename = f"edited_{original_filename}"
        
        # Путь для сохранения в папке translated_books
        save_path = os.path.join("translated_books", filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        try:
            # Генерируем финальное изображение
            self._create_translated_image(text_removed_path, text_blocks, save_path, text_mask)
            return True, save_path
        except Exception as e:
            print(f"Ошибка сохранения отредактированного изображения: {e}")
            return False, str(e)
    
    def cleanup_old_sessions(self, max_age_hours=24):
        """
        Удаляет старые сессии редактирования
        
        Args:
            max_age_hours: Максимальный возраст сессии в часах
        """
        now = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for session_id in os.listdir(self.sessions_dir):
            session_dir = os.path.join(self.sessions_dir, session_id)
            session_file = os.path.join(session_dir, "session.json")
            
            try:
                if not os.path.exists(session_file):
                    continue
                    
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                created_at = session_data.get("created_at", 0)
                if now - created_at > max_age_seconds:
                    # Удаляем из кэша
                    self.clear_session_cache(session_id)
                    
                    # Удаляем все файлы в директории
                    for file in os.listdir(session_dir):
                        os.remove(os.path.join(session_dir, file))
                    # Удаляем директорию
                    os.rmdir(session_dir)
            except Exception as e:
                print(f"Ошибка при очистке сессии {session_id}: {e}")
    
    def _create_translated_image(self, image_path, text_blocks, output_path, text_mask):
        """
        Создает изображение с переведенным текстом с учетом стилей
        
        Args:
            image_path: Путь к изображению без текста
            text_blocks: Список блоков текста с координатами и переводом
            output_path: Путь для сохранения результата
            text_mask: Маска текста
        """
        print("Создание изображения с переводом...")
        img = PILImage.open(image_path)
        img_np = np.array(img)
        draw = ImageDraw.Draw(img)
        
        # Загружаем доступные шрифты
        fonts = self._load_available_fonts()
        
        # Обрабатываем каждый текстовый блок
        for block in text_blocks:
            if not block['translated_text']:
                continue
                
            x_min, y_min, x_max, y_max = block['box']
            text = block['translated_text'].strip()
            
            # Получаем стиль блока или используем значения по умолчанию
            style = block.get('style', {})
            
            # Рисуем текст для этого блока с учетом стиля
            self._draw_wrapped_text(draw, fonts, text, (x_min, y_min, x_max, y_max), style)
        
        # Сохраняем результат
        img.save(output_path)
        print(f"Изображение с переводом сохранено как {output_path}")
        return output_path
    
    def _load_available_fonts(self):
        """
        Загружает доступные шрифты для различных стилей
        
        Returns:
            dict: Словарь шрифтов разных стилей и размеров
        """
        fonts = {}
        
        # Пути к шрифтам для разных стилей
        font_paths = {
            'normal': ["data/fonts/anime-ace-v02.ttf", "arial.ttf", "C:/Windows/Fonts/Arial.ttf", "C:/Windows/Fonts/Calibri.ttf"],
            'bold': ["data/fonts/anime-ace-bb.ttf", "C:/Windows/Fonts/Arialbd.ttf", "C:/Windows/Fonts/Calibrib.ttf"],
            'italic': ["data/fonts/anime-ace-it.ttf", "C:/Windows/Fonts/Ariali.ttf", "C:/Windows/Fonts/Calibrii.ttf"],
            'bold_italic': ["data/fonts/anime-ace-bb-it.ttf", "C:/Windows/Fonts/Arialbi.ttf", "C:/Windows/Fonts/Calibriz.ttf"]
        }
        
        # Загружаем шрифты разных размеров
        for style, paths in font_paths.items():
            fonts[style] = {}
            
            for size in range(8, 33, 2):  # Размеры от 8 до 32 с шагом 2
                for path in paths:
                    try:
                        fonts[style][size] = ImageFont.truetype(path, size)
                        print(f"Загружен шрифт {style} размера {size}: {path}")
                        break
                    except Exception:
                        continue
                
                # Если не удалось загрузить шрифт, используем шрифт по умолчанию
                if size not in fonts[style]:
                    fonts[style][size] = ImageFont.load_default()
                    print(f"Используется шрифт по умолчанию для {style} размера {size}")
        
        return fonts

    def _draw_wrapped_text(self, draw, fonts, text, box, style=None):
        """
        Улучшенная функция для интеллектуального переноса и рисования текста с учетом стилей
        
        Args:
            draw: ImageDraw объект
            fonts: Словарь доступных шрифтов
            text: Текст для отображения
            box: Координаты box (x_min, y_min, x_max, y_max)
            style: Словарь со стилями текста
        """
        if style is None:
            style = {}
        
        # Извлекаем и применяем стили
        x_min, y_min, x_max, y_max = box
        font_size = style.get('font_size', 16)
        font_weight = style.get('font_weight', 'normal')
        font_style = style.get('font_style', 'normal')
        align = style.get('align', 'center')
        offset_x = style.get('offset_x', 0)
        offset_y = style.get('offset_y', 0)
        
        # Применяем смещение
        x_min += offset_x
        y_min += offset_y
        x_max += offset_x
        y_max += offset_y
        
        # Определяем ключ для выбора шрифта
        if font_weight == 'bold' and font_style == 'italic':
            font_key = 'bold_italic'
        elif font_weight == 'bold':
            font_key = 'bold'
        elif font_style == 'italic':
            font_key = 'italic'
        else:
            font_key = 'normal'
        
        # Выбираем ближайший доступный размер шрифта
        available_sizes = list(fonts.get(font_key, {}).keys())
        if available_sizes:
            closest_size = min(available_sizes, key=lambda x: abs(x - font_size))
            font = fonts[font_key][closest_size]
        else:
            # Если шрифт не найден, используем стандартный
            font = ImageFont.load_default()
        
        max_width = x_max - x_min - 15
        
        # Получаем размеры шрифта
        left, top, right, bottom = draw.textbbox((0, 0), 'А', font=font)
        char_height = bottom - top
        
        # Настраиваем межстрочный интервал в зависимости от размера шрифта
        line_spacing = max(6, int(font_size * 0.3))
        
        # Обрабатываем явные переносы строк в тексте
        paragraphs = text.split('\n')
        wrapped_text = []
        
        for paragraph in paragraphs:
            # Разбиваем параграф на части
            import re
            
            # Разбиваем на предложения
            sentences = re.split(r'([.!?]\s+)', paragraph)
            sentence_chunks = []
            
            for i in range(0, len(sentences)-1, 2):
                if i+1 < len(sentences):
                    sentence_chunks.append(sentences[i] + sentences[i+1])
                else:
                    sentence_chunks.append(sentences[i])
            
            if len(sentences) % 2 == 1:
                sentence_chunks.append(sentences[-1])
            
            # Обрабатываем каждое предложение
            for sentence in sentence_chunks:
                # Разбиваем предложение на части по знакам препинания
                parts = re.split(r'([,:;]\s+)', sentence)
                parts_combined = []
                
                for i in range(0, len(parts)-1, 2):
                    if i+1 < len(parts):
                        parts_combined.append(parts[i] + parts[i+1])
                    else:
                        parts_combined.append(parts[i])
                
                if len(parts) % 2 == 1:
                    parts_combined.append(parts[-1])
                
                # Обрабатываем каждую часть
                for part in parts_combined:
                    words = part.split()
                    current_line = ""
                    
                    for word in words:
                        test_line = current_line + " " + word if current_line else word
                        left, top, right, bottom = draw.textbbox((0, 0), test_line, font=font)
                        line_width = right - left
                        
                        if line_width <= max_width:
                            current_line = test_line
                        else:
                            if current_line:
                                wrapped_text.append(current_line)
                            current_line = word
                    
                    if current_line:
                        wrapped_text.append(current_line)
            
            # Добавляем пустую строку между параграфами, если не последний параграф
            if paragraph != paragraphs[-1]:
                wrapped_text.append("")
        
        # Рисуем текст с учетом выравнивания
        if wrapped_text:
            # Считаем высоту всего текста
            text_height_total = len(wrapped_text) * (char_height + line_spacing)
            y_start = y_min + ((y_max - y_min - text_height_total) / 2)
            
            for i, line in enumerate(wrapped_text):
                if not line:  # Пропускаем пустые строки
                    continue
                    
                left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
                text_width = right - left
                
                # Определяем позицию в зависимости от выравнивания
                if align == 'left':
                    x_pos = x_min + 5  # Небольшой отступ
                elif align == 'right':
                    x_pos = x_max - text_width - 5  # Небольшой отступ
                else:  # center
                    x_pos = x_min + ((x_max - x_min - text_width) / 2)
                
                y_pos = y_start + (i * (char_height + line_spacing))
                
                # Добавляем белую обводку для лучшей читаемости 
                for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                    draw.text((x_pos + dx, y_pos + dy), line, fill="white", font=font)
                
                # Основной текст черным
                draw.text((x_pos, y_pos), line, fill="black", font=font)