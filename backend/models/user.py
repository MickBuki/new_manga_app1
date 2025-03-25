"""
Модель пользователя для системы аутентификации
"""
import os
import uuid
import hashlib
import datetime
from dataclasses import dataclass, field

@dataclass
class User:
    """Класс пользователя системы"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    password_hash: str = ""
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_login: datetime.datetime = None
    
    def set_password(self, password):
        """Установка хэша пароля"""
        salt = os.urandom(32)
        self.password_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt, 
            100000
        ).hex() + ':' + salt.hex()
    
    def check_password(self, password):
        """Проверка пароля"""
        if not self.password_hash:
            return False
            
        stored_hash, salt_hex = self.password_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt, 
            100000
        ).hex()
        
        return stored_hash == computed_hash