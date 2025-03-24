"""
Модуль для перевода текста из манги
"""

from .google_translator import translate_with_google
from .openai_translator import translate_with_openai
from .batch import batch_translate_with_openai

def translate_text_blocks(text_blocks, translation_method='google', openai_api_key=None, src_lang='zh', dest_lang='ru'):
    """
    Переводит текстовые блоки с использованием выбранного метода перевода
    
    Args:
        text_blocks: Список блоков текста с ключами 'id', 'box', 'text'
        translation_method: Метод перевода ('google' или 'openai')
        openai_api_key: API ключ OpenAI (если используется translation_method='openai')
        src_lang: Язык оригинала (ja, zh, ko, en и т.д.)
        dest_lang: Язык перевода (ru, en, ja, zh и т.д.)
        
    Returns:
        tuple: (переведенные блоки, сообщение об ошибке или None если без ошибок)
    """
    # Импортируем словари кодов языков для разных сервисов
    from backend.models.constants import GOOGLE_LANG_CODES, OPENAI_LANG_NAMES
    
    print(f"Перевод {len(text_blocks)} текстовых блоков методом {translation_method} с {src_lang} на {dest_lang}...")
    
    # Преобразуем коды языков в нужные форматы для разных систем перевода
    google_src = GOOGLE_LANG_CODES.get(src_lang, 'auto')
    google_dest = GOOGLE_LANG_CODES.get(dest_lang, 'ru')
    
    openai_src = OPENAI_LANG_NAMES.get(src_lang, 'Chinese')
    openai_dest = OPENAI_LANG_NAMES.get(dest_lang, 'Russian')
    
    try:
        if translation_method == 'openai' and not openai_api_key:
            raise ValueError("API ключ OpenAI не указан для перевода через gpt-4o-mini")
        
        if translation_method == 'openai':
            non_empty_blocks = [b for b in text_blocks if b['text'].strip()]
            print(f"Отправка {len(non_empty_blocks)} непустых блоков на перевод...")
            translated_texts = batch_translate_with_openai(
                text_blocks, openai_api_key, src_lang=openai_src, dest_lang=openai_dest
            )
            for i, block in enumerate(text_blocks):
                if i < len(translated_texts):
                    block['translated_text'] = translated_texts[i]
                else:
                    block['translated_text'] = ""
        else:
            for i, block in enumerate(text_blocks):
                if block['text'].strip():
                    translation = translate_with_google(block['text'], src_lang=google_src, dest_lang=google_dest)
                    block['translated_text'] = translation if translation else "[Ошибка перевода]"
                    import time
                    time.sleep(0.5)
                else:
                    block['translated_text'] = ""
        return text_blocks, None
    except Exception as e:
        error_message = f"Ошибка перевода: {str(e)}"
        print(error_message)
        return text_blocks, error_message