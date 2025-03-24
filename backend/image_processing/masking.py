"""
Функции для работы с масками изображений
"""
import numpy as np
import cv2
from PIL import Image as PILImage

def create_bubble_mask(image_shape, bubble_boxes):
    """
    Создает маску для пузырей
    
    Args:
        image_shape: Размеры изображения (высота, ширина)
        bubble_boxes: Список прямоугольников пузырей [(x1, y1, x2, y2), ...]
        
    Returns:
        numpy.ndarray: Маска пузырей
    """
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    
    for x1, y1, x2, y2 in bubble_boxes:
        mask[y1:y2, x1:x2] = 255
    
    return mask

def create_text_background_mask(image_shape, text_background_boxes):
    """
    Создает маску для текстовых блоков без пузырей
    
    Args:
        image_shape: Размеры изображения (высота, ширина)
        text_background_boxes: Список прямоугольников текстовых блоков [(x1, y1, x2, y2), ...]
        
    Returns:
        numpy.ndarray: Маска текстовых блоков без пузырей
    """
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    
    for x1, y1, x2, y2 in text_background_boxes:
        mask[y1:y2, x1:x2] = 255
    
    return mask

def extract_masks_from_rgba(rgba_image):
    """
    Извлекает маски пузырей и текстовых блоков из RGBA изображения
    
    Args:
        rgba_image: RGBA изображение (PIL.Image)
        
    Returns:
        tuple: (маска пузырей, маска текстовых блоков)
    """
    if rgba_image.mode != 'RGBA':
        raise ValueError("Изображение должно быть в формате RGBA")
    
    # Извлекаем каналы из изображения
    r, g, b, a = rgba_image.split()
    
    # Создаем маски на основе цветовых каналов
    bubble_mask = np.array(r) == 255  # Синий канал для пузырей
    text_background_mask = np.array(b) == 255  # Красный канал для текстовых блоков
    
    # Преобразуем булевы маски в uint8
    bubble_mask = (bubble_mask * 255).astype(np.uint8)
    text_background_mask = (text_background_mask * 255).astype(np.uint8)
    
    return bubble_mask, text_background_mask

def create_rgba_mask_image(image_shape, bubble_mask, text_background_mask):
    """
    Создает RGBA изображение с масками для визуализации
    
    Args:
        image_shape: Размеры изображения (высота, ширина)
        bubble_mask: Маска пузырей
        text_background_mask: Маска текстовых блоков
        
    Returns:
        PIL.Image: RGBA изображение с масками
    """
    # Создаем RGBA изображение
    sickzil_img = np.zeros((image_shape[0], image_shape[1], 4), dtype=np.uint8)
    
    # Заполняем маски разными цветами
    sickzil_img[bubble_mask > 0] = [255, 0, 0, 255]  # Синий для пузырей
    sickzil_img[text_background_mask > 0] = [0, 0, 255, 255]  # Красный для текстовых блоков
    
    return PILImage.fromarray(sickzil_img, 'RGBA')

def create_white_filled_image(image, bubble_mask, text_background_mask):
    """
    Создает изображение с белыми областями для пузырей и текстовых блоков
    
    Args:
        image: Исходное изображение (numpy.ndarray)
        bubble_mask: Маска пузырей
        text_background_mask: Маска текстовых блоков
        
    Returns:
        numpy.ndarray: Изображение с белыми областями
    """
    # Создаем копию исходного изображения
    result = image.copy()
    
    # Заполняем маски белым цветом
    result[bubble_mask > 0] = [255, 255, 255]
    result[text_background_mask > 0] = [255, 255, 255]
    
    return result