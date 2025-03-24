import os
import torch
import cv2
import numpy as np
import pytesseract
import tempfile
from PIL import Image
from manga_ocr import MangaOcr
from paddleocr import PaddleOCR
import easyocr

from .constants import (
    PADDLE_OCR_LANGS, 
    TESSERACT_LANG_CODES, 
    OPTIMAL_OCR_ENGINES
)

# Кэширование OCR-движков
__MOCR = None
__PADDLE_OCR_CACHE = {}
__EASY_OCR_CACHE = {}
__TESSERACT_INITIALIZED = False
__TESSERACT_AVAILABLE_LANGS = []
__TESSERACT_FALLBACK = {} 

def get_device(use_gpu):
    """Возвращает устройство для моделей в зависимости от настроек"""
    if use_gpu and torch.cuda.is_available():
        return "cuda"
    else:
        return "cpu"

def get_mangaocr(use_gpu=False):
    """
    Инициализирует MangaOCR (ленивая инициализация)
    
    Args:
        use_gpu: Использовать ли GPU
        
    Returns:
        MangaOcr: Экземпляр MangaOcr
    """
    global __MOCR
    if __MOCR is None:
        device = get_device(use_gpu)
        # Для manga_ocr определяем устройство через переменную окружения,
        # т.к. библиотека может использовать torch.device() внутри
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1" if device == "cpu" else "0"
        __MOCR = MangaOcr()
    return __MOCR

def get_paddleocr(lang='ch', use_gpu=False):
    """
    Ленивая инициализация PaddleOCR с кэшем для разных языков
    
    Args:
        lang: Код языка в формате PaddleOCR
        use_gpu: Использовать ли GPU
        
    Returns:
        PaddleOCR: Экземпляр PaddleOCR
    """
    global __PADDLE_OCR_CACHE
    
    # Если такой язык уже инициализирован, возвращаем из кэша
    if lang in __PADDLE_OCR_CACHE:
        return __PADDLE_OCR_CACHE[lang]
    
    # Преобразуем код языка в формат PaddleOCR
    paddle_lang = PADDLE_OCR_LANGS.get(lang, 'ch')
    device = use_gpu and torch.cuda.is_available()
    
    # Создаем новый экземпляр и сохраняем в кэш
    ocr = PaddleOCR(use_angle_cls=True, lang=paddle_lang, use_gpu=device)
    __PADDLE_OCR_CACHE[lang] = ocr
    
    return ocr

def get_easyocr(lang='ko', use_gpu=False):
    """
    Ленивая инициализация EasyOCR с кэшем для разных языков
    
    Args:
        lang: Код языка (ko, ja, zh, en и т.д.)
        use_gpu: Использовать ли GPU
        
    Returns:
        easyocr.Reader: Экземпляр EasyOCR
    """
    global __EASY_OCR_CACHE
    
    # Преобразуем коды языков в формат EasyOCR
    lang_map = {
        'ko': 'ko',       # Корейский
        'ja': 'ja',       # Японский
        'zh': 'ch_sim',   # Китайский (упрощенный)
        'en': 'en',       # Английский
        'ru': 'ru',       # Русский
        'fr': 'fr',       # Французский
        'es': 'es',       # Испанский
        'de': 'de'        # Немецкий
    }
    
    # Получаем код языка в формате EasyOCR
    ocr_lang = lang_map.get(lang, 'ko')
    
    # Если такой язык уже инициализирован, возвращаем из кэша
    if ocr_lang in __EASY_OCR_CACHE:
        return __EASY_OCR_CACHE[ocr_lang]
    
    # Определяем, использовать ли GPU
    device = get_device(use_gpu)
    use_gpu_flag = device == "cuda"
    
    # Создаем новый экземпляр и сохраняем в кэш
    print(f"Инициализация EasyOCR для языка {ocr_lang} (GPU: {use_gpu_flag})")
    reader = easyocr.Reader([ocr_lang], gpu=use_gpu_flag)
    __EASY_OCR_CACHE[ocr_lang] = reader
    
    return reader

