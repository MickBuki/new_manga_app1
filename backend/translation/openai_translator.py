"""
Модуль для перевода с помощью OpenAI API
"""
from openai import OpenAI

def translate_with_openai(text, api_key, src_lang='Chinese', dest_lang='Russian', model="gpt-4o-mini"):
    """
    Переводит текст с использованием OpenAI API
    
    Args:
        text: Текст для перевода
        api_key: API ключ OpenAI
        src_lang: Язык оригинала (человекочитаемое название)
        dest_lang: Язык перевода (человекочитаемое название)
        model: Модель OpenAI для перевода
        
    Returns:
        str: Переведенный текст
        
    Raises:
        Exception: В случае ошибки перевода
    """
    if not text.strip():
        return ""
        
    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"Please translate the text from manga from {src_lang} to {dest_lang}. Make the translation sound as natural as possible, even if it is just one character."},
                {"role": "user", "content": text}
            ],
            temperature=0.2
        )
        translated_text = completion.choices[0].message.content.strip()
        return translated_text
    except Exception as e:
        error_message = f"Ошибка перевода через OpenAI: {str(e)}"
        print(error_message)
        raise Exception(error_message)