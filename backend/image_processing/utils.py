"""
Вспомогательные функции для работы с изображениями
"""
import base64
import io
import cv2
import numpy as np
from PIL import Image as PILImage

def image_to_base64(img):
    """
    Преобразует PIL Image или numpy массив в строку base64
    
    Args:
        img: PIL Image или numpy массив
        
    Returns:
        str: Строка base64
    """
    if isinstance(img, PILImage.Image):
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    elif isinstance(img, np.ndarray):
        _, buffer = cv2.imencode(".png", img)
        return base64.b64encode(buffer).decode('utf-8')
    return ""

def save_debug_image(image, file_path):
    """
    Сохраняет отладочное изображение
    
    Args:
        image: Изображение (numpy array)
        file_path: Путь для сохранения
    """
    try:
        cv2.imwrite(file_path, image)
    except Exception as e:
        print(f"Ошибка при сохранении отладочного изображения {file_path}: {e}")

def load_image_as_array(image_path):
    """
    Загружает изображение в виде numpy массива
    
    Args:
        image_path: Путь к изображению
        
    Returns:
        numpy.ndarray: Изображение в виде массива
    """
    return cv2.imread(image_path)

def load_image_as_pil(image_path):
    """
    Загружает изображение в виде PIL Image
    
    Args:
        image_path: Путь к изображению
        
    Returns:
        PIL.Image: Изображение
    """
    return PILImage.open(image_path)

def decode_base64_image(base64_string):
    """
    Преобразует строку base64 в PIL Image
    
    Args:
        base64_string: Строка base64
        
    Returns:
        PIL.Image: Изображение
    """
    image_data = base64.b64decode(base64_string)
    return PILImage.open(io.BytesIO(image_data))