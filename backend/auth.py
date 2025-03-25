"""
Функции для проверки аутентификации
"""
import jwt
import datetime
from functools import wraps
from flask import request, redirect, url_for, session
from backend.config import get_settings
from backend.models.user_store import UserStore
from backend.logger import get_app_logger

settings = get_settings()
logger = get_app_logger()

def generate_token(user_id):
    """Генерация JWT токена для пользователя"""
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.jwt_token_expires)
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm='HS256')

def validate_token(token):
    """Проверка JWT токена"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=['HS256'])
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, "Токен истек"
    except jwt.InvalidTokenError:
        return False, "Неверный токен"

def get_current_user():
    """
    Получение текущего пользователя из сессии
    
    Returns:
        User или None
    """
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    user_store = UserStore()
    return user_store.get_user_by_id(user_id)

def login_required(f):
    """Декоратор для проверки авторизации в веб-интерфейсе"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        
        if not user:
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def api_login_required(f):
    """Декоратор для проверки авторизации в API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return {'success': False, 'error': 'Требуется авторизация'}, 401
        
        token = auth_header.split(' ')[1]
        success, result = validate_token(token)
        
        if not success:
            return {'success': False, 'error': result}, 401
        
        user_id = result.get('user_id')
        user_store = UserStore()
        user = user_store.get_user_by_id(user_id)
        
        if not user:
            return {'success': False, 'error': 'Пользователь не найден'}, 404
        
        # Добавляем пользователя в kwargs
        kwargs['current_user'] = user
        return f(*args, **kwargs)
    
    return decorated_function