import torch
from ultralytics import YOLO
from backend.config import get_settings
from backend.logger import get_app_logger

# Кэшированные модели
__BUBBLE_MODEL = None
__TEXT_MODEL = None

def get_device(use_gpu=None):
    """Возвращает устройство для моделей в зависимости от настроек"""
    settings = get_settings()
    logger = get_app_logger()
    
    # Если параметр не передан, используем значение из конфигурации
    if use_gpu is None:
        use_gpu = settings.use_gpu
    
    if use_gpu and torch.cuda.is_available():
        logger.info("Используем GPU для моделей")
        return "cuda"
    else:
        if use_gpu and not torch.cuda.is_available():
            logger.warning("GPU запрошен, но CUDA недоступна. Используем CPU.")
        else:
            logger.info("Используем CPU для моделей")
        return "cpu"

def get_bubble_model(use_gpu=None):
    """
    Загружает модель обнаружения пузырей с текстом (lazy loading)
    
    Args:
        use_gpu: Использовать ли GPU для модели
        
    Returns:
        YOLO: Модель YOLO для обнаружения пузырей
    """
    global __BUBBLE_MODEL
    settings = get_settings()
    logger = get_app_logger()
    
    if __BUBBLE_MODEL is None:
        logger.info(f"Загрузка модели пузырей из {settings.bubble_model_path}")
        __BUBBLE_MODEL = YOLO(settings.bubble_model_path)
        # Установка устройства для модели
        device = get_device(use_gpu)
        __BUBBLE_MODEL.to(device)
    return __BUBBLE_MODEL

def get_text_model(use_gpu=None):
    """
    Загружает модель обнаружения текста (lazy loading)
    
    Args:
        use_gpu: Использовать ли GPU для модели
        
    Returns:
        YOLO: Модель YOLO для обнаружения текста
    """
    global __TEXT_MODEL
    settings = get_settings()
    logger = get_app_logger()
    
    if __TEXT_MODEL is None:
        logger.info(f"Загрузка модели текста из {settings.text_model_path}")
        __TEXT_MODEL = YOLO(settings.text_model_path)
        # Установка устройства для модели
        device = get_device(use_gpu)
        __TEXT_MODEL.to(device)
    return __TEXT_MODEL

def sort_text_bubbles(bubbles, row_threshold=30):
    """
    Сортирует текстовые пузыри сверху вниз и слева направо
    
    Args:
        bubbles: Список пузырей с координатами
        row_threshold: Порог для определения строки
        
    Returns:
        list: Отсортированный список пузырей
    """
    if not bubbles:
        return bubbles
    
    # Вычисляем центр каждого пузыря по оси Y
    bubbles_with_center_y = []
    for bubble in bubbles:
        x1, y1, x2, y2 = bubble
        center_y = (y1 + y2) // 2
        bubbles_with_center_y.append((bubble, center_y))
    
    # Сортируем все пузыри по центру Y
    bubbles_with_center_y.sort(key=lambda x: x[1])
    
    # Группируем пузыри в строки
    rows = []
    current_row = [bubbles_with_center_y[0]]
    
    for i in range(1, len(bubbles_with_center_y)):
        current_bubble, current_y = bubbles_with_center_y[i]
        prev_bubble, prev_y = bubbles_with_center_y[i-1]
        
        if abs(current_y - prev_y) <= row_threshold:
            current_row.append((current_bubble, current_y))
        else:
            rows.append(current_row)
            current_row = [(current_bubble, current_y)]
    
    if current_row:
        rows.append(current_row)
    
    # Сортируем каждую строку слева направо
    sorted_bubbles = []
    for row in rows:
        row.sort(key=lambda x: x[0][0])
        sorted_bubbles.extend([bubble for bubble, _ in row])
    
    return sorted_bubbles