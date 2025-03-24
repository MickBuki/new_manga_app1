"""
Модель настроек приложения
"""
import os
from dataclasses import dataclass

@dataclass
class LogSettings:
    """Настройки логирования"""
    log_level: str = "INFO"
    log_file: str = "manga_translator.log"
    console_log: bool = True
    max_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5

@dataclass
class AppSettings:
    """Настройки приложения"""
    # Общие настройки
    app_name: str = "Manga Translator"
    debug: bool = False
    use_gpu: bool = False
    
    # Пути к ресурсам
    books_dir: str = "data/books"
    translated_books_dir: str = "data/translated_books"
    static_dir: str = "frontend/static"
    thumbnails_dir: str = "frontend/static/thumbnails"
    temp_dir: str = "data/temp"
    editor_sessions_dir: str = "data/editor_sessions"
    
    # Пути к моделям
    bubble_model_path: str = "data/cut_thebuble/run1/weights/best.pt"
    text_model_path: str = "data/merged_text_model/run1/weights/best.pt"
    
    # Параметры моделей
    bubble_conf: float = 0.7
    text_conf: float = 0.5
    
    # Параметры переводчика
    translator_default_method: str = "google"  # "google" или "openai"
    openai_api_key: str = ""  # Ключ API OpenAI
    
    # Настройки логирования
    log_settings: LogSettings = None
    
    def load_from_env(self):
        """Загружает настройки из переменных окружения"""
        # Общие настройки
        self.app_name = os.environ.get('APP_NAME', self.app_name)
        self.debug = os.environ.get('DEBUG', '').lower() == 'true'
        self.use_gpu = os.environ.get('USE_GPU', '').lower() == 'true'
        
        # Пути
        self.books_dir = os.environ.get('BOOKS_DIR', self.books_dir)
        self.translated_books_dir = os.environ.get('TRANSLATED_BOOKS_DIR', self.translated_books_dir)
        self.static_dir = os.environ.get('STATIC_DIR', self.static_dir)
        self.thumbnails_dir = os.environ.get('THUMBNAILS_DIR', self.thumbnails_dir)
        self.temp_dir = os.environ.get('TEMP_DIR', self.temp_dir)
        self.editor_sessions_dir = os.environ.get('EDITOR_SESSIONS_DIR', self.editor_sessions_dir)
        
        # Пути к моделям
        self.bubble_model_path = os.environ.get('BUBBLE_MODEL_PATH', self.bubble_model_path)
        self.text_model_path = os.environ.get('TEXT_MODEL_PATH', self.text_model_path)
        
        # Параметры моделей
        self.bubble_conf = float(os.environ.get('BUBBLE_CONF', self.bubble_conf))
        self.text_conf = float(os.environ.get('TEXT_CONF', self.text_conf))
        
        # Параметры переводчика
        self.translator_default_method = os.environ.get('TRANSLATOR_METHOD', self.translator_default_method)
        self.openai_api_key = os.environ.get('OPENAI_API_KEY', self.openai_api_key)
        
        return self