def get_tesseract(lang='eng'):
    """
    Проверяет доступность Tesseract OCR для указанного языка
    
    Args:
        lang: Код языка в формате Tesseract
        
    Returns:
        bool: True если язык доступен, иначе False
    """
    global __TESSERACT_INITIALIZED, __TESSERACT_AVAILABLE_LANGS
    
    # Если Tesseract уже инициализирован, проверяем наличие языка
    if __TESSERACT_INITIALIZED:
        return lang in __TESSERACT_AVAILABLE_LANGS
    
    try:
        # Для Windows устанавливаем путь к исполняемому файлу
        if os.name == 'nt':
            tesseract_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe'
            ]
            
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    print(f"Используется Tesseract из {path}")
                    break
        
        # Проверяем версию Tesseract
        version = pytesseract.get_tesseract_version()
        print(f"Найден Tesseract OCR версии: {version}")
        
        # Получаем список доступных языков
        __TESSERACT_AVAILABLE_LANGS = pytesseract.get_languages()
        print(f"Доступные языки Tesseract: {__TESSERACT_AVAILABLE_LANGS}")
        
        __TESSERACT_INITIALIZED = True
        
        # Проверяем, доступен ли запрошенный язык
        return lang in __TESSERACT_AVAILABLE_LANGS
        
    except Exception as e:
        print(f"Ошибка инициализации Tesseract OCR: {e}")
        __TESSERACT_INITIALIZED = False
        return False

def get_optimal_ocr_engine(source_language):
    """
    Определяет оптимальный OCR-движок для указанного языка с учётом доступности
    
    Args:
        source_language: Код языка (ja, zh, ko, en и т.д.)
        
    Returns:
        str: Название OCR-движка ('mangaocr', 'paddleocr', 'easyocr' или 'tesseract')
    """
    # Получаем рекомендуемый OCR-движок из словаря
    recommended_engine = OPTIMAL_OCR_ENGINES.get(source_language, 'paddleocr')
    
    # Если рекомендуется Tesseract, проверяем его доступность
    if recommended_engine == 'tesseract':
        tesseract_lang = TESSERACT_LANG_CODES.get(source_language, 'eng')
        if not get_tesseract(tesseract_lang):
            # Если Tesseract недоступен, используем запасной вариант
            print(f"Tesseract недоступен для языка {source_language}, используем запасной OCR")
            
            # Для английского и других европейских языков запасной вариант - EasyOCR
            if source_language in ['en', 'fr', 'de', 'es', 'it', 'pt']:
                return 'easyocr'
            else:
                return 'paddleocr'
    
    return recommended_engine

