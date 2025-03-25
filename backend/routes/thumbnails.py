from . import thumbnails_bp
from flask import redirect, url_for, send_from_directory, abort
import os
from PIL import Image
from backend.file_utils.user_files import get_user_directory
from backend.auth import login_required, get_current_user

@thumbnails_bp.route('/thumbnails/<user_id>/<folder>/<filename>')
@login_required
def serve_user_thumbnail(user_id, folder, filename):
    """
    Обслуживание миниатюр пользовательских изображений
    """
    current_user = get_current_user()
    
    # Проверяем, авторизован ли пользователь
    if not current_user:
        return abort(401)
    
    # Проверяем, имеет ли пользователь доступ к этим миниатюрам
    if current_user.id != user_id:
        return abort(403)
    
    # Путь к оригинальному изображению
    image_path = os.path.join(get_user_directory(user_id, "books"), folder, filename)
    
    # Путь к миниатюре
    thumbnail_dir = os.path.join(get_user_directory(user_id, "thumbnails"), folder)
    thumbnail_path = os.path.join(thumbnail_dir, filename)
    
    # Создаем миниатюру, если она не существует
    if not os.path.exists(thumbnail_path):
        create_thumbnail_for_image(image_path, thumbnail_path)
    
    return send_from_directory(os.path.dirname(thumbnail_path), os.path.basename(thumbnail_path))

@thumbnails_bp.route('/frontend/static/thumbnails/<folder>/<filename>')
def serve_thumbnail(folder, filename):
    """
    Обслуживание миниатюр изображений (для общих файлов)
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