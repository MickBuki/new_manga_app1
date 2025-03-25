"""
Маршруты для аутентификации и регистрации
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from backend.models.user_store import UserStore
from backend.auth import generate_token, get_current_user
from backend.logger import get_app_logger
from . import auth_bp

logger = get_app_logger()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    # Если пользователь уже авторизован, перенаправляем на главную
    if get_current_user():
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Заполните все поля', 'error')
            return render_template('auth/login.html')
        
        user_store = UserStore()
        success, result = user_store.authenticate_user(username, password)
        
        if not success:
            flash(result, 'error')
            return render_template('auth/login.html')
        
        # Запоминаем пользователя в сессии
        session['user_id'] = result.id
        flash(f'Добро пожаловать, {result.username}!', 'success')
        
        # Перенаправляем на главную
        return redirect(url_for('main.index'))
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    # Если пользователь уже авторизован, перенаправляем на главную
    if get_current_user():
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if not username or not email or not password:
            flash('Заполните все обязательные поля', 'error')
            return render_template('auth/register.html')
        
        if password != password_confirm:
            flash('Пароли не совпадают', 'error')
            return render_template('auth/register.html')
        
        if len(username) < 3:
            flash('Имя пользователя должно содержать минимум 3 символа', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
            return render_template('auth/register.html')
        
        user_store = UserStore()
        success, result = user_store.register_user(username, email, password)
        
        if not success:
            flash(result, 'error')
            return render_template('auth/register.html')
        
        # Запоминаем пользователя в сессии
        session['user_id'] = result.id
        flash('Регистрация успешна! Добро пожаловать!', 'success')
        
        # Перенаправляем на главную
        return redirect(url_for('main.index'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Выход из аккаунта"""
    session.pop('user_id', None)
    flash('Вы успешно вышли из аккаунта', 'success')
    return redirect(url_for('auth.login'))

# Добавим API-маршруты для аутентификации

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API для входа"""
    try:
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Заполните все поля'}), 400
        
        user_store = UserStore()
        success, result = user_store.authenticate_user(username, password)
        
        if not success:
            return jsonify({'success': False, 'error': result}), 401
        
        # Генерируем токен
        token = generate_token(result.id)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': result.id,
                'username': result.username,
                'email': result.email
            }
        })
    except Exception as e:
        logger.error(f"Ошибка API входа: {str(e)}")
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500

@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    """API для регистрации"""
    try:
        data = request.get_json()
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'Заполните все обязательные поля'}), 400
        
        if len(username) < 3:
            return jsonify({'success': False, 'error': 'Имя пользователя должно содержать минимум 3 символа'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Пароль должен содержать минимум 6 символов'}), 400
        
        user_store = UserStore()
        success, result = user_store.register_user(username, email, password)
        
        if not success:
            return jsonify({'success': False, 'error': result}), 400
        
        # Генерируем токен
        token = generate_token(result.id)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': result.id,
                'username': result.username,
                'email': result.email
            }
        })
    except Exception as e:
        logger.error(f"Ошибка API регистрации: {str(e)}")
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500