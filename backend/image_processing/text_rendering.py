"""
Функции для рендеринга текста на изображениях
"""
import os
import re
import cv2
import numpy as np
from PIL import Image as PILImage, ImageDraw, ImageFont

def get_font(size=16):
    """
    Загружает подходящий шрифт заданного размера
    
    Args:
        size: Размер шрифта
        
    Returns:
        PIL.ImageFont: Шрифт
    """
    font_paths = [
        "data/fonts/anime-ace-v02.ttf", 
        "arial.ttf", 
        "C:/Windows/Fonts/Arial.ttf", 
        "C:/Windows/Fonts/Calibri.ttf"
    ]
    
    for path in font_paths:
        try:
            font = ImageFont.truetype(path, size)
            print(f"Используется шрифт: {path}")
            return font
        except Exception:
            continue
    
    print("Используется шрифт по умолчанию")
    return ImageFont.load_default()

def draw_wrapped_text(draw, font, text, box, outline_strength=1):
    """
    Рисует текст с переносами и обводкой в указанном прямоугольнике
    
    Args:
        draw: Объект PIL.ImageDraw
        font: Объект PIL.ImageFont
        text: Текст для отрисовки
        box: Границы прямоугольника (x_min, y_min, x_max, y_max)
        outline_strength: Сила обводки (1 - обычная, 2 - усиленная)
    """
    x_min, y_min, x_max, y_max = box
    max_width = x_max - x_min - 15
    
    # Получаем размеры шрифта
    left, top, right, bottom = draw.textbbox((0, 0), 'А', font=font)
    char_width = right - left
    char_height = bottom - top
    
    line_spacing = 6

    # Разбиваем текст на предложения по точкам
    sentences = re.split(r'([.!?]\s+)', text)
    # Объединяем предложения с их знаками препинания
    sentence_chunks = []
    for i in range(0, len(sentences)-1, 2):
        if i+1 < len(sentences):
            sentence_chunks.append(sentences[i] + sentences[i+1])
        else:
            sentence_chunks.append(sentences[i])
    if len(sentences) % 2 == 1:
        sentence_chunks.append(sentences[-1])
    
    # Теперь обрабатываем каждое предложение
    wrapped_text = []
    
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
    
    # Рисуем текст с переносом строк и настраиваемой обводкой
    if wrapped_text:
        text_height_total = len(wrapped_text) * (char_height + line_spacing)
        y_start = y_min + ((y_max - y_min - text_height_total) / 2)
        
        for i, line in enumerate(wrapped_text):
            left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
            text_width = right - left
            x_pos = x_min + ((x_max - x_min - text_width) / 2)
            y_pos = y_start + (i * (char_height + line_spacing))
            
            # Настраиваемая обводка в зависимости от outline_strength
            outline_pixels = []
            
            if outline_strength == 1:
                # Стандартная обводка (8 направлений)
                for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                    outline_pixels.append((dx, dy))
            else:
                # Усиленная обводка (16 направлений, включая точки на расстоянии 2 пикселя)
                for dx in [-2, -1, 0, 1, 2]:
                    for dy in [-2, -1, 0, 1, 2]:
                        if dx == 0 and dy == 0:
                            continue
                        if abs(dx) == 2 and abs(dy) == 2:
                            continue  # Пропускаем диагональные точки на расстоянии 2
                        outline_pixels.append((dx, dy))
            
            # Рисуем обводку
            for dx, dy in outline_pixels:
                draw.text((x_pos + dx, y_pos + dy), line, fill="white", font=font)
                
            # Основной текст черным
            draw.text((x_pos, y_pos), line, fill="black", font=font)

