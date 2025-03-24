"""
Модуль для обработки изображений манги и рендеринга текста
"""

from .utils import image_to_base64, save_debug_image
from .text_rendering import draw_wrapped_text, create_translated_image
from .masking import create_bubble_mask, create_text_background_mask