def preprocess_image(image, language='zh', ocr_engine='paddleocr', block_id=None, debug_dir=None):
    """
    Универсальная функция предобработки изображения для различных OCR-движков.
    
    Args:
        image: Изображение (numpy array)
        language: Код языка ('zh', 'ja', 'ko', 'en', и т.д.)
        ocr_engine: OCR-движок ('paddleocr', 'mangaocr', 'easyocr', 'tesseract')
        block_id: ID блока для отладки
        debug_dir: Директория для сохранения промежуточных результатов
        
    Returns:
        numpy.ndarray: Обработанное изображение
    """
    # Дебаг-функция
    def save_debug(img, name):
        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)
            path = os.path.join(debug_dir, f"block_{block_id}_{name}.png")
            cv2.imwrite(path, img)
            print(f"Сохранено отладочное изображение: {path}")
    
    # Сохраняем исходное изображение
    save_debug(image, "original")
    
    # 1. ОСОБЫЙ СЛУЧАЙ: Для PaddleOCR с китайским не меняем логику
    if ocr_engine == 'paddleocr' and language == 'zh':
        # 1.1. Увеличиваем изображение в 3 раза
        height, width = image.shape[:2]
        upscaled = cv2.resize(image, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)
        save_debug(upscaled, "upscaled")
        
        # 1.2. Конвертируем в оттенки серого
        if len(upscaled.shape) == 3:
            gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
        else:
            gray = upscaled.copy()
        save_debug(gray, "gray")
        
        # 1.3. Применяем легкий GaussianBlur
        smoothed = cv2.GaussianBlur(gray, (3, 3), sigmaX=0.5, sigmaY=0.5)
        save_debug(smoothed, "smoothed")
        
        # 1.4. Усиливаем контраст с CLAHE
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(smoothed)
        save_debug(enhanced, "enhanced")

        # 1.5. Проверяем распределение пикселей для определения фона
        pixel_counts = np.bincount(enhanced.flatten(), minlength=256)
        if pixel_counts[0] > pixel_counts[255]:  # Если больше темных пикселей
            enhanced = cv2.bitwise_not(enhanced)
            save_debug(enhanced, "inverted")

        # 1.6. Применяем метод Оцу
        _, otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        save_debug(otsu, "otsu")
        
        # 1.7. Инвертируем для черного текста на белом
        final = cv2.bitwise_not(otsu)
        save_debug(final, "final")
        
        return final

    # 2. Для корейского языка
    if language == 'ko':
        # 2.1. Масштабирование - увеличиваем больше для корейского
        height, width = image.shape[:2]
        upscaled = cv2.resize(image, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)
        save_debug(upscaled, "upscaled")
        
        # 2.2. Конвертируем в оттенки серого
        if len(upscaled.shape) == 3:
            gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
        else:
            gray = upscaled.copy()
        save_debug(gray, "gray")
        
        # 2.3. Адаптивная бинаризация лучше работает для корейского
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 5
        )
        save_debug(binary, "binary")
        
        # 2.4. Морфологические операции для корейского
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        save_debug(morphed, "morphed")
        
        # 2.5. Инвертируем для черного текста на белом
        final = cv2.bitwise_not(morphed)
        save_debug(final, "final")
        
        return final
    
    # 3. Для Tesseract (европейские языки)
    if ocr_engine == 'tesseract' and language in ['en', 'fr', 'de', 'es', 'it', 'pt']:
        # 3.1. Масштабирование
        height, width = image.shape[:2]
        upscaled = cv2.resize(image, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)
        save_debug(upscaled, "upscaled")
        
        # 3.2. Конвертируем в оттенки серого
        if len(upscaled.shape) == 3:
            gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
        else:
            gray = upscaled.copy()
        save_debug(gray, "gray")
        
        # 3.3. Билатеральный фильтр лучше для текста на латинице
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        save_debug(filtered, "filtered")
        
        # 3.4. Повышаем контраст
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(filtered)
        save_debug(enhanced, "enhanced")
        
        # 3.5. Адаптивная бинаризация для латиницы
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 7
        )
        save_debug(binary, "binary")
        
        # 3.6. Морфологические операции
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        dilated = cv2.dilate(binary, kernel, iterations=1)
        save_debug(dilated, "dilated")
        
        # Для Tesseract нам нужен черный текст на белом
        if np.mean(dilated) > 127:  # Если средняя яркость высокая (больше белого)
            final = cv2.bitwise_not(dilated)
            save_debug(final, "final_inverted")
        else:
            final = dilated
            save_debug(final, "final")
        
        return final
    
    # 4. Для японского языка
    if language == 'ja':
        # 4.1. Масштабирование
        height, width = image.shape[:2]
        upscaled = cv2.resize(image, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)
        save_debug(upscaled, "upscaled")
        
        # 4.2. Конвертируем в оттенки серого
        if len(upscaled.shape) == 3:
            gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
        else:
            gray = upscaled.copy()
        save_debug(gray, "gray")
        
        # 4.3. Улучшаем контраст
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        save_debug(enhanced, "enhanced")
        
        # 4.4. Бинаризация Оцу
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        save_debug(binary, "binary")
        
        # 4.5. Инвертируем для черного текста на белом
        final = cv2.bitwise_not(binary)
        save_debug(final, "final")
        
        return final
    
    # 5. Для всех остальных случаев используем общую логику
    # 5.1. Масштабирование
    height, width = image.shape[:2]
    upscaled = cv2.resize(image, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)
    save_debug(upscaled, "upscaled")
    
    # 5.2. Конвертируем в оттенки серого
    if len(upscaled.shape) == 3:
        gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
    else:
        gray = upscaled.copy()
    save_debug(gray, "gray")
    
    # 5.3. Уменьшаем шум
    smoothed = cv2.GaussianBlur(gray, (3, 3), sigmaX=0.5, sigmaY=0.5)
    save_debug(smoothed, "smoothed")
    
    # 5.4. Улучшаем контраст
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(smoothed)
    save_debug(enhanced, "enhanced")
    
    # 5.5. Проверка инверсии
    pixel_counts = np.bincount(enhanced.flatten(), minlength=256)
    if pixel_counts[0] > pixel_counts[255]:
        enhanced = cv2.bitwise_not(enhanced)
        save_debug(enhanced, "inverted")
    
    # 5.6. Бинаризация
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    save_debug(binary, "binary")
    
    # 5.7. Инвертируем для черного текста на белом
    final = cv2.bitwise_not(binary)
    save_debug(final, "final")
    
    return final

def get_tesseract_config(lang):
    """
    Получает оптимальную конфигурацию Tesseract для конкретного языка
    
    Args:
        lang (str): Код языка (en, fr, de и т.д.)
        
    Returns:
        str: Строка конфигурации для Tesseract
    """
    # Общие параметры для всех языков
    base_config = '--psm 6'  # Предполагаем однострочный блок текста
    
    # Специфичные настройки для латинских языков
    if lang in ['en', 'fr', 'de', 'es', 'it', 'pt']:
        return f'{base_config} --oem 3'  # Используем LSTM движок для лучшего распознавания
    
    # Для остальных языков
    return f'{base_config} --oem 1'  # Используем только LSTM

