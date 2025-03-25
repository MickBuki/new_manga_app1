"""
Хранилище пользователей
"""
import os
import json
import datetime
from backend.models.user import User
from backend.config import get_settings
from backend.logger import get_app_logger

class UserStore:
    """Класс для управления пользователями"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserStore, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.logger = get_app_logger()
        self.settings = get_settings()
        
        # Создаем директорию для хранения данных пользователей
        self.users_dir = os.path.join(self.settings.data_dir, "users")
        os.makedirs(self.users_dir, exist_ok=True)
        
        # Загружаем данные пользователей
        self.users = {}
        self._load_users()
        
        self._initialized = True
    
    def _load_users(self):
        """Загрузка пользователей из файлов"""
        try:
            users_file = os.path.join(self.users_dir, "users.json")
            if os.path.exists(users_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    
                for user_data in users_data:
                    user = User(
                        id=user_data.get('id'),
                        username=user_data.get('username'),
                        email=user_data.get('email'),
                        password_hash=user_data.get('password_hash'),
                        created_at=datetime.datetime.fromisoformat(user_data.get('created_at')),
                        last_login=datetime.datetime.fromisoformat(user_data.get('last_login')) if user_data.get('last_login') else None
                    )
                    self.users[user.id] = user
                    
                self.logger.info(f"Загружено {len(self.users)} пользователей")
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке пользователей: {str(e)}")
    
    def _save_users(self):
        """Сохранение пользователей в файл"""
        try:
            users_data = []
            for user in self.users.values():
                user_dict = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'password_hash': user.password_hash,
                    'created_at': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
                users_data.append(user_dict)
                
            users_file = os.path.join(self.users_dir, "users.json")
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Сохранено {len(self.users)} пользователей")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении пользователей: {str(e)}")
    
    def register_user(self, username, email, password):
        """
        Регистрация нового пользователя
        
        Returns:
            tuple: (успех, пользователь или сообщение об ошибке)
        """
        # Проверяем, есть ли пользователь с таким email или username
        for user in self.users.values():
            if user.email == email:
                return False, "Пользователь с таким email уже существует"
            if user.username == username:
                return False, "Пользователь с таким именем уже существует"
        
        # Создаем нового пользователя
        user = User(username=username, email=email)
        user.set_password(password)
        
        # Сохраняем пользователя
        self.users[user.id] = user
        self._save_users()
        
        # Создаем директории для пользователя
        self._create_user_directories(user.id)
        
        return True, user
    
    def authenticate_user(self, username, password):
        """
        Аутентификация пользователя
        
        Returns:
            tuple: (успех, пользователь или сообщение об ошибке)
        """
        for user in self.users.values():
            if user.username == username:
                if user.check_password(password):
                    user.last_login = datetime.datetime.now()
                    self._save_users()
                    return True, user
                return False, "Неверный пароль"
        
        return False, "Пользователь не найден"
    
    def get_user_by_id(self, user_id):
        """Получение пользователя по ID"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username):
        """Получение пользователя по имени"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def _create_user_directories(self, user_id):
        """Создание директорий пользователя"""
        # Основная директория пользователя
        user_dir = os.path.join(self.users_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Директории для файлов
        books_dir = os.path.join(user_dir, "books")
        translated_dir = os.path.join(user_dir, "translated")
        temp_dir = os.path.join(user_dir, "temp")
        editor_dir = os.path.join(user_dir, "editor")
        
        os.makedirs(books_dir, exist_ok=True)
        os.makedirs(translated_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(editor_dir, exist_ok=True)
        
        return user_dir