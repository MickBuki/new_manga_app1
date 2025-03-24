"""
Модуль для перевода с помощью Google Translate
"""
from deep_translator import GoogleTranslator

def translate_with_google(text, src_lang='zh-CN', dest_lang='ru'):
    """
    Переводит текст с использованием Google Translate
    
    Args:
        text: Текст для перевода
        src_lang: Язык оригинала в формате Google Translate
        dest_lang: Язык перевода в формате Google Translate
        
    Returns:
        str: Переведенный текст или None в случае ошибки
    """
    try:
        if not text.strip():
            return ""
            
        translator = GoogleTranslator(source=src_lang, target=dest_lang)
        translation = translator.translate(text)
        return translation
    except Exception as e:
        print(f"Ошибка перевода через Google Translate: {e}")
        return None