def ocr_with_mangaocr(image_path, block_id, language='ja', use_gpu=False):
    """
    OCR с MangaOCR и унифицированной предобработкой
    
    Args:
        image_path: Путь к изображению
        block_id: ID блока для отладки
        language: Код языка
        use_gpu: Использовать ли GPU
        
    Returns:
        str: Распознанный текст
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"Ошибка чтения изображения {image_path}")
        return ""
    
    # Предобработка с единой функцией
    processed = preprocess_image(image, language=language, ocr_engine='mangaocr', block_id=block_id)
    
    # Сохраняем обработанное изображение
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
        temp_path = temp.name
        cv2.imwrite(temp_path, processed)
    
    try:
        mocr = get_mangaocr(use_gpu)
        text = mocr(temp_path)
        return text
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def ocr_with_paddle(image_path, block_id, lang='ch', use_gpu=False):
    """
    OCR с PaddleOCR и унифицированной предобработкой
    
    Args:
        image_path: Путь к изображению
        block_id: ID блока для отладки
        lang: Код языка
        use_gpu: Использовать ли GPU
        
    Returns:
        str: Распознанный текст
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"Ошибка чтения изображения {image_path}")
        return ""
    
    # Предобработка с единой функцией
    processed = preprocess_image(image, language=lang, ocr_engine='paddleocr', block_id=block_id)
    
    # Сохраняем обработанное изображение
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
        temp_path = temp.name
        cv2.imwrite(temp_path, processed)
    
    try:
        # Использование кэшированного OCR-движка с учетом языка
        reader = get_paddleocr(lang, use_gpu)
        result = reader.ocr(temp_path)
        if result and result[0]:
            text = " ".join([line[1][0] for line in result[0]])
            return text
        return ""
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def ocr_with_easyocr(image_path, block_id, lang='ko', use_gpu=False):
    """
    OCR с EasyOCR и унифицированной предобработкой
    
    Args:
        image_path: Путь к изображению
        block_id: ID блока для отладки
        lang: Код языка
        use_gpu: Использовать ли GPU
        
    Returns:
        str: Распознанный текст
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"Ошибка чтения изображения {image_path}")
        return ""
    
    # Предобработка с единой функцией
    processed = preprocess_image(image, language=lang, ocr_engine='easyocr', block_id=block_id)
    
    # Сохраняем обработанное изображение
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
        temp_path = temp.name
        cv2.imwrite(temp_path, processed)
    
    try:
        reader = get_easyocr(lang, use_gpu)
        
        # Для корейского используем поддержку вертикального текста
        if lang == 'ko':
            result = reader.readtext(
                temp_path,
                detail=0,
                paragraph=False,
                contrast_ths=0.15,      
                adjust_contrast=0.5,    
                width_ths=0.5,          
                height_ths=0.5,         
                rotation_info=[0, 90]  # Поддержка всех ориентаций
            )
        else:
            # Для остальных языков
            result = reader.readtext(
                temp_path,
                detail=0,              
                paragraph=False,       
                contrast_ths=0.15,      
                adjust_contrast=0.5,    
                width_ths=0.5,          
                height_ths=0.5,         
                rotation_info=[0]       # Только горизонтальный текст
            )
        
        return " ".join(result) if result else ""
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def ocr_with_tesseract(image_path, block_id=None, lang='eng'):
    """
    OCR с Tesseract и унифицированной предобработкой
    
    Args:
        image_path: Путь к изображению
        block_id: ID блока для отладки
        lang: Код языка
        
    Returns:
        str: Распознанный текст
    """
    try:
        # Преобразуем код языка в формат Tesseract
        tesseract_lang = TESSERACT_LANG_CODES.get(lang, 'eng')
        
        # Загружаем изображение с помощью OpenCV
        image = cv2.imread(image_path)
        if image is None:
            print(f"Ошибка чтения изображения {image_path}")
            return ""
        
        # Предобработка с единой функцией
        processed = preprocess_image(image, language=lang, ocr_engine='tesseract', block_id=block_id)
        
        # Настройки Tesseract для разных языков
        config = get_tesseract_config(lang)
        
        # Сохраняем обработанное изображение во временный файл
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
            temp_path = temp.name
            cv2.imwrite(temp_path, processed)
            
        try:
            # Распознаем текст с помощью Tesseract
            text = pytesseract.image_to_string(
                temp_path, 
                lang=tesseract_lang,
                config=config
            )
            
            # Очищаем результат от лишних пробелов и переносов строк
            text = ' '.join(text.strip().split())
            return text
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        print(f"Ошибка при распознавании текста с Tesseract: {e}")
        return ""