def create_translated_image(image_path, text_blocks, output_path, bubble_mask, text_background_mask=None):
    """
    Создает переведенное изображение с учетом масок пузырей и текстовых блоков
    
    Args:
        image_path: Путь к исходному изображению
        text_blocks: Список блоков текста с координатами и переводом
        output_path: Путь для сохранения результата
        bubble_mask: Маска пузырей
        text_background_mask: Маска текстовых блоков (опционально)
        
    Returns:
        str: Путь к созданному изображению
    """
    print("Создание изображения с переводом...")
    img = PILImage.open(image_path)
    img_np = np.array(img)
    img_h, img_w = img_np.shape[:2]
    
    translated_np = img_np.copy()
    
    # Проверяем размеры масок
    if bubble_mask.shape[:2] != (img_h, img_w):
        raise ValueError(f"Размеры маски пузырей {bubble_mask.shape[:2]} не совпадают с размерами изображения {(img_h, img_w)}")
    
    # Создаем бинарные маски
    bubble_binary = (bubble_mask > 0).astype(np.uint8)
    
    # Закрашиваем пузыри белым
    if len(translated_np.shape) == 3 and translated_np.shape[2] >= 3:
        translated_np[bubble_binary > 0, 0] = 255
        translated_np[bubble_binary > 0, 1] = 255
        translated_np[bubble_binary > 0, 2] = 255
    else:
        translated_np[bubble_binary > 0] = 255
    
    # Добавляем обработку текстовых блоков, если передана маска
    if text_background_mask is not None:
        if text_background_mask.shape[:2] != (img_h, img_w):
            raise ValueError(f"Размеры маски текстовых блоков {text_background_mask.shape[:2]} не совпадают с размерами изображения {(img_h, img_w)}")
        
        # УЛУЧШЕНИЕ 1: Усиление маски текста для улучшенного покрытия символов
        # Расширяем маску с помощью морфологических операций для захвата полутонов и деталей
        kernel = np.ones((2, 2), np.uint8)
        enhanced_mask = cv2.dilate(text_background_mask, kernel, iterations=1)
        
        # УЛУЧШЕНИЕ 2: Определяем тип фона для выбора оптимальной стратегии
        is_dark_background = False
        
        # Проверяем, является ли изображение черно-белым
        is_grayscale = False
        if len(img_np.shape) == 2 or (len(img_np.shape) == 3 and np.allclose(img_np[:,:,0], img_np[:,:,1], atol=10) and np.allclose(img_np[:,:,1], img_np[:,:,2], atol=10)):
            is_grayscale = True
            
            # Если это черно-белое изображение, проверяем яркость фона
            if len(img_np.shape) == 3:
                gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_np
                
            # Создаем маску для анализа фона вокруг текста
            dilated = cv2.dilate(enhanced_mask, np.ones((5, 5), np.uint8), iterations=1)
            background_region = dilated > 0
            
            # Если маска не пустая, анализируем цвет фона
            if np.sum(background_region) > 0:
                bg_brightness = np.mean(gray[background_region])
                # Если фон темный, отмечаем это
                if bg_brightness < 60:
                    is_dark_background = True
                    print(f"Обнаружен темный фон (яркость: {bg_brightness:.1f}), используем специальную обработку")
        
        # УЛУЧШЕНИЕ 3: Применяем разные стратегии в зависимости от типа фона
        if is_dark_background:
            # Для темного фона (как на вашем изображении) используем прямую заливку
            # с небольшим размытием для естественности
            binary_mask = (enhanced_mask > 0).astype(np.uint8)
            
            # Размываем маску на границах для плавного перехода
            blurred_mask = cv2.GaussianBlur(binary_mask.astype(np.float32), (5, 5), 0)
            
            # Применяем маску, сохраняя оригинальную темноту фона
            if len(translated_np.shape) == 3:
                for c in range(3):
                    translated_np[:,:,c] = translated_np[:,:,c] * (1 - blurred_mask) + 5 * blurred_mask
            else:
                translated_np = translated_np * (1 - blurred_mask) + 5 * blurred_mask
        else:
            # Для других типов фона используем inpainting
            text_mask = (enhanced_mask > 0).astype(np.uint8) * 255
            
            try:
                # Пробуем использовать inpainting
                inpainted_img = cv2.inpaint(translated_np, text_mask, inpaintRadius=7, flags=cv2.INPAINT_NS)
                translated_np = inpainted_img
            except Exception as e:
                print(f"Ошибка при использовании cv2.inpaint: {e}")
                # Если inpainting не работает, используем средний цвет области
                if len(translated_np.shape) == 3:
                    for c in range(3):
                        # Находим средний цвет окружающей области и заполняем им текст
                        bg_color = np.median(translated_np[:,:,c][enhanced_mask == 0])
                        translated_np[:,:,c][enhanced_mask > 0] = bg_color
                else:
                    bg_color = np.median(translated_np[enhanced_mask == 0])
                    translated_np[enhanced_mask > 0] = bg_color
    
    # Преобразуем в PIL изображение для дальнейшей обработки
    translated_img = PILImage.fromarray(translated_np)
    draw = ImageDraw.Draw(translated_img)
    
    # Загружаем шрифт
    try:
        font = get_font(16)
    except Exception:
        font = ImageFont.load_default()
        print("Используется шрифт по умолчанию (после ошибки)")
    
    # УЛУЧШЕНИЕ 4: Определяем, нужна ли усиленная обводка для текста
    outline_strength = 1  # Стандартная обводка
    if 'is_dark_background' in locals() and is_dark_background:
        outline_strength = 2  # Усиленная обводка для темного фона
    
    # Обрабатываем каждый текстовый блок
    for block in text_blocks:
        if not block['translated_text']:
            continue
            
        x_min, y_min, x_max, y_max = block['box']
        text = block['translated_text'].strip()
        
        # Проверяем корректность координат
        if y_min < 0 or y_max > img_h or x_min < 0 or x_max > img_w:
            # Корректируем координаты
            x_min = max(0, min(x_min, img_w-1))
            y_min = max(0, min(y_min, img_h-1))
            x_max = max(0, min(x_max, img_w-1))
            y_max = max(0, min(y_max, img_h-1))
        
        # Используем модифицированную функцию для рисования текста с обводкой
        draw_wrapped_text(draw, font, text, (x_min, y_min, x_max, y_max), outline_strength)
    
    # Сохраняем результат
    translated_img.save(output_path)
    print(f"Изображение с переводом сохранено как {output_path}")
    return output_path