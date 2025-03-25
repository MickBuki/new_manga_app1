"""
Функции для сегментации изображений и обнаружения текстовых блоков
"""
import os
import cv2
import time
import json
import base64
import io
import uuid
import numpy as np
from PIL import Image as PILImage

from backend.config import get_settings
from backend.logger import get_app_logger
from backend.models import get_bubble_model, get_text_model
from backend.file_utils.temp import get_temp_filepath

def process_segmentation(image_path, output_path=None):
    """
    Обработка изображения с использованием двух моделей YOLO
    с разделением на пузыри и текстовые блоки на фоне
    
    Args:
        image_path: Путь к изображению
        output_path: Путь для сохранения результатов
        
    Returns:
        tuple: (результаты сегментации, маска пузырей, маска текстовых блоков)
    """
    if output_path is None:
        output_filename = generate_unique_filename('segmentation_results', '.json')
        output_path = get_temp_filepath(output_filename)
    
    settings = get_settings()
    logger = get_app_logger()
    start_time = time.time()
    temp_files = []  # Список для хранения путей временных файлов
    
    try:
        # 1. Загружаем модели
        logger.info(f"Загрузка моделей для сегментации {image_path}")
        bubble_model = get_bubble_model(settings.use_gpu)
        text_model = get_text_model(settings.use_gpu)
        
        # 2. Загружаем изображение
        img = cv2.imread(image_path)
        if img is None:
            error_msg = f"Не удалось загрузить изображение: {image_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        img_h, img_w = img.shape[:2]
        logger.debug(f"Размер изображения: {img_w}x{img_h}")
        
        # 3. Создаем копии для визуализации
        result_img = img.copy()
        bubbles_img = img.copy()
        
        # 4. Конвертируем оригинал в base64
        _, buffer = cv2.imencode(".png", img)
        original_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # 5. Находим пузыри и текстовые блоки
        logger.info("Обнаружение пузырей и текстовых блоков...")
        bubble_results = bubble_model(image_path, conf=settings.bubble_conf)
        
        # 6. Извлекаем координаты пузырей и текстовых блоков
        bubble_boxes = []
        text_background_boxes = []
        
        for r in bubble_results:
            for i, box in enumerate(r.boxes.xyxy):
                x1, y1, x2, y2 = map(int, box)
                confidence = float(r.boxes.conf[i])
                class_id = int(r.boxes.cls[i])
                class_name = bubble_model.names[class_id]
                
                if class_name == 'bubble':
                    bubble_boxes.append({
                        'coordinates': (x1, y1, x2, y2),
                        'confidence': confidence,
                        'type': 'bubble'
                    })
                    # Рисуем синий прямоугольник для пузырей
                    cv2.rectangle(bubbles_img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(bubbles_img, f"Bubble {confidence:.2f}", (x1, y1-5), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                elif class_name == 'text':
                    text_background_boxes.append({
                        'coordinates': (x1, y1, x2, y2),
                        'confidence': confidence,
                        'type': 'text_background'
                    })
                    # Рисуем зеленый прямоугольник для текстовых блоков
                    cv2.rectangle(bubbles_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(bubbles_img, f"Text {confidence:.2f}", (x1, y1-5), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Сортируем пузыри
        logger.info(f"Найдено {len(bubble_boxes)} пузырей и {len(text_background_boxes)} текстовых блоков")
        
        # 7. Создаем маски для текста
        combined_bubble_mask = np.zeros((img_h, img_w), dtype=np.uint8)
        combined_text_background_mask = np.zeros((img_h, img_w), dtype=np.uint8)
        text_boxes = []
        
        # 8. Обрабатываем каждый пузырь и текстовый блок
        logger.info(f"Обработка {len(bubble_boxes) + len(text_background_boxes)} областей...")
        all_boxes = bubble_boxes + text_background_boxes
        
        for box_info in all_boxes:
            x1, y1, x2, y2 = box_info['coordinates']
            box_type = box_info['type']
            
            # Вырезаем область
            box_img = img[y1:y2, x1:x2]
            if box_img.size == 0:
                continue
            
            # Используем временный файл с уникальным именем для избежания конфликтов
            temp_path = f"temp_box_{uuid.uuid4().hex}.png"
            
            # Проверяем, что изображение непустое
            if box_img.size > 0:
                # Сохраняем изображение
                success = cv2.imwrite(temp_path, box_img)
                if not success:
                    logger.warning(f"Ошибка при сохранении изображения {temp_path}")
                    continue
                    
                # Проверяем, что файл существует и имеет размер
                if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                    logger.warning(f"Ошибка: файл {temp_path} не создан или имеет нулевой размер")
                    continue
                    
                temp_files.append(temp_path)  # Добавляем в список временных файлов
                
                try:
                    # Обнаруживаем текст
                    text_in_box = text_model(temp_path, conf=settings.text_conf)
                    
                    # Получаем координаты текста
                    for r in text_in_box:
                        for j, text_box in enumerate(r.boxes.xyxy):
                            tx1, ty1, tx2, ty2 = map(int, text_box)
                            confidence = float(r.boxes.conf[j])
                            
                            # Пересчитываем координаты относительно исходного изображения
                            global_tx1 = x1 + tx1
                            global_ty1 = y1 + ty1
                            global_tx2 = x1 + tx2
                            global_ty2 = y1 + ty2
                            
                            # Проверяем границы
                            global_tx1 = max(0, min(global_tx1, img_w-1))
                            global_ty1 = max(0, min(global_ty1, img_h-1))
                            global_tx2 = max(0, min(global_tx2, img_w-1))
                            global_ty2 = max(0, min(global_ty2, img_h-1))
                            
                            # Добавляем в список боксов
                            text_boxes.append((global_tx1, global_ty1, global_tx2, global_ty2))
                            
                            # Заполняем маску в зависимости от типа блока
                            if box_type == 'bubble':
                                combined_bubble_mask[global_ty1:global_ty2, global_tx1:global_tx2] = 255
                            else:  # text_background
                                combined_text_background_mask[global_ty1:global_ty2, global_tx1:global_tx2] = 255
                            
                            # Рисуем бокс
                            cv2.rectangle(result_img, (global_tx1, global_ty1), (global_tx2, global_ty2), (0, 255, 0), 2)
                            cv2.putText(result_img, f"{confidence:.2f}", (global_tx1, global_ty1-5), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                except Exception as e:
                    logger.error(f"Ошибка при обработке области: {e}")
            else:
                logger.warning("Пропуск области: пустое изображение")
        
        # 9. Расширяем маски
        dilated_bubble_mask = cv2.dilate(combined_bubble_mask, np.ones((1, 1), np.uint8), iterations=1)
        dilated_text_background_mask = cv2.dilate(combined_text_background_mask, np.ones((1, 1), np.uint8), iterations=1)

        # 10. Удаляем текст с разным цветом закрашивания
        text_removed = img.copy()

        # Закрашиваем пузыри белым
        text_removed[dilated_bubble_mask > 0] = [255, 255, 255]

        # Закрашиваем текстовые блоки белым, используя побитовое сравнение
        text_removed[dilated_text_background_mask > 0] = [255, 255, 255]

        
        # 11. Создаем маску для SickZil
        sickzil_img = np.zeros((img_h, img_w, 4), dtype=np.uint8)
        sickzil_img[dilated_bubble_mask > 0] = [255, 0, 0, 255]  # Синий для пузырей
        sickzil_img[dilated_text_background_mask > 0] = [0, 0, 255, 255]  # Красный для текстовых блоков
        sickzil_pil = PILImage.fromarray(sickzil_img, 'RGBA')
        
        # 12. Результаты в base64
        _, bubbles_buffer = cv2.imencode(".png", bubbles_img)
        bubbles_base64 = base64.b64encode(bubbles_buffer).decode('utf-8')
        
        _, boxes_buffer = cv2.imencode(".png", result_img)
        boxes_base64 = base64.b64encode(boxes_buffer).decode('utf-8')
        
        _, mask_buffer = cv2.imencode(".png", dilated_bubble_mask)
        mask_base64 = base64.b64encode(mask_buffer).decode('utf-8')
        
        _, removed_buffer = cv2.imencode(".png", text_removed)
        text_removed_base64 = base64.b64encode(removed_buffer).decode('utf-8')
        
        buffered = io.BytesIO()
        sickzil_pil.save(buffered, format="PNG")
        final_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # 13. Формируем результат
        results = {
            'original': original_base64,
            'prediction': bubbles_base64,
            'boxes_image': boxes_base64,
            'overlay': boxes_base64,
            'final': final_base64,
            'text_removed': text_removed_base64,
            'text_boxes': [box['coordinates'] for box in bubble_boxes + text_background_boxes]
        }
        
        # 14. Сохраняем результаты
        with open(output_path, 'w') as f:
            json.dump(results, f)
        
        logger.info(f"Сегментация завершена за {time.time() - start_time:.2f} секунд")
        return results, dilated_bubble_mask, dilated_text_background_mask
        
    except Exception as e:
        logger.error(f"Ошибка в process_segmentation: {e}", exc_info=True)
        raise
    finally:
        # Удаляем все временные файлы только в блоке finally
        for temp_path in temp_files:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.debug(f"Удален временный файл: {temp_path}")
                except Exception as e:
                    logger.warning(f"Ошибка при удалении временного файла {temp_path}: {e}")