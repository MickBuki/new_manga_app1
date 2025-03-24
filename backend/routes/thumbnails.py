from . import thumbnails_bp
from flask import redirect, url_for
import os
from PIL import Image

@thumbnails_bp.route('/static/thumbnails/<folder>/<filename>')
def serve_thumbnail(folder, filename):
    """
    Обслуживание миниатюр изображений
    """
    # Путь к оригинальному изображению
    image_path = os.path.join('books', folder, filename)
    
    # Путь к миниатюре
    thumbnail_dir = os.path.join('static', 'thumbnails', folder)
    thumbnail_path = os.path.join(thumbnail_dir, filename)
    
    # Создаем миниатюру, если она не существует
    if not os.path.exists(thumbnail_path):
        create_thumbnail_for_image(image_path, thumbnail_path)
    
    return redirect(url_for('static', filename=f'thumbnails/{folder}/{filename}'))

def create_thumbnail_for_image(image_path, thumbnail_path, size=(150, 150)):
    """
    Создание миниатюры для изображения
    """
    # Создаем директорию для миниатюры, если она не существует
    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
    
    # Создаем миниатюру
    try:
        img = Image.open(image_path)
        img.thumbnail(size)
        img.save(thumbnail_path)
    except Exception as e:
        print(f"Ошибка при создании миниатюры для {image_path}: {e}")