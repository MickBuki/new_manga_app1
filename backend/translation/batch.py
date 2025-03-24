"""
Модуль для пакетного перевода текстовых блоков
"""
import re
import time
from openai import OpenAI
from .openai_translator import translate_with_openai

def batch_translate_with_openai(text_blocks, api_key, src_lang='Simplified Chinese, 简体中文', dest_lang='Russian', model="gpt-4o-mini"):
    """
    Выполняет пакетный перевод нескольких текстовых блоков через OpenAI
    
    Args:
        text_blocks: Список блоков текста с ключами 'id', 'box', 'text'
        api_key: API ключ OpenAI
        src_lang: Язык оригинала (человекочитаемое название)
        dest_lang: Язык перевода (человекочитаемое название)
        model: Модель OpenAI для перевода
        
    Returns:
        list: Список переведенных текстов
    """
    # Фильтруем непустые блоки и блоки, содержащие более одного символа пунктуации
    valid_blocks = []
    original_indices = []
    for i, block in enumerate(text_blocks):
        text = block['text'].strip()
        if text and not (len(text) == 1 and text in ".,!?;:、。！？；："):
            valid_blocks.append(text)
            original_indices.append(i)
    
    if not valid_blocks:
        return []
    
    # Формируем запрос для пакетного перевода
    prompt = ""
    for i, text in enumerate(valid_blocks):
        prompt += f"[Block {i+1}]: {text}\n\n"
    
    try:
        # Выполняем пакетный перевод через OpenAI
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are a translator of {src_lang} manga into {dest_lang}. Translate the following text fragments accurately and naturally, preserving the conversational tone, humor, and cultural context of manga. Make the translation sound casual and engaging, as if it's spoken by characters in a manga. Only return the translation in the same format '[Block X]: translation'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        translated_text = completion.choices[0].message.content.strip()
        
        # Парсим результаты
        translations = {}
        pattern = re.compile(r'\[Block\s*(\d+)\]\s*:\s*(.*?)(?=\[Block\s*\d+\]|$)', re.DOTALL)
        matches = pattern.findall(translated_text)
        
        for match in matches:
            try:
                block_num = int(match[0]) - 1
                translation = match[1].strip()
                if 0 <= block_num < len(valid_blocks):
                    translations[block_num] = translation
            except (ValueError, IndexError):
                continue
        
        # Формируем результат, сохраняя порядок блоков
        result = []
        for i, block in enumerate(text_blocks):
            text = block['text'].strip()
            if not text or (len(text) == 1 and text in ".,!?;:、。！？；："):
                result.append(text)
                continue
            try:
                idx = original_indices.index(i)
                if idx in translations:
                    result.append(translations[idx])
                else:
                    print(f"Индивидуальный перевод для блока {i}: {text}")
                    result.append(translate_with_openai(text, api_key, src_lang, dest_lang))
            except ValueError:
                result.append("[Ошибка перевода]")
        return result
    except Exception as e:
        print(f"Ошибка пакетного перевода: {str(e)}")
        
        # В случае ошибки пакетного перевода, пытаемся перевести каждый блок отдельно
        result = []
        for i, block in enumerate(text_blocks):
            text = block['text'].strip()
            if not text or (len(text) == 1 and text in ".,!?;:、。！？；："):
                result.append(text)
                continue
            try:
                if i in original_indices:
                    print(f"Индивидуальный перевод блока {i}: {text}")
                    result.append(translate_with_openai(text, api_key, src_lang, dest_lang))
                    time.sleep(0.2)
                else:
                    result.append("")
            except Exception as e:
                print(f"Ошибка индивидуального перевода: {str(e)}")
                result.append("[Ошибка перевода]")
        return result