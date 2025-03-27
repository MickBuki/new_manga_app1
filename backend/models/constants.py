# Константы для OCR и языковых моделей

# Пути к моделям
BUBBLE_MODEL_PATH = 'data/cut_thebuble/run1/weights/best.pt'  # Модель пузырей
TEXT_MODEL_PATH = 'data/merged_text_model/run1/weights/best.pt'  # Модель текста

# Параметры моделей
BUBBLE_CONF = 0.7    # Порог уверенности для пузырей
TEXT_CONF = 0.5      # Порог уверенности для текста

# Коды языков для Google Translate
GOOGLE_LANG_CODES = {
    'ja': 'ja',      # Японский
    'zh': 'zh-CN',   # Китайский (упрощенный)
    'ko': 'ko',      # Корейский
    'en': 'en',      # Английский
    'ru': 'ru',      # Русский
    'fr': 'fr',      # Французский
    'es': 'es',      # Испанский
    'de': 'de',      # Немецкий
}

# Имена языков для OpenAI
OPENAI_LANG_NAMES = {
    'ja': 'Japanese, 日本語',
    'zh': 'Simplified Chinese, 简体中文',
    'ko': 'Korean, 한국어',
    'en': 'English',
    'ru': 'Russian',
    'fr': 'French',
    'es': 'Spanish',
    'de': 'German',
}

# Коды языков для PaddleOCR
PADDLE_OCR_LANGS = {
    'ja': 'japan',
    'zh': 'ch',
    'ko': 'korean',
    'en': 'en',
    'fr': 'fr',
    'es': 'es',
    'de': 'german',
}

# Коды языков для Tesseract
TESSERACT_LANG_CODES = {
    'en': 'eng',      # Английский
    'fr': 'fra',      # Французский
    'es': 'spa',      # Испанский
    'de': 'deu',      # Немецкий
    'ru': 'rus',      # Русский
    'it': 'ita',      # Итальянский
    'pt': 'por',      # Португальский
    'zh': 'chi_sim',  # Китайский упрощенный
    'ja': 'jpn',      # Японский 
    'ko': 'kor'       # Корейский
}

# Оптимальные OCR-движки для разных языков
OPTIMAL_OCR_ENGINES = {
    'ja': 'mangaocr',    # Японский -> MangaOCR (специализированный для манги)
    'zh': 'paddleocr',   # Китайский -> PaddleOCR
    'ko': 'paddleocr',   # Корейский -> PaddleOCR
    'en': 'paddleocr',   # Английский -> tesseract
    'ru': 'easyocr',     # Русский -> EasyOCR
    'fr': 'tesseract',   # Французский -> Tesseract
    'es': 'tesseract',   # Испанский -> Tesseract
    'de': 'tesseract',   # Немецкий -> Tesseract
}